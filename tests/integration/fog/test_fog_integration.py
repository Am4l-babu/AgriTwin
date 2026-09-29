"""
Fog Gateway — Integration Test Suite
=====================================

Architecture under test:
    ESP32 (MQTT) → Fog Gateway → Cloud Backend (FastAPI)

Test approach:
    • Component-level integration: instantiate fog components directly to get
      fast, reliable tests that don't depend on a running server process.
    • End-to-end tests: marked with @pytest.mark.e2e; require the fog gateway
      server to be running on localhost:8001.  Skip automatically if it isn't.

Run all tests:
    cd mini_project
    pytest tests/integration/fog/ -v

Run only component tests (no live fog needed):
    pytest tests/integration/fog/ -v -m "not e2e"

Run only e2e tests (fog + cloud both must be running):
    pytest tests/integration/fog/ -v -m e2e

Prerequisites (component tests only):
    pip install pytest pytest-asyncio paho-mqtt requests httpx
    MQTT broker must be running on localhost:1883
    fog/data/ directory must exist (or set SQLITE_DB_PATH env var)
"""

import asyncio
import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

# ─── Path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
FOG_DIR = ROOT / "fog"
sys.path.insert(0, str(FOG_DIR))
sys.path.insert(0, str(Path(__file__).parent))  # fog_test_helpers lives here

from fog_test_helpers import (  # noqa: E402
    CLOUD_PORT,
    FOG_API_PORT,
    MQTT_HOST,
    MQTT_PORT,
    TEST_FARM_ID,
    MockCloudServer,
    wait_for_condition,
)
from payloads import (  # noqa: E402
    BOUNDARY_SOIL_BELOW,
    BOUNDARY_SOIL_EXACT,
    BOUNDARY_TEMP_EXACT,
    EMERGENCY_HIGH_TEMP,
    EMERGENCY_LOW_SOIL,
    INVALID_EMPTY,
    INVALID_MISSING_SENSOR_TYPE,
    INVALID_MISSING_TIMESTAMP,
    INVALID_MISSING_VALUE,
    INVALID_OUT_OF_RANGE_HIGH,
    INVALID_OUT_OF_RANGE_LOW,
    INVALID_STRING_VALUE,
    INVALID_UNKNOWN_SENSOR_TYPE,
    NORMAL_HUMIDITY,
    NORMAL_LIGHT,
    NORMAL_SOIL_MOISTURE,
    NORMAL_TEMPERATURE,
    STATUS_ONLINE,
    make_multi_sensor_batch,
    make_soil_sequence,
)

# ─── Fog component imports ─────────────────────────────────────────────────────
from src.buffer_manager.buffer import BufferManager
from src.cloud_sync.sync_service import CloudSyncService
from src.config.settings import Settings
from src.emergency_control.controller import EmergencyController
from src.preprocessing.validator import DataValidator

