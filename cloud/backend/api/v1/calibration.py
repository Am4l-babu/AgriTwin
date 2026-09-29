"""
Sensor Calibration API

Manages calibration profiles for edge sensors:
- CRUD operations for calibration profiles (stored as JSON files)
- Calibration wizard: compute offset/multiplier from reference points
- Live calibration status overview
"""

import json
import os
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# Path to calibration profiles (edge layer)
# Use environment variable if available, otherwise try relative paths
_env_cal = os.environ.get("CALIBRATION_DIR")
if _env_cal:
    CALIBRATION_DIR = Path(_env_cal)
else:
    # Try project root first, then fallback for Docker
    _root = Path(__file__).resolve()
    for i in range(len(_root.parents)):
        candidate = _root.parents[i] / "edge" / "calibration_profiles"
        if candidate.exists():
            CALIBRATION_DIR = candidate
            break
    else:
        CALIBRATION_DIR = Path("/app/calibration_profiles")


# ── Pydantic Models ──────────────────────────────────────────────────────────

class ReferencePoint(BaseModel):
    raw: float = Field(..., description="Raw ADC reading from sensor")
    actual: float = Field(..., description="Known reference value")
    condition: str = Field("", description="Description of test condition")


class CalibrationWizardRequest(BaseModel):
    sensor_type: str
    method: str = Field(..., description="offset_correction | two_point_linear | three_point_polynomial")
    points: list[ReferencePoint] = Field(..., min_length=1, max_length=3)
    notes: str = ""


class ProfileUpdate(BaseModel):
    """Partial update to a calibration profile"""
    offset: Optional[float] = None
    multiplier: Optional[float] = None
    dry_value: Optional[int] = None
    wet_value: Optional[int] = None
    point1: Optional[dict] = None
    point2: Optional[dict] = None
    point3: Optional[dict] = None
    notes: Optional[str] = None
    interpretation: Optional[dict] = None


# ── Helper ────────────────────────────────────────────────────────────────────

SENSOR_FILE_MAP = {
    "temperature": "temperature_calibration.json",
    "humidity": "humidity_calibration.json",
    "light": "light_calibration.json",
    "soil_moisture": "soil_calibration.json",
    "ph": "ph_calibration.json",
}


def _read_profile(sensor_type: str) -> dict:
    fname = SENSOR_FILE_MAP.get(sensor_type)
    if not fname:
        raise HTTPException(status_code=404, detail=f"Unknown sensor type: {sensor_type}")
    fpath = CALIBRATION_DIR / fname
    if not fpath.exists():
        raise HTTPException(status_code=404, detail=f"Profile not found: {fname}")
    with open(fpath, "r") as f:
        return json.load(f)


def _write_profile(sensor_type: str, data: dict):
    fname = SENSOR_FILE_MAP.get(sensor_type)
    if not fname:
        raise HTTPException(status_code=404, detail=f"Unknown sensor type: {sensor_type}")
    fpath = CALIBRATION_DIR / fname
    with open(fpath, "w") as f:
        json.dump(data, f, indent=2)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/profiles")
async def list_profiles():
    """List all calibration profiles with summary info."""
    profiles = []
    for sensor_type, fname in SENSOR_FILE_MAP.items():
        fpath = CALIBRATION_DIR / fname
        if fpath.exists():
            with open(fpath, "r") as f:
                data = json.load(f)
            profiles.append({
                "sensor_type": sensor_type,
                "method": data.get("calibration_method", "unknown"),
                "calibration_date": data.get("calibration_date", "unknown"),
                "description": data.get("description", ""),
                "notes": data.get("notes", ""),
                "has_interpretation": "interpretation" in data,
                "has_reference_points": "reference_points" in data,
            })
        else:
            profiles.append({
                "sensor_type": sensor_type,
                "method": "not_calibrated",
                "calibration_date": None,
                "description": f"{sensor_type} sensor (no profile)",
                "notes": "",
                "has_interpretation": False,
                "has_reference_points": False,
            })
    return {"profiles": profiles}


@router.get("/profiles/{sensor_type}")
async def get_profile(sensor_type: str):
    """Get full calibration profile for a sensor."""
    return _read_profile(sensor_type)


@router.put("/profiles/{sensor_type}")
async def update_profile(sensor_type: str, update: ProfileUpdate):
    """Update specific fields of a calibration profile."""
    profile = _read_profile(sensor_type)

    update_dict = update.model_dump(exclude_none=True)
    profile.update(update_dict)
    profile["calibration_date"] = str(date.today())

    _write_profile(sensor_type, profile)
    return {"status": "updated", "sensor_type": sensor_type, "profile": profile}


