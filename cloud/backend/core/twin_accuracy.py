"""
Twin Accuracy Monitor — DT Brain

Tracks prediction accuracy of the digital twin physics engine by comparing
predicted sensor values against real sensor readings.

Physics models tracked:
  1. Soil Moisture Balance:  M_{t+1} = M_t + I - E - U
  2. Evaporation:            E ∝ T × (1 - H)
  3. Plant Water Uptake:     U = k × Light_intensity
  4. Light Influence:        growth_rate = a × light_level
  5. Temperature Effect:     evaporation_rate = base × temp_factor
  6. Time Evolution:         recurring step predictions
"""

import sqlite3
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
DB_PATH = os.path.join(DB_DIR, "sensor_history.db")


def _conn():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_twin_accuracy_db():
    """Create twin_accuracy table for storing prediction errors."""
    conn = _conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS twin_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                predicted_soil_moisture REAL,
                actual_soil_moisture REAL,
                predicted_temperature REAL,
                actual_temperature REAL,
                predicted_humidity REAL,
                actual_humidity REAL,
                soil_moisture_error REAL,
                temperature_error REAL,
                humidity_error REAL,
                evapotranspiration REAL,
                water_deficit REAL,
                growth_stage TEXT,
                calibration_triggered INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_twin_accuracy_farm_ts
                ON twin_accuracy(farm_id, timestamp DESC);
        """)
        conn.commit()
        logger.info("✓ Twin accuracy table initialized")
    finally:
        conn.close()


def store_prediction(farm_id: str, prediction: Dict, actual: Dict):
    """
    Store a twin prediction vs actual sensor comparison.

    prediction keys: soil_moisture, temperature, humidity, evapotranspiration,
                     water_deficit, growth_stage
    actual keys:     soil_moisture, temperature, humidity
    """
    pred_soil = prediction.get("soil_moisture")
    act_soil = actual.get("soil_moisture") or actual.get("soil")
    pred_temp = prediction.get("temperature")
    act_temp = actual.get("temperature") or actual.get("temp")
    pred_hum = prediction.get("humidity")
    act_hum = actual.get("humidity")

    soil_err = abs(pred_soil - act_soil) if pred_soil is not None and act_soil is not None else None
    temp_err = abs(pred_temp - act_temp) if pred_temp is not None and act_temp is not None else None
    hum_err = abs(pred_hum - act_hum) if pred_hum is not None and act_hum is not None else None
    calibrated = 1 if (soil_err and soil_err > 10) else 0

    conn = _conn()
    try:
        conn.execute("""
            INSERT INTO twin_accuracy
                (farm_id, predicted_soil_moisture, actual_soil_moisture,
                 predicted_temperature, actual_temperature,
                 predicted_humidity, actual_humidity,
                 soil_moisture_error, temperature_error, humidity_error,
                 evapotranspiration, water_deficit, growth_stage,
                 calibration_triggered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            farm_id,
            pred_soil, act_soil,
            pred_temp, act_temp,
            pred_hum, act_hum,
            soil_err, temp_err, hum_err,
            prediction.get("evapotranspiration"),
            prediction.get("water_deficit"),
            prediction.get("growth_stage"),
            calibrated,
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to store twin prediction: {e}")
    finally:
        conn.close()


def get_accuracy_stats(farm_id: str = "farm_001", hours: int = 24) -> Dict:
    """
    Compute twin accuracy statistics over a time window.

    Returns overall accuracy %, MAE, RMSE, max error, sample count,
    and per-model breakdowns.
    """
    conn = _conn()
    try:
        since = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute("""
            SELECT
                COUNT(*) as sample_count,
                ROUND(AVG(soil_moisture_error), 2) as avg_soil_err,
                ROUND(MAX(soil_moisture_error), 2) as max_soil_err,
                ROUND(AVG(temperature_error), 2) as avg_temp_err,
                ROUND(MAX(temperature_error), 2) as max_temp_err,
                ROUND(AVG(humidity_error), 2) as avg_hum_err,
                ROUND(MAX(humidity_error), 2) as max_hum_err,
                ROUND(AVG(evapotranspiration), 3) as avg_et,
                ROUND(AVG(water_deficit), 2) as avg_water_deficit,
                SUM(calibration_triggered) as calibration_count
            FROM twin_accuracy
            WHERE farm_id = ? AND timestamp >= ?
        """, (farm_id, since)).fetchone()

        if not row or row["sample_count"] == 0:
            return {"sample_count": 0, "twin_accuracy_pct": None}

        d = dict(row)
        # Overall accuracy: 100 - average absolute soil moisture error
        avg_soil = d["avg_soil_err"] or 0
        d["twin_accuracy_pct"] = round(max(0, 100 - avg_soil), 1)
        d["model_reliability_pct"] = round(max(0, 100 - avg_soil), 1)

        # RMSE for soil moisture
        rows = conn.execute("""
            SELECT soil_moisture_error FROM twin_accuracy
            WHERE farm_id = ? AND timestamp >= ? AND soil_moisture_error IS NOT NULL
        """, (farm_id, since)).fetchall()
        if rows:
            mse = sum(r["soil_moisture_error"] ** 2 for r in rows) / len(rows)
            d["soil_rmse"] = round(math.sqrt(mse), 2)
        else:
            d["soil_rmse"] = 0

        return d
    finally:
        conn.close()


def get_accuracy_history(farm_id: str = "farm_001", hours: int = 24, limit: int = 500) -> List[Dict]:
    """Return time-series of twin accuracy records for charting."""
    conn = _conn()
    try:
        since = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute("""
            SELECT * FROM twin_accuracy
            WHERE farm_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (farm_id, since, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_physics_model_summary(farm_id: str = "farm_001", hours: int = 24) -> Dict:
    """
    Build a human-readable summary of all 6 physics model states
    for the AI assistant and dashboard DT Brain view.
    """
    stats = get_accuracy_stats(farm_id, hours)
    conn = _conn()
    try:
        # Get the latest prediction record
        latest = conn.execute("""
            SELECT * FROM twin_accuracy
            WHERE farm_id = ? ORDER BY timestamp DESC LIMIT 1
        """, (farm_id,)).fetchone()
        latest = dict(latest) if latest else {}
    finally:
        conn.close()

    pred_soil = latest.get("predicted_soil_moisture", 0) or 0
    act_soil = latest.get("actual_soil_moisture", 0) or 0
    et_per_step = latest.get("evapotranspiration", 0) or 0  # mm per 0.17hr step
    # Convert per-step ET to daily rate: et_per_step * 24 / 0.17
    et_mmday = round(et_per_step * 24 / 0.17, 2) if et_per_step else 0
    deficit = latest.get("water_deficit", 0) or 0
    stage = latest.get("growth_stage", "unknown")
    act_temp = latest.get("actual_temperature", 25) or 25
    act_hum = latest.get("actual_humidity", 60) or 60
    light_estimate = max(0, 100 - (act_hum * 0.3))  # rough proxy

    # Compute accumulated GDD from temperature history (base temp = 10°C)
    # GDD per step = max(0, T - 10) * (0.17/24)
    conn2 = _conn()
    try:
        since_gdd = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        gdd_rows = conn2.execute("""
            SELECT actual_temperature FROM twin_accuracy
            WHERE farm_id = ? AND timestamp >= ? AND actual_temperature IS NOT NULL
        """, (farm_id, since_gdd)).fetchall()
        gdd_accumulated = sum(max(0, r["actual_temperature"] - 10) * (0.17 / 24) for r in gdd_rows)
        gdd_accumulated = round(gdd_accumulated, 1)
    finally:
        conn2.close()

    # Model 2: Evaporation — E ∝ T × (1 − H)
    evap_factor = round((act_temp / 40) * (1 - act_hum / 100), 3)
    if evap_factor > 0.4:
        evap_label = "very fast"
    elif evap_factor > 0.2:
        evap_label = "moderate"
    else:
        evap_label = "slow"

    # Model 3: Plant water uptake — U = k × Light
    plant_k = 0.05
    uptake = round(plant_k * light_estimate, 2)

    # Model 5: Temperature effect
    if act_temp < 22:
        temp_effect = "slow drying"
    elif act_temp < 32:
        temp_effect = "moderate drying"
    else:
        temp_effect = "very fast drying"

    # Model 6: Time evolution — predict when stress occurs
    moisture_loss_per_hour = max(0.5, et_mmday / 24 * 100)  # rough %/hr
    hours_to_stress = max(0, (act_soil - 30) / moisture_loss_per_hour) if moisture_loss_per_hour > 0 else 999

    return {
        "twin_accuracy_pct": stats.get("twin_accuracy_pct"),
        "model_reliability_pct": stats.get("model_reliability_pct"),
        "avg_prediction_error": stats.get("avg_soil_err", 0),
        "sample_count": stats.get("sample_count", 0),
        "gdd_accumulated_Cd": gdd_accumulated,
        "latest_prediction": {
            "predicted_soil_moisture": pred_soil,
            "actual_soil_moisture": act_soil,
            "error": round(abs(pred_soil - act_soil), 2),
        },
        "physics_models": {
            "1_soil_moisture_balance": {
                "equation": "M_{t+1} = M_t + I - E - U",
                "current_moisture_pct": act_soil,
                "predicted_moisture_pct": pred_soil,
                "evapotranspiration_mmday": et_mmday,
                "water_deficit_mm": deficit,
                "status": "needs irrigation" if deficit > 10 else "adequate",
            },
            "2_evaporation_model": {
                "equation": "E ∝ T × (1 − H)",
                "temperature_c": act_temp,
                "humidity_pct": act_hum,
                "evaporation_factor": evap_factor,
                "rate_label": evap_label,
            },
            "3_plant_water_uptake": {
                "equation": "U = k × Light_intensity",
                "plant_constant_k": plant_k,
                "light_estimate_pct": round(light_estimate, 1),
                "uptake_rate": uptake,
            },
            "4_light_influence": {
                "equation": "growth_rate = a × light_level",
                "light_level_pct": round(light_estimate, 1),
                "growth_stage": stage,
                "prediction": "growth ↑, water use ↑" if light_estimate > 50 else "growth ↓, water use ↓",
            },
            "5_temperature_effect": {
                "equation": "evaporation_rate = base_rate × temp_factor",
                "temperature_c": act_temp,
                "effect_label": temp_effect,
            },
            "6_time_evolution": {
                "current_moisture_pct": act_soil,
                "moisture_loss_per_hour_pct": round(moisture_loss_per_hour, 2),
                "hours_until_stress": round(hours_to_stress, 1),
                "prediction": f"moisture will reach 30% in ~{hours_to_stress:.0f} hours" if hours_to_stress < 999 else "stable",
            },
        },
    }