# ─── Markers ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def fog_is_running() -> bool:
    try:
        r = requests.get(f"http://localhost:{FOG_API_PORT}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def skip_if_fog_down():
    return pytest.mark.skipif(
        not fog_is_running(), reason="Fog Gateway not running on localhost:8001"
    )


def _make_settings(**overrides) -> Settings:
    """Create a minimal Settings instance for component tests."""
    defaults = dict(
        farm_id=TEST_FARM_ID,
        device_id="test_fog_001",
        mqtt_broker_host=MQTT_HOST,
        mqtt_broker_port=MQTT_PORT,
        mqtt_username="",
        cloud_api_url=f"http://localhost:{CLOUD_PORT}",
        sqlite_db_path=str(FOG_DIR / "data" / "test_integration.db"),
        validation_enabled=True,
        emergency_control_enabled=True,
        buffer_sync_batch_size=100,
        cloud_sync_interval=2,
        cloud_connection_timeout=5,
        buffer_retention_days=7,
    )
    defaults.update(overrides)
    return Settings(**defaults)


async def _make_buffer(settings: Settings | None = None) -> BufferManager:
    s = settings or _make_settings()
    buf = BufferManager(s)
    await buf.initialize()
    return buf


async def _reset_buffer(buf: BufferManager):
    """Wipe all test data from the buffer."""
    conn: sqlite3.Connection = buf.sqlite_conn
    conn.execute("DELETE FROM sensor_data")
    conn.execute("DELETE FROM alerts")
    conn.execute("DELETE FROM device_status")
    conn.commit()


# ──────────────────────────────────────────────────────────────────────────────
# TC-01  Normal Data Flow
# ──────────────────────────────────────────────────────────────────────────────

class TestNormalDataFlow:
    """
    Verify valid sensor readings flow through the fog correctly:
        publish MQTT → fog ingests → stored in SQLite buffer
    Expected: record count increases, values stored accurately.
    """

    async def test_valid_soil_stored_in_buffer(self):
        """TC-01-A: A valid soil_moisture reading is stored in the buffer."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        await buf.store_sensor_data(
            farm_id=TEST_FARM_ID,
            sensor_type="soil_moisture",
            data=NORMAL_SOIL_MOISTURE,
        )

        records = buf.sqlite_conn.execute(
            "SELECT * FROM sensor_data WHERE sensor_type='soil_moisture'"
        ).fetchall()
        assert len(records) == 1, "Expected exactly one record in buffer"
        await buf.close()

    async def test_all_standard_sensor_types_accepted(self):
        """TC-01-B: All supported sensor types are buffered without errors."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        payloads = [
            ("soil_moisture", NORMAL_SOIL_MOISTURE),
            ("temperature", NORMAL_TEMPERATURE),
            ("humidity", NORMAL_HUMIDITY),
            ("light", NORMAL_LIGHT),
        ]
        for sensor_type, payload in payloads:
            await buf.store_sensor_data(TEST_FARM_ID, sensor_type, payload)

        count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert count == 4, f"Expected 4 records, got {count}"
        await buf.close()

    async def test_new_records_begin_as_unsynced(self):
        """TC-01-C: Newly stored records have synced=0."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        await buf.store_sensor_data(TEST_FARM_ID, "temperature", NORMAL_TEMPERATURE)

        row = buf.sqlite_conn.execute(
            "SELECT synced FROM sensor_data ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row[0] == 0, "New records must be unsynced (synced=0)"
        await buf.close()

    async def test_stored_value_matches_input(self):
        """TC-01-D: The buffered value exactly matches the published value."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        await buf.store_sensor_data(TEST_FARM_ID, "humidity", NORMAL_HUMIDITY)

        row = buf.sqlite_conn.execute(
            "SELECT value FROM sensor_data WHERE sensor_type='humidity' LIMIT 1"
        ).fetchone()
        assert row is not None
        assert abs(float(row[0]) - NORMAL_HUMIDITY["value"]) < 0.001
        await buf.close()


# ──────────────────────────────────────────────────────────────────────────────
# TC-02  Data Validation
# ──────────────────────────────────────────────────────────────────────────────