@router.post("/wizard")
async def calibration_wizard(req: CalibrationWizardRequest):
    """
    Calibration wizard: compute calibration parameters from reference measurements.

    Methods:
    - offset_correction (1-3 points): computes offset and multiplier via least-squares
    - two_point_linear (2 points): computes dry_value/wet_value mapping
    - three_point_polynomial (3 points): stores 3-point calibration data
    """
    points = req.points

    if req.method == "offset_correction":
        # Least-squares fit: actual = raw * multiplier + offset
        if len(points) == 1:
            multiplier = 1.0
            offset = points[0].actual - points[0].raw
        else:
            n = len(points)
            sum_raw = sum(p.raw for p in points)
            sum_actual = sum(p.actual for p in points)
            sum_raw2 = sum(p.raw ** 2 for p in points)
            sum_raw_actual = sum(p.raw * p.actual for p in points)
            denom = n * sum_raw2 - sum_raw ** 2
            if abs(denom) < 1e-10:
                multiplier = 1.0
                offset = sum_actual / n - sum_raw / n
            else:
                multiplier = (n * sum_raw_actual - sum_raw * sum_actual) / denom
                offset = (sum_actual - multiplier * sum_raw) / n

        # Load existing profile or create new
        try:
            profile = _read_profile(req.sensor_type)
        except HTTPException:
            profile = {
                "sensor_type": req.sensor_type,
                "calibration_method": "offset_correction",
            }

        profile["offset"] = round(offset, 4)
        profile["multiplier"] = round(multiplier, 4)
        profile["calibration_date"] = str(date.today())
        profile["calibration_method"] = "offset_correction"
        profile["notes"] = req.notes or profile.get("notes", "")
        profile["reference_points"] = [
            {"reference": p.actual, "measured": p.raw, "condition": p.condition}
            for p in points
        ]

        _write_profile(req.sensor_type, profile)
        return {
            "status": "calibrated",
            "method": "offset_correction",
            "offset": profile["offset"],
            "multiplier": profile["multiplier"],
            "profile": profile,
        }

    elif req.method == "two_point_linear":
        if len(points) < 2:
            raise HTTPException(status_code=400, detail="two_point_linear requires exactly 2 points")

        dry_point = max(points[:2], key=lambda p: p.raw)
        wet_point = min(points[:2], key=lambda p: p.raw)

        try:
            profile = _read_profile(req.sensor_type)
        except HTTPException:
            profile = {
                "sensor_type": req.sensor_type,
                "calibration_method": "two_point_linear",
            }

        profile["dry_value"] = int(dry_point.raw)
        profile["wet_value"] = int(wet_point.raw)
        profile["calibration_date"] = str(date.today())
        profile["calibration_method"] = "two_point_linear"
        profile["notes"] = req.notes or profile.get("notes", "")

        _write_profile(req.sensor_type, profile)
        return {
            "status": "calibrated",
            "method": "two_point_linear",
            "dry_value": profile["dry_value"],
            "wet_value": profile["wet_value"],
            "profile": profile,
        }

    elif req.method == "three_point_polynomial":
        if len(points) < 3:
            raise HTTPException(status_code=400, detail="three_point_polynomial requires exactly 3 points")

        try:
            profile = _read_profile(req.sensor_type)
        except HTTPException:
            profile = {
                "sensor_type": req.sensor_type,
                "calibration_method": "three_point_polynomial",
            }

        for i, p in enumerate(points[:3], 1):
            profile[f"point{i}"] = {
                "raw": p.raw,
                "actual": p.actual,
                "buffer": p.condition,
            }

        profile["calibration_date"] = str(date.today())
        profile["calibration_method"] = "three_point_polynomial"
        profile["notes"] = req.notes or profile.get("notes", "")

        _write_profile(req.sensor_type, profile)
        return {
            "status": "calibrated",
            "method": "three_point_polynomial",
            "profile": profile,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {req.method}")


@router.get("/status")
async def calibration_status():
    """Overview of all sensor calibration statuses."""
    statuses = []
    for sensor_type, fname in SENSOR_FILE_MAP.items():
        fpath = CALIBRATION_DIR / fname
        if fpath.exists():
            with open(fpath, "r") as f:
                data = json.load(f)
            statuses.append({
                "sensor_type": sensor_type,
                "calibrated": True,
                "method": data.get("calibration_method", "unknown"),
                "date": data.get("calibration_date", "unknown"),
                "file": fname,
            })
        else:
            statuses.append({
                "sensor_type": sensor_type,
                "calibrated": False,
                "method": None,
                "date": None,
                "file": fname,
            })
    return {"statuses": statuses}
