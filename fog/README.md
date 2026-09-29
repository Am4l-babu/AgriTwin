# Fog Layer — Raspberry Pi Zero 2 W Gateway

> **Deployment target:** Raspberry Pi Zero 2 W  
> **Hostname:** `agritwin-fog.local` (mDNS via Avahi)  
> **Role:** MQTT broker + data preprocessing + emergency control + cloud sync

The Fog layer acts as an intelligent edge gateway between IoT devices and the cloud, providing:

- **Local MQTT Broker**: Mosquitto broker for ESP32 communication
- **Data Preprocessing**: Validation, transformation, and enrichment
- **Buffering**: Temporary storage during cloud outages (Redis + SQLite)
- **Emergency Control**: Autonomous decision-making when cloud is unreachable
- **Edge Analytics**: Local data aggregation and filtering
- **Cloud Sync**: Forwards processed data to the laptop cloud backend

## Architecture

```
      ┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐
      │   ESP32-S3   │      │   ESP32-S3   │      │      ESP32-S3        │
      │   (Edge #1)  │      │   (Edge #2)  │      │      (Edge #N)       │
      └──────┬───────┘      └──────┬───────┘      └──────┬───────────────┘
             │                     │                      │
             └─────────────────────┴──────────────────────┘
                          MQTT (port 1883)
                          to agritwin-fog.local
                                   │
             ┌─────────────────────▼──────────────────────────────┐
             │       RASPBERRY PI ZERO 2 W  (Fog Layer)            │
             │       hostname: agritwin-fog.local                  │
             │                                                      │
             │  ┌──────────────────────────────────────────────┐  │
             │  │  Mosquitto MQTT Broker  (port 1883 / 9001)    │  │
             │  └─────────────────────┬────────────────────────┘  │
             │                        │                             │
             │  ┌─────────────────────▼────────────────────────┐  │
             │  │  MQTT Ingestion Service (paho-mqtt)           │  │
             │  └─────────────────────┬────────────────────────┘  │
             │                        │                             │
             │  ┌─────────────────────▼────────────────────────┐  │
             │  │  Preprocessing Engine (Validation + Smooth)   │  │
             │  └─────────────────────┬────────────────────────┘  │
             │                        │                             │
             │  ┌─────────────────────▼────────────────────────┐  │
             │  │  Buffer Manager (Redis hot + SQLite cold)      │  │
             │  └─────────────────────┬────────────────────────┘  │
             │                        │                             │
             │  ┌─────────────────────▼────────────────────────┐  │
             │  │  Emergency Control Service (autonomous rules)  │  │
             │  └─────────────────────┬────────────────────────┘  │
             │                        │                             │
             │  ┌─────────────────────▼────────────────────────┐  │
             │  │  Cloud Sync Service  (HTTP POST to laptop)    │  │
             │  └──────────────────────────────────────────────┘  │
             └─────────────────────────────────────────────────────┘
                          HTTP API  (port 8000)
                                   │
             ┌─────────────────────▼──────────────────────────────┐
             │       LAPTOP  (Cloud Layer)                          │
             │  FastAPI Backend  :8000  +  Next.js Dashboard :3000  │
             └─────────────────────────────────────────────────────┘
```


## Features

### 1. **Data Validation**
- Schema validation for incoming MQTT messages
- Range checking for sensor values
- Anomaly detection
- Duplicate detection

### 2. **Buffering Strategy**
- **Redis**: Hot buffer for recent data (last 1 hour)
- **SQLite**: Cold buffer for historical data (last 7 days)
- Automatic synchronization when cloud reconnects
- Configurable buffer size limits

### 3. **Emergency Control**
- Rule-based automation (e.g., automatic irrigation)
- Threshold-based triggers
- Local decision-making without cloud connectivity
- Safety limits and failsafes

### 4. **Edge Analytics**
- Data aggregation (min, max, avg)
- Downsampling for bandwidth conservation
- Statistical calculations
- Trend detection

## Tech Stack

- **Python 3.11+**
- **FastAPI**: REST API and background tasks
- **Mosquitto**: MQTT broker
- **Redis**: In-memory cache
- **SQLite**: Local database
- **Paho MQTT**: Python MQTT client
- **SQLAlchemy**: ORM
- **Pydantic**: Data validation

## Installation

### Raspberry Pi Setup (Recommended)