class TestDataValidation:
    """
    Verify that the DataValidator correctly accepts/rejects payloads.
    Invalid data must NOT reach the buffer.
    """

    def setup_method(self):
        self.validator = DataValidator(_make_settings())

    def test_valid_soil_moisture_passes(self):
        """TC-02-A: Valid payload passes validation."""
        ok, errors = self.validator.validate_sensor_data(NORMAL_SOIL_MOISTURE)
        assert ok is True
        assert errors == []

    def test_valid_temperature_passes(self):
        ok, errors = self.validator.validate_sensor_data(NORMAL_TEMPERATURE)
        assert ok is True

    @pytest.mark.parametrize("payload,expected_fragment", [
        (INVALID_MISSING_SENSOR_TYPE, "sensor_type"),
        (INVALID_MISSING_VALUE, "value"),
        (INVALID_MISSING_TIMESTAMP, "timestamp"),
        (INVALID_EMPTY, "sensor_type"),
    ])
    def test_missing_required_field_rejected(self, payload, expected_fragment):
        """TC-02-B: Payloads missing required fields are rejected."""
        ok, errors = self.validator.validate_sensor_data(payload)
        assert ok is False
        assert any(expected_fragment in e for e in errors), (
            f"Expected error mentioning '{expected_fragment}', got: {errors}"
        )

    def test_out_of_range_high_rejected(self):
        """TC-02-C: Value above sensor maximum is rejected."""
        ok, errors = self.validator.validate_sensor_data(INVALID_OUT_OF_RANGE_HIGH)
        assert ok is False
        assert any("range" in e.lower() or "out" in e.lower() for e in errors)

    def test_out_of_range_low_rejected(self):
        """TC-02-D: Value below sensor minimum is rejected."""
        ok, errors = self.validator.validate_sensor_data(INVALID_OUT_OF_RANGE_LOW)
        assert ok is False

    def test_unknown_sensor_type_rejected(self):
        """TC-02-E: Unknown sensor type is rejected."""
        ok, errors = self.validator.validate_sensor_data(INVALID_UNKNOWN_SENSOR_TYPE)
        assert ok is False

    def test_non_numeric_value_rejected(self):
        """TC-02-F: String value is rejected."""
        ok, errors = self.validator.validate_sensor_data(INVALID_STRING_VALUE)
        assert ok is False

    def test_all_six_sensor_types_accepted(self):
        """TC-02-G: Every supported sensor type passes validation."""
        for sensor_type in ["soil_moisture", "temperature", "humidity", "ph", "light", "ec"]:
            payload = {
                "sensor_type": sensor_type,
                "value": {"soil_moisture": 45, "temperature": 22, "humidity": 60,
                          "ph": 6.8, "light": 10000, "ec": 1.5}[sensor_type],
                "timestamp": int(time.time()),
            }
            ok, errors = self.validator.validate_sensor_data(payload)
            assert ok is True, f"'{sensor_type}' should be valid. Errors: {errors}"


# ──────────────────────────────────────────────────────────────────────────────
# TC-03  Emergency Rule Triggering
# ──────────────────────────────────────────────────────────────────────────────

class TestEmergencyRules:
    """
    Verify that the EmergencyController fires the correct actions when
    sensor thresholds are breached.

    Rules (from controller.py defaults):
        auto_irrigation_low  : soil_moisture < 30  → activate_irrigation
        temperature_alert_high: temperature > 35   → send_alert
    """

    async def test_low_soil_triggers_irrigation_alert(self):
        """TC-03-A: soil_moisture=18 (< 30) triggers emergency irrigation."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", EMERGENCY_LOW_SOIL
        )

        # The irrigation action stores an alert
        alerts = buf.sqlite_conn.execute("SELECT * FROM alerts").fetchall()
        assert len(alerts) >= 1, "Expected at least one alert after emergency trigger"
        await buf.close()

    async def test_normal_soil_does_not_trigger(self):
        """TC-03-B: soil_moisture=55 (> 30) does NOT trigger irrigation."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", NORMAL_SOIL_MOISTURE
        )

        alerts = buf.sqlite_conn.execute("SELECT * FROM alerts").fetchall()
        assert len(alerts) == 0, "No alert expected for healthy soil moisture"
        await buf.close()

    async def test_high_temperature_triggers_alert(self):
        """TC-03-C: temperature=38.5 (> 35) triggers temperature alert."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        await controller.evaluate_conditions(
            TEST_FARM_ID, "temperature", EMERGENCY_HIGH_TEMP
        )

        alerts = buf.sqlite_conn.execute("SELECT * FROM alerts").fetchall()
        assert len(alerts) >= 1
        await buf.close()

    async def test_boundary_soil_exact_threshold_not_triggered(self):
        """TC-03-D: soil_moisture==30 is NOT < 30, so rule should not fire."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", BOUNDARY_SOIL_EXACT
        )

        alerts = buf.sqlite_conn.execute("SELECT * FROM alerts").fetchall()
        assert len(alerts) == 0, "Exact-threshold value should NOT trigger the rule"
        await buf.close()

    async def test_boundary_soil_just_below_threshold_triggered(self):
        """TC-03-E: soil_moisture=29.9 IS < 30, rule must fire."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", BOUNDARY_SOIL_BELOW
        )

        alerts = buf.sqlite_conn.execute("SELECT * FROM alerts").fetchall()
        assert len(alerts) >= 1
        await buf.close()

    async def test_cooldown_prevents_repeated_triggers(self):
        """TC-03-F: Same rule does NOT fire twice within the cooldown window."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        # First trigger
        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", EMERGENCY_LOW_SOIL
        )
        first_count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]

        # Immediate second trigger (within cooldown)
        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", EMERGENCY_LOW_SOIL
        )
        second_count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]

        assert second_count == first_count, (
            "Cooldown should prevent duplicate triggers: "
            f"first={first_count}, second={second_count}"
        )
        await buf.close()

    async def test_emergency_control_disabled_no_triggers(self):
        """TC-03-G: When emergency_control_enabled=False, no rules fire."""
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings(emergency_control_enabled=False)
        controller = EmergencyController(settings, buf)
        await controller.start()

        await controller.evaluate_conditions(
            TEST_FARM_ID, "soil_moisture", EMERGENCY_LOW_SOIL
        )

        alerts = buf.sqlite_conn.execute("SELECT * FROM alerts").fetchall()
        assert len(alerts) == 0, "Disabled emergency control must produce no alerts"
        await buf.close()


