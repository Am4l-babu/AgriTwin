"""
Mock Sensor Payloads

Realistic ESP32 sensor payloads used across all integration tests.
Matches the format validated by fog/src/preprocessing/validator.py:
  Required fields: sensor_type, value, timestamp
  sensor_type must be one of: soil_moisture, temperature, humidity, ph, light, ec
"""

import time


def _ts() -> int:
    """Current UTC unix timestamp as int."""
    return int(time.time())


# ─── Normal / Healthy Readings ────────────────────────────────────────────────

NORMAL_SOIL_MOISTURE = {
    "sensor_type": "soil_moisture",
    "value": 55.0,          # healthy – well above 30% irrigation threshold
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

NORMAL_TEMPERATURE = {
    "sensor_type": "temperature",
    "value": 24.5,          # comfortable temperature, below 35°C alert threshold
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

NORMAL_HUMIDITY = {
    "sensor_type": "humidity",
    "value": 62.0,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

NORMAL_LIGHT = {
    "sensor_type": "light",
    "value": 12500.0,       # lux – bright indirect sunlight
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

NORMAL_PH = {
    "sensor_type": "ph",
    "value": 6.5,           # ideal: 6.0–7.0
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

NORMAL_EC = {
    "sensor_type": "ec",
    "value": 1.8,           # mS/cm – healthy range
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}


# ─── Emergency / Alert Payloads ───────────────────────────────────────────────

# Triggers 'auto_irrigation_low' rule  (soil_moisture < 30)
EMERGENCY_LOW_SOIL = {
    "sensor_type": "soil_moisture",
    "value": 18.0,          # critically low – triggers auto-irrigation
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

# Exactly at threshold boundary, should NOT trigger (< 30, value == 30 is NOT < 30)
BOUNDARY_SOIL_EXACT = {
    "sensor_type": "soil_moisture",
    "value": 30.0,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

# Just below threshold, SHOULD trigger
BOUNDARY_SOIL_BELOW = {
    "sensor_type": "soil_moisture",
    "value": 29.9,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

# Triggers 'temperature_alert_high' rule (temperature > 35)
EMERGENCY_HIGH_TEMP = {
    "sensor_type": "temperature",
    "value": 38.5,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}

# Exactly at threshold – should NOT trigger (> 35, value == 35 is NOT > 35)
BOUNDARY_TEMP_EXACT = {
    "sensor_type": "temperature",
    "value": 35.0,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
    "farm_id": "farm_001",
}


# ─── Invalid Payloads ─────────────────────────────────────────────────────────

# Missing required field: sensor_type
INVALID_MISSING_SENSOR_TYPE = {
    "value": 55.0,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
}

# Missing required field: value
INVALID_MISSING_VALUE = {
    "sensor_type": "soil_moisture",
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
}

# Missing required field: timestamp
INVALID_MISSING_TIMESTAMP = {
    "sensor_type": "temperature",
    "value": 24.5,
    "device_id": "esp32_edge_001",
}

# Value out of valid range (soil_moisture max = 100)
INVALID_OUT_OF_RANGE_HIGH = {
    "sensor_type": "soil_moisture",
    "value": 150.0,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
}

# Value out of valid range (temperature min = -40)
INVALID_OUT_OF_RANGE_LOW = {
    "sensor_type": "temperature",
    "value": -50.0,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
}

# Unknown sensor type
INVALID_UNKNOWN_SENSOR_TYPE = {
    "sensor_type": "wind_speed",
    "value": 12.5,
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
}

# Non-numeric value
INVALID_STRING_VALUE = {
    "sensor_type": "humidity",
    "value": "very humid",
    "timestamp": _ts(),
    "device_id": "esp32_edge_001",
}

# Completely malformed (not valid JSON structure)
INVALID_EMPTY = {}


# ─── Burst/Stress Sequences ───────────────────────────────────────────────────

def make_soil_sequence(count: int, base_value: float = 55.0) -> list:
    """Generate a sequence of soil_moisture readings."""
    import random
    return [
        {
            "sensor_type": "soil_moisture",
            "value": round(base_value + random.uniform(-5, 5), 1),
            "timestamp": _ts() + i,
            "device_id": "esp32_edge_001",
            "farm_id": "farm_001",
        }
        for i in range(count)
    ]


def make_multi_sensor_batch(count_each: int = 10) -> list:
    """Generate readings for all sensor types."""
    import random
    payloads = []
    specs = [
        ("soil_moisture", 40.0, 80.0),
        ("temperature", 18.0, 30.0),
        ("humidity", 45.0, 80.0),
        ("light", 5000.0, 20000.0),
    ]
    for sensor, lo, hi in specs:
        for i in range(count_each):
            payloads.append({
                "sensor_type": sensor,
                "value": round(random.uniform(lo, hi), 2),
                "timestamp": _ts() + i,
                "device_id": "esp32_edge_001",
                "farm_id": "farm_001",
            })
    return payloads


# ─── Device Status Payload ────────────────────────────────────────────────────

STATUS_ONLINE = {
    "device_id": "esp32_edge_001",
    "status": "online",
    "rssi": -62,
    "free_heap": 245000,
    "uptime": 3600,
    "timestamp": _ts(),
}
