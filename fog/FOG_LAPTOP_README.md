# ⚠️ DEPRECATED — Fog Layer on Laptop (Old Architecture)

> **This document describes the old architecture where the fog layer ran on the laptop.**
> **It is kept for historical reference only.**
>
> **Current architecture:** The fog layer now runs on a **Raspberry Pi Zero 2 W**
> (`agritwin-fog.local`). The laptop only runs the cloud layer.
>
> Please refer to [fog/README.md](README.md) for up-to-date Raspberry Pi setup instructions.

---

# Fog Layer - Running on Your Laptop

## Overview

Your **laptop** acts as the **Fog Layer** - the critical bridge between edge devices and cloud services.

### Why Fog Layer on Laptop?

The fog layer provides:

- ✅ **Local MQTT broker** (Mosquitto)
- ✅ **Data preprocessing** and validation
- ✅ **Digital Twin** execution
- ✅ **Local database** (InfluxDB + PostgreSQL)
- ✅ **Emergency control** (works even if internet fails)
- ✅ **Offline buffering** (stores data when cloud is down)
- ✅ **Dashboard server** (real-time visualization)

## 🔥 Why This is Important

### If Internet Dies:
- ✅ System still works
- ✅ Laptop buffers data
- ✅ Emergency threshold control activates
- ✅ Local decisions continue

### If Cloud AI Crashes:
- ✅ Local fallback logic remains active
- ✅ Digital twin keeps running
- ✅ Irrigation continues based on rules

**This is industrial thinking!** 💡

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  LAPTOP (Fog Layer)                  │
├──────────────┬─────────────┬────────────────────────┤
│ MQTT Broker  │ Ingestion   │ Preprocessing          │
│ (Mosquitto)  │ MQTT Listen │ Validation + Smoothing │
├──────────────┼─────────────┼────────────────────────┤
│ Buffer Mgr   │ Emergency   │ Digital Twin           │
│ Redis+SQLite │ Threshold   │ Physics + AI + Optim   │
├──────────────┴─────────────┴────────────────────────┤
│ Local DB: InfluxDB (time-series) + PostgreSQL       │
└──────────────────────────────────────────────────────┘
           ↕                           ↕
      ESP32-S3 Sense              Cloud Backend
```

## Installation on Laptop

### 1. Install Prerequisites

**macOS:**
```bash
brew install mosquitto
brew install influxdb
brew install postgresql@15
brew install redis
brew install python@3.11
brew install node
```

**Ubuntu/Debian:**
```bash
sudo apt install mosquitto mosquitto-clients
sudo apt install influxdb influxdb-client
sudo apt install postgresql postgresql-contrib
sudo apt install redis-server
sudo apt install python3.11 python3-pip
sudo apt install nodejs npm
```

**Windows:**
```powershell
choco install mosquitto
choco install influxdb
choco install postgresql15
choco install redis
choco install python311
choco install nodejs
```

### 2. Start Services

```bash
# MQTT Broker
mosquitto -c fog/broker/mosquitto.conf

# InfluxDB
influxd

# PostgreSQL
pg_ctl -D /usr/local/var/postgres start