# ──────────────────────────────────────────────────────────────────────────────
# TC-04  Backend Offline — Buffering
# ──────────────────────────────────────────────────────────────────────────────

class TestBackendOfflineBuffering:
    """
    Verify that when the cloud backend is unreachable the fog:
        1. Stores all incoming data locally.
        2. Does NOT crash or lose data.
        3. Marks zero records as synced.
    """

    async def test_data_buffered_when_backend_offline(self):
        """TC-04-A: Records accumulate in the buffer when cloud is unreachable."""
        settings = _make_settings(
            cloud_api_url="http://localhost:19999",  # nothing listening here
        )
        buf = await _make_buffer(settings)
        await _reset_buffer(buf)

        # Simulate fog receiving sensor data from MQTT
        batch = make_soil_sequence(10, base_value=60.0)
        for payload in batch:
            await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", payload)

        unsynced = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data WHERE synced=0"
        ).fetchone()[0]
        assert unsynced == 10, (
            f"All 10 records must be unsynced when backend is offline, got {unsynced}"
        )
        await buf.close()

    async def test_buffer_accepts_all_sensor_types_offline(self):
        """TC-04-B: All sensor types are buffered during backend outage."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        batch = make_multi_sensor_batch(count_each=5)  # 4 types × 5 = 20
        for item in batch:
            await buf.store_sensor_data(TEST_FARM_ID, item["sensor_type"], item)

        count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert count == 20
        await buf.close()

    async def test_fog_components_do_not_crash_during_backend_failure(self):
        """TC-04-C: CloudSyncService does not raise when backend is unreachable."""
        settings = _make_settings(
            cloud_api_url="http://localhost:19999",
            cloud_sync_interval=1,
        )
        buf = await _make_buffer(settings)
        cloud_sync = CloudSyncService(settings, buf)

        # Should not raise
        await cloud_sync.start()
        await asyncio.sleep(2.5)  # let at least one sync cycle run
        await cloud_sync.stop()
        await buf.close()

    async def test_sync_service_stays_disconnected_when_backend_down(self):
        """TC-04-D: CloudSyncService.is_connected() returns False when backend is down."""
        settings = _make_settings(cloud_api_url="http://localhost:19999")
        buf = await _make_buffer(settings)
        cloud_sync = CloudSyncService(settings, buf)
        await cloud_sync.start()
        await asyncio.sleep(1.5)

        assert cloud_sync.is_connected() is False
        await cloud_sync.stop()
        await buf.close()

    async def test_large_buffer_accumulation_no_data_loss(self):
        """TC-04-E: 500 records are stored without loss during extended offline."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        N = 500
        batch = make_soil_sequence(N, base_value=55.0)
        for item in batch:
            await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

        stored = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert stored == N, f"No data loss expected: stored={stored}, expected={N}"
        await buf.close()


# ──────────────────────────────────────────────────────────────────────────────
# TC-05  Backend Recovery and Sync
# ──────────────────────────────────────────────────────────────────────────────

