# AgriTwin — Resource-aware Digital Twin Framework for Precision Micro-farming

> **Public snapshot.** This is a clean copy of my private development repository. Network credentials and the OTA password were removed, so set your own in `edge/src/main.cpp` (or `edge/configs/config_template.h`) before flashing. Development history stays in the private repo.


> Real-time IoT monitoring system with digital twin physics simulation, AI assistant (LLaMA 3), twin accuracy monitoring, Prometheus metrics, OTA firmware updates, offline mobile support, and a Flutter companion app — built for intelligent micro-farming in resource-constrained environments.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Firmware](https://img.shields.io/badge/firmware-v1.1.0-blue)](edge/src/main.cpp)
[![Backend](https://img.shields.io/badge/backend-FastAPI%200.111-green)](cloud/backend/main_working.py)
[![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-black)](cloud/frontend)
[![Mobile](https://img.shields.io/badge/mobile-Flutter%203-blue)](mobile)

---

## Architecture Overview

AgriTwin uses a **4-layer edge-to-cloud hierarchy**:

```
[ ESP32 Edge ] ---MQTT:1883---> [ Raspberry Pi Fog ] ---HTTP:8000---> [ Cloud / Laptop ]
      |                                  |                                      |
   DHT11, LDR, Soil, 2x Relay      Mosquitto broker                   FastAPI :8000
   GPIO 4, 33, 34, 26, 25          InfluxDB 1.6 local buffer          Next.js :3000
   firmware v1.1.0                 fog_server.py sync                 Ollama/LLaMA3 :11434
   OTA via ArduinoOTA              camera_service.py                  SQLite DB
   hardware watchdog 30s           agritwin-fog.local                 DT Brain + Twin Accuracy
                                                                               |
                                                                    [ Flutter Mobile App ]
                                                                   Android / iOS / Windows
                                                                   8 tabs, offline cache
```

### Data Flow
```
ESP32 publishes every 10s
  -> farms/001/sensors/temperature/data  (JSON per sensor)
  -> agritwin/sensors                    (combined JSON)
         |
Pi Mosquitto broker :1883
  -> fog_server.py -> InfluxDB 1.6 (port 8086)
  -> every 30s: POST /api/v1/sensors/ingest -> Cloud SQLite
  -> camera_service.py -> every 5min: POST /api/v1/camera/upload
         |
Cloud mqtt_client.py (direct subscriber to Pi broker)
  -> SQLite sensor_history.db
  -> WebSocket broadcast to browser
  -> Digital Twin physics engine (simulate_step every reading)
  -> Twin Accuracy store_prediction()
         |
Next.js dashboard polls /api/v1/sensors/latest every 5s
Flutter app polls every 5s (cached offline on failure)
```

---

## Tech Stack

| Layer | Component | Technology | Version |
|-------|-----------|-----------|---------|
| Edge | Microcontroller firmware | ESP32 + PlatformIO (C++) | Firmware v1.1.0 |
| Edge | OTA updates | ArduinoOTA | built-in |
| Edge | Watchdog | esp_task_wdt | 30s timeout |
| Fog | MQTT broker | Eclipse Mosquitto | 2.x |
| Fog | Time-series buffer | InfluxDB | 1.6.7 |
| Fog | Fog gateway | Python 3 fog_server.py | — |
| Fog | Camera capture | Python + fswebcam | — |
| Cloud | REST API | FastAPI | 0.111 |
| Cloud | Sensor database | SQLite 3 | — |
| Cloud | AI assistant | Ollama + LLaMA 3 8B | — |
| Cloud | Web dashboard | Next.js 14 + React 18 | — |
| Cloud | Charts | Recharts | 2.x |
| Cloud | Animations | Framer Motion | 11.x |
| Cloud | Digital Twin | Python physics engine | — |
| Cloud | Observability | Prometheus metrics | — |
| Mobile | App framework | Flutter + Dart | 3.x |
| Mobile | Offline storage | shared_preferences | — |
| Mobile | Charts | fl_chart | — |

---

## Features

### Edge (ESP32 firmware v1.1.0)
- 4-sensor reading loop — DHT11 (temp+humidity), LDR (light %), capacitive soil moisture
- Dual relay control — water pump (GPIO 26) and grow light (GPIO 25), active-LOW
- Auto-control mode — pump/light triggered automatically by sensor thresholds
- MQTT publish — structured JSON per sensor + combined topic every 10s
- OTA firmware updates — password set in firmware (change the default), hostname `esp32-agritwin`
- Hardware watchdog — 30-second timeout, auto-reboot on hang
- Multi-WiFi fallback — tries up to three networks in priority order
- mDNS resolution — connects to `agritwin-fog.local` without hardcoded IP
- LWT (Last Will and Testament) — publishes offline status on disconnect

### Fog (Raspberry Pi Zero 2 W)
- Mosquitto broker — MQTT backbone for all device communication
- InfluxDB 1.6 local buffer — stores readings locally even when cloud is down
- fog_server.py — syncs buffered data to cloud every 30s
- camera_service.py — captures images every 5 minutes, uploads to cloud
- Systemd services — all fog processes auto-start on Pi boot

### Cloud Backend (FastAPI)
- REST API — 90+ endpoints: sensors, relay, camera, AI, digital twin, metrics
- MQTT bridge — mqtt_client.py subscribes directly to Pi broker
- WebSocket — real-time sensor push to browser (/ws/{farm_id})
- Digital twin engine — Penman-Monteith ET, GDD accumulation, water balance
- Twin Accuracy Monitor — tracks prediction vs. actual, 6 physics model states
- AI assistant — LLaMA 3 via Ollama with live sensor + physics context
- Prometheus metrics — /metrics endpoint, sensor counters, twin accuracy gauges
- Calibration API — Thompson Sampling adaptive interval adjustment
- Multi-Agent System — autonomous farm decision agents

### Cloud Dashboard (Next.js 14)
- Live sensor gauges — temperature, humidity, light %, soil moisture (5s refresh)
- PlantDive — 96-frame plant scroll animation with live ET, GDD, water deficit, growth stage
- History charts — 24h/7d/30d Recharts line charts
- Camera gallery — live view + archive
- AI chat — farm-context-aware LLaMA 3 chatbot
- DT Brain dashboard — 6 physics model cards, accuracy ring, prediction history
- Relay controls — pump & light toggle with live state feedback

### Flutter Mobile App (8 screens)
| Tab | Screen | Features |
|-----|--------|----------|
| 1 | Dashboard | Live sensors, crop health score, quick actions |
| 2 | History | Time-series charts, stats |
| 3 | Camera | Image gallery, capture trigger |
| 4 | Alerts | Sensor threshold alerts |
| 5 | AI Assistant | LLaMA 3 chat |
| 6 | DT Brain | Twin accuracy ring, 6 physics model cards |
| 7 | Settings | Theme, server config |
| 8 | Calibration | Sensor calibration tools |

- Offline cache — last sensor reading served when server unreachable
- Pending command queue — relay commands queued offline, replayed on reconnect
- Dark/light theme — persistent via shared_preferences
- Physics widgets — VPD (Tetens formula), DLI, ET, crop health score, growth stage

---

## Hardware

### ESP32 Pin Assignments

| Component | GPIO | Type | Reason |
|-----------|------|------|--------|
| DHT11 (temp+humidity) | GPIO 4 | Digital input | Not on ADC2 (would conflict with WiFi) |
| LDR (light) | GPIO 33 | ADC1 analog | ADC1 — safe with WiFi active |
| Soil moisture | GPIO 34 | ADC1 input-only | ADC1 input-only pin — ideal for analog |
| Water pump relay | GPIO 26 | Digital output | GPIO output, active-LOW |
| Grow light relay | GPIO 25 | Digital output | Adjacent to GPIO 26, convenient pairing |

> **Why ADC1?** ESP32 ADC2 is shared with the WiFi radio and gives unreliable readings when WiFi is active. GPIO 33 and 34 use ADC1 exclusively.

> **Why active-LOW relays?** Most relay modules use optocouplers that fire on LOW. Boot/reset defaults all GPIOs HIGH — so relays stay OFF during reset.

### Raspberry Pi Zero 2 W
- Hostname: `agritwin-fog.local` (192.168.1.7)
- Camera: Logitech C270 USB webcam on /dev/video0
- OS: Raspberry Pi OS Lite (Debian 13 trixie)

### Network (home Wi-Fi — 192.168.1.x)
| Device | Address |
|--------|---------|
| Laptop (Cloud) | 192.168.1.4 |
| Raspberry Pi (Fog) | 192.168.1.7 |
| ESP32 | DHCP / esp32-agritwin.local |
| Phone | DHCP |

---

## API Quick Reference (FastAPI :8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/sensors/latest | Latest sensor reading |
| GET | /api/v1/sensors/history | Historical readings |
| GET | /api/v1/sensors/stats | Min/max/avg |
| POST | /api/v1/sensors/ingest | Fog batch sync |
| POST | /api/v1/relay/control | Pump/light control |
| GET | /api/v1/camera/latest | Latest image metadata |
| GET | /api/v1/camera/list | Paginated gallery |
| POST | /api/v1/camera/upload | Pi image upload |
| POST | /api/v1/ai/chat | AI chat (LLaMA 3) |
| GET | /api/v1/ai/status | Ollama status |
| GET | /api/v1/twin-accuracy/brain | DT Brain — all 6 models + GDD + ET |
| GET | /api/v1/twin-accuracy/stats | Accuracy %, MAE, RMSE |
| GET | /metrics | Prometheus metrics |
| GET | /health | Health check |
| WS | /ws/{farm_id} | Real-time sensor WebSocket |

---

## MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| agritwin/sensors | ESP32 → Pi | temp, humidity, light, soil, relay state, fw_version |
| farms/001/sensors/{type}/data | ESP32 → Pi | {sensor_type, value, timestamp, device_id} |
| farms/001/commands | Cloud → ESP32 | {command, relay, state} |
| farms/001/relay/state | ESP32 → Cloud | {pump, light} (retained) |
| farms/001/status | ESP32 → Pi | online|offline |

---

## Digital Twin Physics Models

| # | Model | Equation |
|---|-------|----------|
| 1 | Soil Moisture Balance | M(t+1) = M(t) + I - E - U |
| 2 | Evaporation | E ∝ T × (1 - H) |
| 3 | Plant Water Uptake | U = k × light |
| 4 | Light Influence | growth_rate = a × light_level |
| 5 | Temperature Effect | ET_rate = base × temp_factor |
| 6 | Time Evolution | moisture extrapolation |

ET calculated via simplified Penman-Monteith. GDD = Σ max(0, T - 10°C) × (timestep_hours/24).

---

## Quick Start

```
Double-click START_AGRITWIN.bat
```

Or manually:
```powershell
# Backend
cd cloud\backend
..\..\..\.venv\Scripts\python.exe -m uvicorn main_working:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd cloud\frontend && npm run dev

# Ollama
%LOCALAPPDATA%\Programs\Ollama\ollama.exe serve
```

| URL | Service |
|-----|---------|
| http://localhost:3000 | Dashboard |
| http://localhost:3000/dt-brain | DT Brain |
| http://localhost:3000/ai | AI Chat |
| http://localhost:8000/docs | API Swagger |
| http://localhost:8000/metrics | Prometheus |

---

## Repository Structure

```
mini_project/
├── edge/                        ESP32 firmware (PlatformIO)
│   ├── src/main.cpp             Firmware v1.1.0
│   ├── platformio.ini           Board config + OTA partitions
│   └── partitions.csv           OTA partition table
├── fog/                         Raspberry Pi fog layer
│   └── src/                     fog_server.py, camera_service.py
├── cloud/
│   ├── backend/
│   │   ├── main_working.py      FastAPI entry point
│   │   ├── core/                mqtt_client, sensor_storage, twin_accuracy
│   │   └── api/v1/              ai, camera, relay, metrics, twin_accuracy, MAS, ML
│   ├── frontend/                Next.js 14 dashboard
│   │   ├── app/                 page.tsx, dt-brain, ai, camera, mas
│   │   └── components/          PlantDive, DashboardSection, HistoryCharts
│   └── digital_twin/            comprehensive_physics.py
├── mobile/                      Flutter app
│   └── lib/
│       ├── main.dart            8-screen app
│       ├── screens/             dashboard, history, camera, ai, dt_brain, settings...
│       ├── widgets/             crop_health, growth_stage, environment_insights...
│       └── services/            api_service, offline_cache
├── ml/                          ML training scripts
├── tinyml/                      TinyML edge inference
├── data/                        sensor_history.db
├── START_AGRITWIN.bat           One-click startup
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).