# Redis
redis-server
```

### 3. Install Python Dependencies

```bash
cd fog
pip install -r requirements.txt
```

### 4. Start Fog Gateway

```bash
python main.py
```

## Folder Structure

```
fog/
├── broker/
│   └── mosquitto.conf              # MQTT broker configuration
├── ingestion/
│   ├── mqtt_listener.py            # Subscribe to sensor data
│   └── data_pipeline.py            # Process incoming messages
├── preprocessing/
│   ├── validator.py                # Validate sensor ranges
│   └── smoother.py                 # Additional smoothing
├── emergency_control/
│   ├── threshold_logic.py          # Auto-irrigation rules
│   └── actuator_commands.py        # Send commands to ESP32
├── buffer_manager/
│   ├── offline_buffer.py           # SQLite fallback storage
│   └── redis_cache.py              # Hot data cache
├── digital_twin/
│   ├── twin_state_manager.py       # State synchronization
│   ├── physics_model/
│   │   ├── evapotranspiration.py   # ET0 calculation
│   │   └── water_balance.py        # Soil water model
│   ├── growth_model/
│   │   └── plant_growth.py         # GDD and biomass
│   ├── ai_engine/
│   │   └── prediction_model.py     # LSTM yield prediction
│   ├── optimization_engine/
│   │   └── irrigation_optimizer.py # Linear programming
│   └── decision_engine/
│       └── actuator_decision.py    # Decide when to irrigate
├── config/
│   └── settings.yaml               # Configuration
├── logs/
│   └── fog.log                     # Application logs
├── main.py                         # Entry point
└── requirements.txt
```

## Data Flow

### 1. ESP32-S3 Publishes Sensor Data

```json
{
  "farm_id": "farm_01",
  "soil_moisture": 32.5,
  "temperature": 29.3,
  "humidity": 68.2,
  "light": 540,
  "timestamp": 1708075200
}
```

### 2. MQTT Listener Receives

```python
# fog/ingestion/mqtt_listener.py
@mqtt_client.on_message()
async def on_message(topic, payload):
    data = json.loads(payload)
    
    # Validate
    if validator.validate(data):
        # Store in InfluxDB
        await influx_client.write_point(data)
        
        # Update digital twin
        await twin_manager.update_physical_state(data)
        
        # Check emergency conditions
        await emergency_controller.evaluate(data)
```

### 3. Digital Twin Simulation Runs

```python
# Every 5 minutes
twin_state = twin_manager.get_state()

# Run physics simulation
et0 = evapotranspiration.calculate(weather_data)
predicted_moisture = water_balance.simulate(current_moisture, et0)

# Update virtual state
twin_manager.update_virtual_state({
    "soil_moisture": predicted_moisture
})

# Check divergence
divergence = twin_manager.calculate_divergence()
if divergence > 0.15:
    twin_manager.recalibrate()
```

### 4. Optimizer Decides

```python
# fog/digital_twin/decision_engine/actuator_decision.py
decision = optimizer.optimize_irrigation(
    current_moisture=32.5,
    predicted_et0=5.2,
    forecast=[{"temp": 30, "rain": 0}],
    constraints={"min_moisture": 40, "max_water": 100}
)

if decision["action"] == "irrigate":
    # Publish command to ESP32
    mqtt_client.publish(
        "farms/farm_01/commands/irrigation",
        {"action": "activate", "duration_sec": 30}
    )
```

### 5. ESP32 Executes

Edge device receives command and activates irrigation valve.

## Emergency Control

### Autonomous Rules (No Cloud Required)

```python
# fog/emergency_control/threshold_logic.py
class EmergencyController:
    def __init__(self):
        self.rules = [
            {
                "name": "Auto-irrigation",
                "condition": lambda data: data['soil_moisture'] < 30,
                "action": "activate_valve_01",
                "duration_sec": 30,
                "cooldown_sec": 600
            },
            {
                "name": "Heat protection",
                "condition": lambda data: data['temperature'] > 35,
                "action": "activate_fan_01",
                "duration_sec": 1800,
                "cooldown_sec": 300
            }
        ]
    
    async def evaluate(self, sensor_data):
        for rule in self.rules:
            if rule['condition'](sensor_data):
                if self.can_activate(rule):
                    await self.execute_action(rule)
```

**Example:**
- Soil moisture drops below 30% → Auto-irrigate for 30 seconds
- Temperature exceeds 35°C → Turn on fan for 30 minutes
- No internet required!

## Offline Buffering

### Strategy

1. **Hot Buffer (Redis):** Last 1 hour of data
2. **Cold Buffer (SQLite):** Last 7 days when cloud is offline

```python
# fog/buffer_manager/offline_buffer.py
class BufferManager:
    async def store(self, data):
        # Always store in Redis (hot cache)
        await redis_client.setex(
            f"sensor:{data['timestamp']}", 
            3600,  # 1 hour TTL
            json.dumps(data)
        )
        
        # If cloud is down, store in SQLite
        if not cloud_client.is_healthy():
            await sqlite_db.insert('offline_buffer', data)
    
    async def sync_to_cloud(self):
        # When cloud comes back online
        buffered_data = await sqlite_db.query('offline_buffer')
        await cloud_client.bulk_upload(buffered_data)
        await sqlite_db.clear('offline_buffer')
