# Fog Gateway — Integration Test Plan

**Project**: Smart Farming IoT Platform  
**Component Under Test**: Fog Gateway (`fog/`)  
**Test File**: `tests/integration/fog/test_fog_integration.py`  
**Last Updated**: 2025  

---

## 1. Overview

The Fog Gateway sits between the ESP32 edge device and the cloud backend.  
It is responsible for:

| Responsibility | Implementation |
|---|---|
| MQTT ingestion | `fog/src/ingestion/mqtt_client.py` |
| Payload validation | `fog/src/preprocessing/validator.py` |
| Local buffering (SQLite) | `fog/src/buffer_manager/buffer.py` |
| Cloud synchronisation | `fog/src/cloud_sync/sync_service.py` |
| Emergency rule evaluation | `fog/src/emergency_control/controller.py` |
| REST health endpoint | `fog/main.py` → FastAPI on `localhost:8001` |

---

## 2. Test Architecture

### 2.1 Test Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  E2E Tests (pytest.mark.e2e)                                    │
│  - Require live fog process on :8001 and MQTT broker on :1883   │
│  - Publish via ESP32Publisher MQTT → fog → assert via HTTP      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  Component Integration Tests (default, no mark required)        │
│  - Instantiate fog components directly in test (no live server) │
│  - Inject data via Python method calls, not MQTT                │
│  - Assert SQLite state directly                                  │
│  - Mock cloud server on dynamic port per test class             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Helpers

| Helper | File | Purpose |
|---|---|---|
| `MockCloudServer` | `conftest.py` | Thread-based HTTP server; supports online/offline/500-error toggle |
| `ESP32Publisher` | `conftest.py` | MQTT publisher simulating ESP32 |
| `BufferInspector` | `conftest.py` | Direct SQLite read-only access for assertions |
| `wait_for_condition` | `conftest.py` | Polling helper for async state changes |
| Sensor payloads | `payloads.py` | Pre-built valid, invalid, edge-case and bulk payloads |

---

## 3. Test Cases

### TC-01 — Normal Data Flow

**Objective**: Valid sensor readings are stored correctly in the buffer.

| ID | Name | Precondition | Steps | Expected |
|---|---|---|---|---|
| TC-01-A | Valid soil stored | Buffer empty | Call `buf.store_sensor_data("soil_moisture", ...)` | 1 record in SQLite |
| TC-01-B | All sensor types accepted | Buffer empty | Store temperature, humidity, light, soil | 4 records in SQLite |
| TC-01-C | New records unsynced | Buffer empty | Store any reading | `synced=0` on new row |
| TC-01-D | Value accuracy | Buffer empty | Store humidity=72.3 | SQLite row value ≈ 72.3 |

---

### TC-02 — Data Validation

**Objective**: The `DataValidator` accepts only valid payloads; rejected payloads never reach the buffer.

| ID | Name | Input | Expected |
|---|---|---|---|
| TC-02-A | Valid soil passes | `NORMAL_SOIL_MOISTURE` | `(True, [])` |
| TC-02-B | Missing sensor_type | `INVALID_MISSING_SENSOR_TYPE` | `(False, [...])` containing "sensor_type" |
| TC-02-C | Missing value | `INVALID_MISSING_VALUE` | `(False, [...])` containing "value" |
| TC-02-D | Missing timestamp | `INVALID_MISSING_TIMESTAMP` | `(False, [...])` containing "timestamp" |
| TC-02-E | Empty dict | `INVALID_EMPTY` | `(False, [...])` |
| TC-02-F | Value above max | `INVALID_OUT_OF_RANGE_HIGH` | `(False, [...])` mentioning "range" |
| TC-02-G | Value below min | `INVALID_OUT_OF_RANGE_LOW` | `(False, [...])` |
| TC-02-H | Unknown sensor type | `INVALID_UNKNOWN_SENSOR_TYPE` | `(False, [...])` |
| TC-02-I | String value (non-numeric) | `INVALID_STRING_VALUE` | `(False, [...])` |
| TC-02-J | All 6 sensor types | Valid payload for each | All pass `(True, [])` |

---

### TC-03 — Emergency Rule Triggering

**Objective**: Emergency rules fire at the right thresholds and respect cooldowns.

| ID | Name | Input | Expected |
|---|---|---|---|
| TC-03-A | Low soil triggers irrigation | soil=18.0 (< 30) | Alert stored in `alerts` table |
| TC-03-B | Normal soil no alert | soil=55.0 (> 30) | 0 alerts |
| TC-03-C | High temp triggers alert | temperature=38.5 (> 35) | Alert stored |
| TC-03-D | Exact threshold not triggered | soil=30.0 (NOT < 30) | 0 alerts |
| TC-03-E | Just below threshold triggers | soil=29.9 (< 30) | 1 alert |
| TC-03-F | Cooldown prevents repeat | soil=18.0 × 2 (< 1s apart) | Exactly 1 alert (cooldown suppresses 2nd) |
| TC-03-G | Emergency disabled | `emergency_control_enabled=False` | 0 alerts even for soil=18.0 |

**Thresholds** (from `controller.py`):
- `auto_irrigation_low`: `soil_moisture < 30.0`, cooldown 600 s
- `temperature_alert_high`: `temperature > 35.0`, cooldown 300 s

---

### TC-04 — Backend Offline Buffering

**Objective**: When the cloud backend is unreachable, the fog buffers all data locally without crashing.

| ID | Name | Setup | Steps | Expected |
|---|---|---|---|---|
| TC-04-A | Data buffered when offline | cloud_api_url → :19999 (nothing) | Store 10 records | `unsynced=10` |
| TC-04-B | All sensor types buffered offline | Same | Store 4×5 = 20 records | `count=20` |
| TC-04-C | CloudSyncService doesn't crash | Same | Run sync for 2 s | No exception raised |
| TC-04-D | is_connected() returns False | Same | Check after 1 sync cycle | `False` |
| TC-04-E | Large buffer (500 records) no loss | Same | Store 500 records | `count=500` |

