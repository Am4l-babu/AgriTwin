"""
Prometheus Metrics Endpoint

Exposes /metrics in Prometheus text exposition format for monitoring:
  - sensor ingestion rate
  - MQTT message counts
  - API request counts
  - twin accuracy gauge
  - system health
"""

import time
from fastapi import APIRouter, Response
from loguru import logger

router = APIRouter(tags=["Monitoring"])

# Simple in-memory counters (reset on restart)
_counters = {
    "sensor_readings_total": 0,
    "mqtt_messages_received": 0,
    "mqtt_reconnects": 0,
    "api_requests_total": 0,
    "twin_predictions_total": 0,
    "twin_calibrations_total": 0,
    "websocket_connections_total": 0,
    "ingest_batch_total": 0,
}

_gauges = {
    "twin_accuracy_pct": 0.0,
    "twin_avg_error": 0.0,
    "sensor_last_reading_age_seconds": 0.0,
    "active_websocket_connections": 0,
    "db_readings_count": 0,
    "db_size_mb": 0.0,
}

_start_time = time.time()


def inc(counter: str, amount: int = 1):
    """Increment a counter."""
    if counter in _counters:
        _counters[counter] += amount


def gauge(name: str, value: float):
    """Set a gauge value."""
    _gauges[name] = value


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint."""
    lines = []

    # Counters
    for name, val in _counters.items():
        lines.append(f"# TYPE agritwin_{name} counter")
        lines.append(f"agritwin_{name} {val}")

    # Gauges
    for name, val in _gauges.items():
        lines.append(f"# TYPE agritwin_{name} gauge")
        lines.append(f"agritwin_{name} {val}")

    # Uptime
    uptime = time.time() - _start_time
    lines.append("# TYPE agritwin_uptime_seconds gauge")
    lines.append(f"agritwin_uptime_seconds {uptime:.0f}")

    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