```

## Configuration

### `fog/config/settings.yaml`

```yaml
farm:
  farm_id: "farm_001"
  device_id: "fog_001"

mqtt:
  broker: "localhost"
  port: 1883
  qos: 1

influxdb:
  url: "http://localhost:8086"
  token: "your-token"
  org: "smart-farming"
  bucket: "sensor-data"

postgresql:
  host: "localhost"
  port: 5432
  database: "smart_farming"
  user: "postgres"
  password: "your-password"

redis:
  host: "localhost"
  port: 6379
  db: 0

cloud:
  backend_url: "https://api.smartfarming.com"
  api_key: "your-api-key"
  sync_interval_sec: 30

emergency_control:
  enabled: true
  irrigation_threshold: 30
  temperature_alert: 35

digital_twin:
  simulation_interval_sec: 300
  enable_physics: true
  enable_ai: true
  enable_optimization: true

logging:
  level: "INFO"
  file: "logs/fog.log"
```

## Dashboard

### Option 1: React + WebSocket (Real-time)

```bash
cd fog/dashboard
npm install
npm run dev
```

Features:
- Real-time sensor graphs
- Digital twin visualization
- Predicted moisture curve
- Recommended irrigation window

### Option 2: Grafana (Quick Setup)

```bash
# Start Grafana
grafana-server --config=/usr/local/etc/grafana/grafana.ini

# Access: http://localhost:3000
# Add InfluxDB datasource
# Import dashboard from fog/grafana/dashboard.json
```

## Monitoring

### Health Checks

```bash
# Check fog gateway status
curl http://localhost:8001/health

# Response:
{
  "status": "healthy",
  "services": {
    "mqtt": "connected",
    "influxdb": "connected",
    "postgresql": "connected",
    "redis": "connected",
    "cloud": "connected"
  },
  "last_sensor_reading": "2026-02-16T10:30:00Z",
  "twin_divergence": 0.08
}
```

### Logs

```bash
# Follow logs
tail -f fog/logs/fog.log

# Search for errors
grep ERROR fog/logs/fog.log
```

## Testing

### Simulate Sensor Data

```bash
# Publish test message
mosquitto_pub -h localhost -t 'farms/farm_001/sensors/soil_moisture/data' \
  -m '{"farm_id":"farm_001","soil_moisture":32.5,"timestamp":1708075200}'
```

### Test Emergency Control

```bash
# Trigger low moisture alert
mosquitto_pub -h localhost -t 'farms/farm_001/sensors/soil_moisture/data' \
  -m '{"farm_id":"farm_001","soil_moisture":25.0,"timestamp":1708075200}'

# Check if irrigation command sent
mosquitto_sub -h localhost -t 'farms/farm_001/commands/#' -v
```

## Performance

**Laptop Specs:**
- CPU: Modern i5/i7 or M1/M2
- RAM: 8 GB minimum, 16 GB recommended
- Storage: 50 GB free (for local database)

**Expected Load:**
- 10 farms × 5 sensors × 12 readings/hour = 600 messages/hour
- InfluxDB: ~1 MB/day per farm
- Digital twin simulation: ~5% CPU usage
- Dashboard: ~10% CPU when active

## Troubleshooting

### MQTT not receiving messages
```bash
# Check broker status
systemctl status mosquitto

# Test subscription
mosquitto_sub -h localhost -t '#' -v

# Check ESP32 connection
pio device monitor  # Should show MQTT connect logs
```

### InfluxDB not storing data
```bash
# Check InfluxDB service
influx ping

# Verify bucket exists
influx bucket list

# Check write permissions
influx auth list
```

### Digital twin not updating
```bash
# Check fog gateway logs
tail -f fog/logs/fog.log | grep "twin"

# Manual trigger
curl -X POST http://localhost:8001/api/twin/simulate
```

## Next Steps

1. ✅ Install all services on laptop
2. ✅ Start MQTT broker
3. ✅ Configure `settings.yaml`
4. ✅ Start fog gateway
5. ✅ Connect ESP32-S3 Sense
6. ✅ Monitor dashboard
7. 🚀 Deploy to production (move to cloud server)

---

**Your laptop is now a powerful industrial control system!** 💻⚡