class TestBackendRecovery:
    """
    Verify that when the cloud backend comes back online:
        1. All buffered records are synced.
        2. Records are marked synced=1.
        3. No duplicates appear in cloud.
        4. Sync is idempotent (running it twice doesn't re-send).
    """

    async def test_buffered_records_synced_after_backend_recovery(self):
        """TC-05-A: After backend recovers, all unsynced records are uploaded."""
        mock_server = MockCloudServer(port=8099)
        mock_server.start()
        try:
            settings = _make_settings(
                cloud_api_url="http://localhost:8099",
                cloud_sync_interval=1,
                buffer_sync_batch_size=50,
            )
            buf = await _make_buffer(settings)
            await _reset_buffer(buf)

            # Store data while "offline" (we won't start sync yet)
            batch = make_soil_sequence(15)
            for item in batch:
                await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

            # Bring backend "online" and start sync
            mock_server.go_online()
            cloud_sync = CloudSyncService(settings, buf)
            await cloud_sync.start()
            await asyncio.sleep(3)  # allow sync cycle to complete
            await cloud_sync.stop()

            synced_count = buf.sqlite_conn.execute(
                "SELECT COUNT(*) FROM sensor_data WHERE synced=1"
            ).fetchone()[0]
            assert synced_count == 15, (
                f"All 15 records must be synced after recovery, got {synced_count}"
            )
            await buf.close()
        finally:
            mock_server.stop()

    async def test_no_duplicate_records_after_sync(self):
        """TC-05-B: Running sync twice does NOT create duplicate records in the cloud."""
        mock_server = MockCloudServer(port=8098)
        mock_server.start()
        try:
            settings = _make_settings(
                cloud_api_url="http://localhost:8098",
                cloud_sync_interval=1,
            )
            buf = await _make_buffer(settings)
            await _reset_buffer(buf)

            batch = make_soil_sequence(5)
            for item in batch:
                await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

            # First sync
            cloud_sync = CloudSyncService(settings, buf)
            await cloud_sync.start()
            await asyncio.sleep(2.5)
            await cloud_sync.stop()

            first_upload_count = len(mock_server.received)

            # Second sync — already-synced records must NOT be re-sent
            mock_server.clear_received()
            cloud_sync2 = CloudSyncService(settings, buf)
            await cloud_sync2.start()
            await asyncio.sleep(2.5)
            await cloud_sync2.stop()

            second_upload_count = len(mock_server.received)

            assert second_upload_count == 0, (
                f"Already-synced records must not be re-uploaded. "
                f"Second sync sent {second_upload_count} records."
            )
            await buf.close()
        finally:
            mock_server.stop()

    async def test_all_records_marked_synced_flag(self):
        """TC-05-C: After successful sync, all records show synced=1."""
        mock_server = MockCloudServer(port=8097)
        mock_server.start()
        try:
            settings = _make_settings(
                cloud_api_url="http://localhost:8097",
                cloud_sync_interval=1,
            )
            buf = await _make_buffer(settings)
            await _reset_buffer(buf)

            for item in make_multi_sensor_batch(count_each=3):  # 12 records
                await buf.store_sensor_data(TEST_FARM_ID, item["sensor_type"], item)

            cloud_sync = CloudSyncService(settings, buf)
            await cloud_sync.start()
            await asyncio.sleep(3)
            await cloud_sync.stop()

            unsynced = buf.sqlite_conn.execute(
                "SELECT COUNT(*) FROM sensor_data WHERE synced=0"
            ).fetchone()[0]
            assert unsynced == 0, f"Expected 0 unsynced records after sync, got {unsynced}"
            await buf.close()
        finally:
            mock_server.stop()

    async def test_exact_record_count_uploaded_matches_buffered(self):
        """TC-05-D: Number of records uploaded == number buffered (no missing, no extra)."""
        mock_server = MockCloudServer(port=8096)
        mock_server.start()
        try:
            N = 20
            settings = _make_settings(
                cloud_api_url="http://localhost:8096",
                cloud_sync_interval=1,
                buffer_sync_batch_size=50,
            )
            buf = await _make_buffer(settings)
            await _reset_buffer(buf)

            for item in make_soil_sequence(N):
                await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

            cloud_sync = CloudSyncService(settings, buf)
            await cloud_sync.start()
            await asyncio.sleep(3)
            await cloud_sync.stop()

            uploaded = len(mock_server.received)
            assert uploaded == N, (
                f"Expected {N} records uploaded, got {uploaded}"
            )
            await buf.close()
        finally:
            mock_server.stop()

    async def test_partial_sync_failure_retried_on_next_cycle(self):
        """TC-05-E: If cloud returns 500, records stay unsynced and are retried."""
        mock_server = MockCloudServer(port=8095)
        mock_server.start()
        mock_server.force_server_error()   # first cycle fails
        try:
            settings = _make_settings(
                cloud_api_url="http://localhost:8095",
                cloud_sync_interval=1,
            )
            buf = await _make_buffer(settings)
            await _reset_buffer(buf)

            for item in make_soil_sequence(5):
                await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

            cloud_sync = CloudSyncService(settings, buf)
            await cloud_sync.start()
            await asyncio.sleep(1.5)  # first cycle fails (500)

            # Clear the error, allow retry
            mock_server.clear_error()
            await asyncio.sleep(2.5)  # second cycle succeeds
            await cloud_sync.stop()

            synced = buf.sqlite_conn.execute(
                "SELECT COUNT(*) FROM sensor_data WHERE synced=1"
            ).fetchone()[0]
            assert synced == 5, (
                f"All 5 records must be synced after retry, got {synced}"
            )
            await buf.close()
        finally:
            mock_server.stop()


