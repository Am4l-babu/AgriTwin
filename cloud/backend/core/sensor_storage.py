"""
SQLite Sensor Data Storage

Lightweight storage for historical sensor readings.
Uses plain sqlite3 (no ORM) for simplicity and zero dependencies.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger

# Database path - store in project data/ directory
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
DB_PATH = os.path.join(DB_DIR, "sensor_history.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema"""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                device_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                temperature REAL,
                humidity REAL,
                light_level REAL,
                soil_moisture REAL,
                raw_ldr INTEGER,
                raw_soil INTEGER,
                rssi INTEGER,
                free_heap INTEGER,
                uptime INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_farm_timestamp 
                ON sensor_readings(farm_id, timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON sensor_readings(timestamp DESC);
        """)
        conn.commit()
        # Migration: add raw_ldr and raw_soil columns if they don't exist yet (for existing databases)
        for col, coltype in [("raw_ldr", "INTEGER"), ("raw_soil", "INTEGER")]:
            try:
                conn.execute(f"ALTER TABLE sensor_readings ADD COLUMN {col} {coltype}")
                conn.commit()
                logger.info(f"Migration: added column {col}")
            except Exception:
                pass  # Column already exists
        logger.info(f"✓ Database initialized at {DB_PATH}")
    finally:
        conn.close()


# Sensor validation bounds — reject clearly impossible readings
_SENSOR_BOUNDS = {
    "temperature": (-40.0, 80.0),
    "humidity": (0.0, 100.0),
    "light_level": (0.0, 100000.0),
    "soil_moisture": (0.0, 100.0),
}


def _validate_reading(key: str, value) -> Optional[float]:
    """Return sanitised float or None if out of bounds / not a number."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    import math
    if math.isnan(v) or math.isinf(v):
        return None
    lo, hi = _SENSOR_BOUNDS.get(key, (None, None))
    if lo is not None and not (lo <= v <= hi):
        logger.warning(f"Sensor {key}={v} out of bounds [{lo}, {hi}] — skipped")
        return None
    return round(v, 2)


def store_reading(farm_id: str, data: dict):
    """Store a sensor reading in the database.
    Accepts both nested {sensors:{...}, system:{...}} and flat {temperature, humidity, ...} formats.
    Values are validated against physical bounds before storage.
    """
    conn = get_connection()
    try:
        # Support both nested and flat payload formats
        sensors = data.get("sensors") or data
        system = data.get("system") or data

        temp = _validate_reading("temperature", sensors.get("temperature"))
        hum = _validate_reading("humidity", sensors.get("humidity"))
        light = _validate_reading("light_level", sensors.get("light_level"))
        soil = _validate_reading("soil_moisture", sensors.get("soil_moisture"))

        # Skip entirely empty readings (no valid sensor data)
        if all(v is None for v in (temp, hum, light, soil)):
            logger.debug("All sensor values invalid — skipping store")
            return

        # Raw ADC values for calibration wizards (optional, may not be present in all payloads)
        raw_ldr_val = data.get("raw_ldr")
        raw_soil_val = data.get("raw_soil")
        if raw_ldr_val is not None:
            try:
                raw_ldr_val = int(raw_ldr_val)
                if not (0 <= raw_ldr_val <= 4095):
                    raw_ldr_val = None
            except (TypeError, ValueError):
                raw_ldr_val = None
        if raw_soil_val is not None:
            try:
                raw_soil_val = int(raw_soil_val)
                if not (0 <= raw_soil_val <= 4095):
                    raw_soil_val = None
            except (TypeError, ValueError):
                raw_soil_val = None

        conn.execute("""
            INSERT INTO sensor_readings 
                (farm_id, device_id, temperature, humidity, light_level, soil_moisture, raw_ldr, raw_soil, rssi, free_heap, uptime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            farm_id,
            data.get("device_id", "unknown"),
            temp,
            hum,
            light,
            soil,
            raw_ldr_val,
            raw_soil_val,
            system.get("rssi"),
            system.get("free_heap"),
            system.get("uptime"),
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to store reading: {e}")
    finally:
        conn.close()


def get_history(
    farm_id: str = "farm_001",
    hours: int = 24,
    limit: int = 1000
) -> List[Dict]:
    """Get historical sensor readings"""
    conn = get_connection()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")
        rows = conn.execute("""
            SELECT id, farm_id, device_id, timestamp,
                   temperature, humidity, light_level, soil_moisture,
                   rssi, free_heap, uptime
            FROM sensor_readings
            WHERE farm_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (farm_id, since_str, limit)).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_latest(farm_id: str = "farm_001") -> Optional[Dict]:
    """Get the most recent sensor reading"""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT * FROM sensor_readings
            WHERE farm_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (farm_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_stats(farm_id: str = "farm_001", hours: int = 24) -> Dict:
    """Get min/max/avg stats for a time period"""
    conn = get_connection()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute("""
            SELECT 
                COUNT(*) as count,
                ROUND(AVG(temperature), 1) as avg_temp,
                ROUND(MIN(temperature), 1) as min_temp,
                ROUND(MAX(temperature), 1) as max_temp,
                ROUND(AVG(humidity), 1) as avg_humidity,
                ROUND(MIN(humidity), 1) as min_humidity,
                ROUND(MAX(humidity), 1) as max_humidity,
                ROUND(AVG(light_level), 0) as avg_light,
                ROUND(MIN(light_level), 0) as min_light,
                ROUND(MAX(light_level), 0) as max_light,
                ROUND(AVG(soil_moisture), 1) as avg_soil,
                ROUND(MIN(soil_moisture), 1) as min_soil,
                ROUND(MAX(soil_moisture), 1) as max_soil
            FROM sensor_readings
            WHERE farm_id = ? AND timestamp >= ?
        """, (farm_id, since_str)).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_reading_count(farm_id: str = "farm_001") -> int:
    """Get total number of readings stored"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM sensor_readings WHERE farm_id = ?",
            (farm_id,)
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def cleanup_old_readings(retention_days: int = 30) -> int:
    """Delete readings older than retention_days. Returns deleted count."""
    conn = get_connection()
    try:
        cutoff = (datetime.utcnow() - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            "DELETE FROM sensor_readings WHERE timestamp < ?", (cutoff,)
        )
        conn.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info(f"🗑 Cleaned up {deleted} readings older than {retention_days} days")
        return deleted
    finally:
        conn.close()


def get_db_size_mb() -> float:
    """Return the database file size in MB."""
    try:
        return round(os.path.getsize(DB_PATH) / (1024 * 1024), 2)
    except OSError:
        return 0.0