---

### TC-05 — Backend Recovery and Sync

**Objective**: After the cloud recovers, all buffered records are uploaded exactly once.

| ID | Name | Setup | Steps | Expected |
|---|---|---|---|---|
| TC-05-A | Buffered records synced on recovery | Offline, store 15, then online | Start sync, wait 3 s | `synced=15` |
| TC-05-B | No duplicates after second sync | Sync once, clear `received`, sync again | — | Second sync uploads 0 records |
| TC-05-C | All records get synced=1 flag | Store 12, sync | After sync | `unsynced=0` |
| TC-05-D | Exact count uploaded | Store 20, sync | Check `mock_server.received` | `len(received)==20` |
| TC-05-E | Partial failure retried | First cycle → 500, second → 200 | Clear error, wait | `synced=5` after retry |

---

### TC-06 — MQTT Disconnect / Reconnect

**Objective**: The MQTT ingestion service handles connection drops without data loss.

| ID | Name | Requires fog? | Expected |
|---|---|---|---|
| TC-06-A | Disconnect sets `_connected=False` | MQTT broker only | `is_connected()` False after `disconnect()` |
| TC-06-B | Reconnect works after disconnect | MQTT broker only | `is_connected()` True after re-`connect()` |
| TC-06-C | /health reflects MQTT state | **Live fog** | `body["services"]["mqtt"]` present |

---

### TC-07 — High-Frequency Stress

**Objective**: The system handles bursts of messages without data loss or corruption.

| ID | Name | Volume | Expected |
|---|---|---|---|
| TC-07-A | 100 rapid messages stored | 100 × soil_moisture | `count=100` |
| TC-07-B | 500 mixed messages no loss | 4 types × 125 | `count=500` |
| TC-07-C | Burst of 50 low-soil alerts → 1 alert | 50 × soil=18.0 | Exactly 1 alert (cooldown) |
| TC-07-D | 200 concurrent async writes no corruption | `asyncio.gather` 200 tasks | `count=200` |

---

### TC-08 — Idempotency and No-Duplicate Guarantee

**Objective**: The sync mechanism never re-uploads already-synced records.

| ID | Name | Steps | Expected |
|---|---|---|---|
| TC-08-A | mark_as_synced prevents refetch | Store 5, fetch, mark, re-fetch | `get_unsynced_data` returns `[]` |
| TC-08-B | Partial batch marks only uploaded | Store 10, mark first 4 | 6 remain unsynced |
| TC-08-C | cleanup_old_data preserves unsynced | Mark 3 synced (old), run cleanup | 3 unsynced records survive |

---

### TC-09 — Buffer Health

| ID | Name | Expected |
|---|---|---|
| TC-09-A | `is_healthy()` True after `initialize()` | True |
| TC-09-B | `is_healthy()` False after `close()` | False |

---

### TC-10 — End-to-End (E2E, requires live fog)

> Start the fog before running: `cd fog && python main.py`

| ID | Name | Steps | Expected |
|---|---|---|---|
| TC-10-A | /health returns 200 | GET /health | `status in ("healthy", "degraded")`, `services` has `mqtt`, `buffer` |
| TC-10-B | / returns metadata | GET / | Body has `farm_id`, `version` |
| TC-10-C | MQTT publish increments buffer | `esp32.publish_sensor("soil_moisture", 52.0)` | Buffer count increases within 6 s |
| TC-10-D | Invalid payload not buffered | Publish `INVALID_MISSING_SENSOR_TYPE` | Buffer count unchanged |
| TC-10-E | Emergency low soil creates alert | `esp32.publish_sensor("soil_moisture", 12.0)` | Alert count increases within 6 s |

---

## 4. Running the Tests

### 4.1 Install dependencies

```powershell
cd C:\Users\aml\Desktop\mini_project
.venv\Scripts\python.exe -m pip install pytest pytest-asyncio paho-mqtt requests httpx
```

### 4.2 Component tests only (no live fog needed)

```powershell
.venv\Scripts\pytest.exe tests/integration/fog/ -v -m "not e2e"
```

### 4.3 All tests including E2E

Start dependencies first:

```powershell
# Terminal 1 – Mosquitto (MQTT broker)
net start mosquitto

# Terminal 2 – Fog Gateway
cd C:\Users\aml\Desktop\mini_project\fog
..\venv\Scripts\python.exe main.py
```

Then:

```powershell
.venv\Scripts\pytest.exe tests/integration/fog/ -v
```

### 4.4 With coverage report

```powershell
.venv\Scripts\pytest.exe tests/integration/fog/ -v --cov=fog/src --cov-report=term-missing
```

### 4.5 Individual test class

```powershell
.venv\Scripts\pytest.exe tests/integration/fog/test_fog_integration.py::TestEmergencyRules -v
```

---

## 5. Sensor Ranges (from `validator.py`)

| Sensor | Min | Max | Units |
|---|---|---|---|
| soil_moisture | 0 | 100 | % |
| temperature | -40 | 80 | °C |
| humidity | 0 | 100 | % |
| ph | 0 | 14 | pH |
| light | 0 | 100000 | lux |
| ec | 0 | 10 | mS/cm |

---

## 6. Emergency Rule Thresholds (from `controller.py`)

| Rule ID | Sensor | Condition | Action | Cooldown |
|---|---|---|---|---|
| `auto_irrigation_low` | soil_moisture | value **< 30.0** | `activate_irrigation` | 600 s |
| `temperature_alert_high` | temperature | value **> 35.0** | `send_alert` | 300 s |