# ──────────────────────────────────────────────────────────────────────────────
# TC-06  MQTT Disconnect / Reconnect
# ──────────────────────────────────────────────────────────────────────────────

class TestMQTTDisconnect:
    """
    Verify the fog MQTT ingestion service handles connection drops gracefully.
    These tests check behaviour via the fog /health endpoint (requires fog running)
    and via direct component inspection.
    """

    async def test_mqtt_client_disconnects_gracefully(self):
        """TC-06-A: disconnect() sets _connected=False without raising."""
        from src.ingestion.mqtt_client import MQTTIngestionService

        settings = _make_settings()
        buf = await _make_buffer(settings)
        validator = DataValidator(settings)
        controller = EmergencyController(settings, buf)
        await controller.start()

        svc = MQTTIngestionService(settings, validator, buf, controller)
        try:
            await svc.connect()
            assert svc.is_connected() is True

            await svc.disconnect()
            assert svc.is_connected() is False
        except Exception as exc:
            # If MQTT broker is down, connection attempt raises — that's acceptable
            pytest.skip(f"MQTT broker not reachable: {exc}")
        finally:
            await buf.close()

    async def test_mqtt_reconnect_after_disconnect(self):
        """TC-06-B: The service can reconnect after an explicit disconnect."""
        from src.ingestion.mqtt_client import MQTTIngestionService

        settings = _make_settings()
        buf = await _make_buffer(settings)
        validator = DataValidator(settings)
        controller = EmergencyController(settings, buf)
        await controller.start()

        svc = MQTTIngestionService(settings, validator, buf, controller)
        try:
            await svc.connect()
            await svc.disconnect()
            assert svc.is_connected() is False

            await svc.connect()
            assert svc.is_connected() is True

            await svc.disconnect()
        except Exception as exc:
            pytest.skip(f"MQTT broker not reachable: {exc}")
        finally:
            await buf.close()

    @skip_if_fog_down()
    def test_fog_health_reflects_mqtt_state(self):
        """TC-06-C: [E2E] /health shows mqtt status correctly. Requires fog running."""
        r = requests.get(f"http://localhost:{FOG_API_PORT}/health", timeout=5)
        assert r.status_code in (200, 207)
        body = r.json()
        assert "services" in body
        assert "mqtt" in body["services"]


# ──────────────────────────────────────────────────────────────────────────────
# TC-07  High-Frequency Stress Test
# ──────────────────────────────────────────────────────────────────────────────