See the full step-by-step guide in the section
[**Running the Fog Layer on Raspberry Pi**](#running-the-fog-layer-on-raspberry-pi) below.

### Manual Setup (Development / Testing on Any Linux Machine)
```bash
cd fog

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Mosquitto
sudo apt-get install -y mosquitto mosquitto-clients

# Install Redis
sudo apt-get install -y redis-server

# Copy and edit environment variables
cp .env.example .env
nano .env            # Set CLOUD_API_URL to your laptop's IP

# Start services
mosquitto -c broker/mosquitto.conf &
redis-server &

# Run fog gateway
python main.py
```

## Configuration

Edit `config/config.yaml`:

```yaml
fog:
  farm_id: farm_001
  device_id: fog_gateway_001
  
mqtt:
  broker:
    host: 0.0.0.0
    port: 1883
  client:
    keepalive: 60
    
cloud:
  api_url: http://cloud-backend:8000
  mqtt_broker: cloud-mqtt-broker
  sync_interval: 30  # seconds
  
buffer:
  redis:
    max_size_mb: 100
  sqlite:
    max_records: 100000
    retention_days: 7
    
emergency_control:
  enabled: true
  rules:
    - name: auto_irrigation
      condition: soil_moisture < 30
      action: activate_pump
      duration: 30  # seconds
```

## API Endpoints

### Health Check
```bash
GET http://localhost:8001/health
```

### Buffer Status
```bash
GET http://localhost:8001/api/v1/buffer/status
```

### Emergency Rules
```bash
GET http://localhost:8001/api/v1/emergency/rules
POST http://localhost:8001/api/v1/emergency/rules
```

### Manual Sync
```bash
POST http://localhost:8001/api/v1/sync/trigger
```

## MQTT Topics

### Subscribed (from Edge devices)
- `farms/+/sensors/+/data`
- `farms/+/status`
- `farms/+/alerts`

### Published (to Cloud)
- `fog/{fog_id}/cloud/sensor_data`
- `fog/{fog_id}/cloud/status`

### Published (to Edge devices)
- `farms/{farm_id}/commands/+`

## Offline Mode

When cloud connectivity is lost:

1. **Buffer incoming data** in Redis/SQLite
2. **Continue emergency control** based on local rules
3. **Log all activities** for later synchronization
4. **Send alerts** to predefined local endpoints

When cloud reconnects:

1. **Sync buffered data** in chronological order
2. **Send status report** with offline duration
3. **Resume normal operation**

## Monitoring

View logs:
```bash
tail -f logs/fog_gateway.log
```

Monitor MQTT traffic:
```bash
mosquitto_sub -h localhost -t '#' -v
```

Check Redis buffer:
```bash
redis-cli
> KEYS sensor:*
> GET sensor:farm_001:soil_moisture:latest
```

## Testing

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Simulate cloud outage
python tests/simulate_outage.py
```

## Troubleshooting

### MQTT Connection Issues
```bash
# Test MQTT broker
mosquitto_sub -h localhost -p 1883 -t '#' -v

# Check broker logs
tail -f /var/log/mosquitto/mosquitto.log
```

### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

### Buffer Full
```bash
# Clear old data
python scripts/clear_buffer.py --older-than 7d
```

---

## Running the Fog Layer on Raspberry Pi

Follow these steps to deploy the fog node on a **Raspberry Pi Zero 2 W**.
When done, the Pi will be reachable as `agritwin-fog.local` on your local network
and the ESP32 devices will publish MQTT messages directly to it.

### 1. Install Raspberry Pi OS Lite

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Choose **Raspberry Pi OS Lite (64-bit)** (no desktop needed).
3. In the Imager settings (gear icon), configure:
   - Hostname → `agritwin-fog`
   - Enable SSH (password **or** public-key auth)
   - WiFi SSID and password (same network as ESP32 and laptop)
   - Username / password
4. Flash the SD card and insert into the Pi.

### 2. Enable SSH and Boot

```bash
# Find the Pi's IP (or use the mDNS hostname once Avahi is running)
ssh pi@agritwin-fog.local
# or
ssh pi@<pi-ip-address>
```

### 3. Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y

# Mosquitto MQTT broker
sudo apt install -y mosquitto mosquitto-clients

# Redis (hot buffer)
sudo apt install -y redis-server

# Avahi daemon — enables agritwin-fog.local mDNS resolution
sudo apt install -y avahi-daemon

# Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv git
```

### 4. Configure Hostname and mDNS (Avahi)

The hostname was set to `agritwin-fog` during the Imager setup.
Verify it is working by running from your **laptop**:

```bash
ping agritwin-fog.local        # should resolve and reply
```

If it does not resolve, check Avahi is running on the Pi:

```bash
sudo systemctl enable avahi-daemon
sudo systemctl start  avahi-daemon
sudo systemctl status avahi-daemon
```

### 5. Configure Mosquitto MQTT Broker

Copy the project's broker config and enable Mosquitto as a service:

```bash
# On the Raspberry Pi
sudo cp ~/agritwin/fog/broker/mosquitto.conf /etc/mosquitto/conf.d/agritwin.conf

# Restart and enable on boot
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

Verify the broker is listening:

```bash
mosquitto_sub -h localhost -t '#' -v &   # subscribe to all topics
mosquitto_pub -h localhost -t test -m hello   # publish a test message
```

### 6. Clone the Repository on the Raspberry Pi

```bash
cd ~
git clone https://github.com/Am4l-babu/S6-MINI-PROJECT.git agritwin
cd agritwin/fog
```

### 7. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 8. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Key values to set in `.env`:

```dotenv
# Point to the laptop running the cloud backend
CLOUD_API_URL=http://<laptop-ip>:8000
CLOUD_BACKEND_URL=http://<laptop-ip>:8000

# MQTT broker is local (on this Pi)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
```

> Find your laptop's IP with `ipconfig` (Windows) or `ip a` (Linux/macOS).
> Both devices must be on the same WiFi network.

### 9. Run the Fog Gateway Services

```bash
# Activate venv if not already active
source ~/agritwin/fog/venv/bin/activate

cd ~/agritwin/fog
python main.py
```

To run it as a background service that survives reboots, create a systemd unit:

```bash
sudo nano /etc/systemd/system/agritwin-fog.service
```

Paste:

```ini
[Unit]
Description=AgriTwin Fog Gateway
After=mosquitto.service redis.service network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/agritwin/fog
ExecStart=/home/pi/agritwin/fog/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/home/pi/agritwin/fog/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agritwin-fog
sudo systemctl start  agritwin-fog
sudo systemctl status agritwin-fog
```

### 10. Configure ESP32 to Connect via `agritwin-fog.local`

In [edge/include/config.h](../edge/include/config.h) the MQTT broker is already set:

```cpp
#define MQTT_BROKER "agritwin-fog.local"   // Raspberry Pi fog node (mDNS)
#define MQTT_PORT   1883
```

Re-flash the ESP32 after any config change:

```bash
cd edge
pio run --target upload
```

### 11. Verify MQTT Communication

On the Raspberry Pi, subscribe to all sensor topics:

```bash
mosquitto_sub -h localhost -t 'farms/#' -v
```

Power on (or reset) the ESP32. You should see messages like:

```
farms/farm_001/sensors/temperature/data {"value": 24.5, "unit": "C", ...}
farms/farm_001/sensors/soil_moisture/data {"value": 42.0, "unit": "%", ...}
```

From the **laptop**, you can also verify remotely:

```bash
mosquitto_sub -h agritwin-fog.local -t 'farms/#' -v
```

### 12. Forward Processed Data to the Cloud Backend on the Laptop

The fog gateway syncs buffered data automatically via the `CloudSyncService`.
You can also trigger a manual sync:

```bash
# On the Raspberry Pi
source ~/agritwin/fog/venv/bin/activate
python ~/agritwin/fog/send_to_cloud.py \
    --cloud http://<laptop-ip>:8000 \
    --db ~/agritwin/fog/data/fog_buffer.db
```

Or set the environment variable to avoid repeating the IP:

```bash
export CLOUD_BACKEND_URL=http://<laptop-ip>:8000
python ~/agritwin/fog/send_to_cloud.py
```

### Quick Health Check

| Component | Check command |
|-----------|--------------|
| Mosquitto | `sudo systemctl status mosquitto` |
| Redis | `redis-cli ping` → should return `PONG` |
| Avahi / mDNS | `ping agritwin-fog.local` (from laptop) |
| Fog gateway | `sudo systemctl status agritwin-fog` |
| Cloud reachable | `curl http://<laptop-ip>:8000/health` |
| MQTT messages | `mosquitto_sub -h localhost -t 'farms/#' -v` |

---

## License

MIT License
