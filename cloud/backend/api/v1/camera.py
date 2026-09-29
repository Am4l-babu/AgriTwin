"""
Camera API — /api/v1/camera
Receives images from the Raspberry Pi fog layer, stores them on disk,
and exposes endpoints for the web dashboard and mobile app.

Endpoints
---------
POST  /api/v1/camera/upload          — Pi uploads a JPEG
GET   /api/v1/camera/latest          — latest image (returns JSON with URL)
GET   /api/v1/camera/list            — paginated image gallery
GET   /api/v1/camera/image/{filename} — serve a stored image file
POST  /api/v1/camera/capture         — trigger on-demand capture via MQTT
DELETE /api/v1/camera/image/{filename} — delete a stored image
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from loguru import logger

router = APIRouter(prefix="/api/v1/camera", tags=["Camera"])

# ── Storage dir (created next to this file's package root) ────────────────────
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent   # cloud/backend
IMAGE_DIR = _BACKEND_ROOT / "camera_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_filename(name: str) -> str:
    """Strip any path components so callers can't traverse the directory."""
    return Path(name).name


def _image_metadata(path: Path) -> dict:
    stat = path.stat()
    return {
        "filename": path.name,
        "url": f"/api/v1/camera/image/{path.name}",
        "size_bytes": stat.st_size,
        "captured_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    farm_id: str = Form(default="farm_001"),
):
    """Receive a JPEG from the Raspberry Pi camera service."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG files accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    # Timestamp-based filename to avoid collisions
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    save_name = f"{farm_id}_{ts}{ext}"
    save_path = IMAGE_DIR / save_name

    save_path.write_bytes(content)
    logger.info(f"[Camera] Saved image: {save_name} ({len(content)} bytes) from {farm_id}")

    return {"status": "ok", "filename": save_name, "url": f"/api/v1/camera/image/{save_name}"}


@router.get("/latest")
async def get_latest_image(farm_id: str = "farm_001"):
    """Return metadata for the most-recently uploaded image."""
    images = sorted(IMAGE_DIR.glob(f"{farm_id}_*.jp*"), key=lambda p: p.stat().st_mtime)
    if not images:
        raise HTTPException(status_code=404, detail="No images found")
    return _image_metadata(images[-1])


@router.get("/list")
async def list_images(
    farm_id: str = "farm_001",
    page: int = 1,
    page_size: int = 20,
):
    """Return a paginated list of captured images (newest first)."""
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")

    all_images = sorted(
        IMAGE_DIR.glob(f"{farm_id}_*.jp*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    total = len(all_images)
    start = (page - 1) * page_size
    end = start + page_size
    page_images = all_images[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "images": [_image_metadata(p) for p in page_images],
    }


@router.get("/image/{filename}")
async def serve_image(filename: str):
    """Serve a stored image file."""
    safe = _safe_filename(filename)
    path = IMAGE_DIR / safe
    if not path.exists() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/jpeg")


@router.post("/capture")
async def trigger_capture(request: Request, farm_id: str = "farm_001"):
    """Ask the Pi to take a photo now (publishes an MQTT message)."""
    try:
        mqtt_client = request.app.state.mqtt_client
        topic = f"farm/{farm_id}/camera/capture"
        payload = json.dumps({"command": "capture", "farm_id": farm_id,
                               "requested_at": datetime.utcnow().isoformat()})
        mqtt_client.publish(topic, payload)
        logger.info(f"[Camera] Capture trigger sent → {topic}")
        return {"status": "triggered", "topic": topic}
    except AttributeError:
        raise HTTPException(status_code=503, detail="MQTT client not available")
    except Exception as e:
        logger.error(f"[Camera] Trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/image/{filename}")
async def delete_image(filename: str):
    """Delete a stored image."""
    safe = _safe_filename(filename)
    path = IMAGE_DIR / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    path.unlink()
    logger.info(f"[Camera] Deleted: {safe}")
    return {"status": "deleted", "filename": safe}