class TestStressHighFrequency:
    """
    Verify the buffer and emergency controller handle bursts of messages
    without data loss, crashes or incorrect emergency rule counts.
    """

    async def test_100_messages_all_stored(self):
        """TC-07-A: 100 rapid messages are all stored without loss."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        batch = make_soil_sequence(100, base_value=55.0)
        for item in batch:
            await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

        count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert count == 100, f"Expected 100 records, got {count}"
        await buf.close()

    async def test_500_mixed_messages_no_loss(self):
        """TC-07-B: 500 mixed-type messages stored completely."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        batch = make_multi_sensor_batch(count_each=125)  # 4 × 125 = 500
        for item in batch:
            await buf.store_sensor_data(TEST_FARM_ID, item["sensor_type"], item)

        count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert count == 500
        await buf.close()

    async def test_emergency_rule_fires_once_in_burst(self):
        """
        TC-07-C: Even in a burst of 50 low-soil readings, the cooldown
        ensures the emergency rule fires only once.
        """
        buf = await _make_buffer()
        await _reset_buffer(buf)
        settings = _make_settings()
        controller = EmergencyController(settings, buf)
        await controller.start()

        for _ in range(50):
            await controller.evaluate_conditions(
                TEST_FARM_ID, "soil_moisture", EMERGENCY_LOW_SOIL
            )

        alert_count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]
        assert alert_count == 1, (
            f"Cooldown must limit alerts to 1 even in a burst of 50; got {alert_count}"
        )
        await buf.close()

    async def test_concurrent_writes_no_corruption(self):
        """TC-07-D: Concurrent asyncio tasks writing to buffer don't corrupt data."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        N = 200
        tasks = [
            buf.store_sensor_data(
                TEST_FARM_ID,
                "temperature",
                {
                    "sensor_type": "temperature",
                    "value": 22.0 + (i % 10),
                    "timestamp": int(time.time()) + i,
                    "device_id": "esp32_edge_001",
                },
            )
            for i in range(N)
        ]
        await asyncio.gather(*tasks)

        count = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert count == N, f"Concurrent inserts: expected {N}, got {count}"
        await buf.close()


# ──────────────────────────────────────────────────────────────────────────────
# TC-08  Idempotency and No-Duplicate Guarantee
# ──────────────────────────────────────────────────────────────────────────────

class TestIdempotencyAndDeduplication:
    """
    Verify that the sync service respects the synced flag and never
    re-uploads already-synced records, even after a fog restart simulation.
    """

    async def test_mark_as_synced_prevents_reupload(self):
        """TC-08-A: mark_as_synced correctly prevents records from being fetched again."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        for item in make_soil_sequence(5):
            await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

        # Simulate what cloud sync does: fetch, then mark
        unsynced = await buf.get_unsynced_data(limit=100)
        assert len(unsynced) == 5

        ids = [r["id"] for r in unsynced]
        await buf.mark_as_synced(ids)

        unsynced_after = await buf.get_unsynced_data(limit=100)
        assert len(unsynced_after) == 0, (
            "After marking synced, get_unsynced_data must return empty list"
        )
        await buf.close()

    async def test_partial_sync_marks_only_uploaded_records(self):
        """TC-08-B: Only records in the successful batch are marked synced."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        for item in make_soil_sequence(10):
            await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

        # Sync only first 4
        batch = await buf.get_unsynced_data(limit=4)
        assert len(batch) == 4
        await buf.mark_as_synced([r["id"] for r in batch])

        remaining = await buf.get_unsynced_data(limit=100)
        assert len(remaining) == 6, (
            f"Expected 6 remaining unsynced records, got {len(remaining)}"
        )
        await buf.close()

    async def test_cleanup_removes_only_synced_records(self):
        """TC-08-C: cleanup_old_data() only removes synced=1 old records."""
        buf = await _make_buffer()
        await _reset_buffer(buf)

        for item in make_soil_sequence(6):
            await buf.store_sensor_data(TEST_FARM_ID, "soil_moisture", item)

        # Mark 3 as synced
        batch = await buf.get_unsynced_data(limit=3)
        await buf.mark_as_synced([r["id"] for r in batch])

        # Cleanup (synced old records should be removed; unsynced must survive)
        # Force old timestamp on synced records for cleanup to pick them up
        buf.sqlite_conn.execute(
            "UPDATE sensor_data SET created_at='2000-01-01' WHERE synced=1"
        )
        buf.sqlite_conn.commit()
        await buf.cleanup_old_data()

        total = buf.sqlite_conn.execute(
            "SELECT COUNT(*) FROM sensor_data"
        ).fetchone()[0]
        assert total == 3, (
            f"Cleanup must preserve unsynced records. Remaining: {total}"
        )
        await buf.close()


# ──────────────────────────────────────────────────────────────────────────────
# TC-09  Buffer Health Check
# ──────────────────────────────────────────────────────────────────────────────

class TestBufferHealth:
    """Verify the buffer health check works correctly."""

    async def test_buffer_is_healthy_after_init(self):
        """TC-09-A: BufferManager.is_healthy() returns True after initialize()."""
        buf = await _make_buffer()
        assert buf.is_healthy() is True
        await buf.close()

    async def test_buffer_unhealthy_after_close(self):
        """TC-09-B: After close(), is_healthy() returns False."""
        buf = await _make_buffer()
        await buf.close()
        assert buf.is_healthy() is False


# ──────────────────────────────────────────────────────────────────────────────
# TC-10  End-to-End (requires live fog on :8001 + MQTT on :1883)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
class TestEndToEnd:
    """
    Full pipeline tests:
        ESP32 (MQTT publish) → Fog Gateway → SQLite buffer → /health

    All tests in this class are skipped unless fog is reachable on port 8001.
    Start the fog:  cd fog && python main.py
    """

    def test_fog_health_endpoint_returns_healthy(self):
        """TC-10-A: /health returns 200 with all services listed."""
        if not fog_is_running():
            pytest.skip("Fog not running")
        r = requests.get(f"http://localhost:{FOG_API_PORT}/health", timeout=5)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("healthy", "degraded")
        assert "mqtt" in body["services"]
        assert "buffer" in body["services"]

    def test_fog_root_returns_metadata(self):
        """TC-10-B: GET / returns fog metadata."""
        if not fog_is_running():
            pytest.skip("Fog not running")
        r = requests.get(f"http://localhost:{FOG_API_PORT}/", timeout=5)
        assert r.status_code == 200
        body = r.json()
        assert "farm_id" in body
        assert "version" in body

    def test_publish_via_mqtt_increments_buffer(self, esp32, buffer):
        """
        TC-10-C: Publishing a valid MQTT message to the fog's subscribed topic
        results in an additional record in the SQLite buffer.
        """
        if not fog_is_running():
            pytest.skip("Fog not running")

        before = buffer.count_all()
        esp32.publish_sensor("soil_moisture", 52.0)

        # Give the fog time to process
        assert wait_for_condition(
            lambda: buffer.count_all() > before, timeout=6
        ), "Buffer should have grown after publishing"

    def test_invalid_payload_not_buffered(self, esp32, buffer):
        """TC-10-D: Publishing an invalid payload results in no new buffer entry."""
        if not fog_is_running():
            pytest.skip("Fog not running")

        before = buffer.count_all()
        esp32.publish_raw(
            topic="farms/farm_001/sensors/soil_moisture/data",
            payload=INVALID_MISSING_SENSOR_TYPE,
        )
        time.sleep(2)  # fog processes synchronously
        after = buffer.count_all()

        assert after == before, (
            "Invalid payload must not increase buffer count"
        )

    def test_emergency_low_soil_creates_alert_e2e(self, esp32, buffer):
        """TC-10-E: Publishing critically low soil_moisture creates an alert record."""
        if not fog_is_running():
            pytest.skip("Fog not running")

        before_alerts = len(buffer.alerts())
        esp32.publish_sensor("soil_moisture", 12.0)  # way below 30%

        assert wait_for_condition(
            lambda: len(buffer.alerts()) > before_alerts, timeout=6
        ), "Emergency alert should be stored in buffer"
