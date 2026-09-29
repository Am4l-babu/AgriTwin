"""
fog_test_helpers.py
-------------------
Shared utilities, constants, and helper classes used by both
conftest.py (fixtures) and test_fog_integration.py (assertions).
"""

import json
import sqlite3
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import List

import paho.mqtt.client as mqtt
import requests

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
FOG_DIR = ROOT / "fog"

# ─── Constants ────────────────────────────────────────────────────────────────
MQTT_HOST = "localhost"
MQTT_PORT = 1883
FOG_API_HOST = "localhost"
FOG_API_PORT = 8001
CLOUD_HOST = "localhost"
CLOUD_PORT = 8000
TEST_FARM_ID = "farm_001"
TEST_DB_PATH = str(FOG_DIR / "data" / "fog_buffer.db")


# ──────────────────────────────────────────────────────────────────────────────
# Mock Cloud Backend
# ──────────────────────────────────────────────────────────────────────────────

class MockCloudHandler(BaseHTTPRequestHandler):
    """
    HTTP handler for the mock cloud backend.
    Class-level state is shared across all instances of a single server.
    Use MockCloudServer to manage a handler instance.
    """
    received_bulk: List[dict] = []
    online: bool = True
    force_error: bool = False

    def log_message(self, *args):
        pass

    def _send(self, code: int, body: dict):
        encoded = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        cls = type(self)
        if not cls.online:
            self.send_error(503, "Service Unavailable")
            return
        if self.path == "/health":
            self._send(200, {"status": "healthy", "service": "mock-cloud"})
        else:
            self._send(404, {"detail": "not found"})

    def do_POST(self):
        cls = type(self)
        if not cls.online:
            self.send_error(503, "Service Unavailable")
            return
        if cls.force_error:
            self._send(500, {"detail": "internal server error"})
            return
        if self.path == "/api/v1/data/bulk_upload":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            cls.received_bulk.extend(body.get("data", []))
            self._send(200, {"status": "ok", "count": len(body.get("data", []))})
        else:
            self._send(404, {"detail": "not found"})


class MockCloudServer:
    """Thread-based mock cloud backend that can be toggled on/off."""

    def __init__(self, port: int = CLOUD_PORT):
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        # Each instance uses its own subclass so class-level state is isolated
        self._handler_cls = type(
            f"Handler_{port}",
            (MockCloudHandler,),
            {"received_bulk": [], "online": True, "force_error": False},
        )

    def start(self):
        self._handler_cls.received_bulk = []
        self._handler_cls.online = True
        self._handler_cls.force_error = False
        self._server = HTTPServer(("localhost", self.port), self._handler_cls)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        for _ in range(20):
            try:
                requests.get(f"http://localhost:{self.port}/health", timeout=1)
                return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError(f"Mock cloud server on port {self.port} failed to start")

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None

    def go_offline(self):
        self._handler_cls.online = False

    def go_online(self):
        self._handler_cls.online = True

    def force_server_error(self):
        self._handler_cls.force_error = True

    def clear_error(self):
        self._handler_cls.force_error = False

    @property
    def received(self) -> List[dict]:
        return self._handler_cls.received_bulk

    def clear_received(self):
        self._handler_cls.received_bulk = []


# ──────────────────────────────────────────────────────────────────────────────
# MQTT Publisher
# ──────────────────────────────────────────────────────────────────────────────

class ESP32Publisher:
    """Simulates an ESP32 device publishing sensor data over MQTT."""

    def __init__(self, host: str = MQTT_HOST, port: int = MQTT_PORT):
        self.host = host
        self.port = port
        self._client = mqtt.Client(
            client_id=f"test_esp32_{uuid.uuid4().hex[:6]}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        )
        self._connected = False

    def connect(self):
        def on_connect(client, userdata, flags, rc):
            self._connected = rc == 0

        self._client.on_connect = on_connect
        self._client.connect(self.host, self.port, keepalive=60)
        self._client.loop_start()
        for _ in range(20):
            if self._connected:
                return
            time.sleep(0.2)
        raise RuntimeError("ESP32Publisher could not connect to MQTT broker")

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def publish_sensor(
        self,
        sensor_type: str,
        value: float,
        farm_id: str = TEST_FARM_ID,
        extra: dict | None = None,
        qos: int = 1,
    ) -> bool:
        topic = f"farms/{farm_id}/sensors/{sensor_type}/data"
        payload = {
            "sensor_type": sensor_type,
            "value": value,
            "timestamp": int(time.time()),
            "device_id": "esp32_edge_001",
            "farm_id": farm_id,
        }
        if extra:
            payload.update(extra)
        result = self._client.publish(topic, json.dumps(payload), qos=qos)
        return result.rc == 0

    def publish_raw(self, topic: str, payload: dict, qos: int = 1):
        self._client.publish(topic, json.dumps(payload), qos=qos)

    def burst(self, sensor_type: str, values: List[float], delay: float = 0.0):
        for v in values:
            self.publish_sensor(sensor_type, v)
            if delay:
                time.sleep(delay)


# ──────────────────────────────────────────────────────────────────────────────
# Buffer Inspector
# ──────────────────────────────────────────────────────────────────────────────

class BufferInspector:
    """Direct read-only access to the fog's SQLite buffer for test assertions."""

    def __init__(self, db_path: str = TEST_DB_PATH):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def count_all(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM sensor_data").fetchone()[0]

    def count_unsynced(self) -> int:
        with self._conn() as c:
            return c.execute(
                "SELECT COUNT(*) FROM sensor_data WHERE synced=0"
            ).fetchone()[0]

    def count_synced(self) -> int:
        with self._conn() as c:
            return c.execute(
                "SELECT COUNT(*) FROM sensor_data WHERE synced=1"
            ).fetchone()[0]

    def all_records(self) -> List[dict]:
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(
                "SELECT * FROM sensor_data ORDER BY timestamp ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def alerts(self) -> List[dict]:
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(
                "SELECT * FROM alerts ORDER BY timestamp ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def last_record(self) -> dict | None:
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            row = c.execute(
                "SELECT * FROM sensor_data ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def reset(self):
        with self._conn() as c:
            c.execute("DELETE FROM sensor_data")
            c.execute("DELETE FROM alerts")
            c.execute("DELETE FROM device_status")


# ──────────────────────────────────────────────────────────────────────────────
# Polling Helper
# ──────────────────────────────────────────────────────────────────────────────

def wait_for_condition(fn, timeout: float = 5.0, interval: float = 0.2) -> bool:
    """Poll fn() until it returns True or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if fn():
            return True
        time.sleep(interval)
    return False
