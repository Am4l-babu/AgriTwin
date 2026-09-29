# Farm Deployment Template

This template helps you deploy a new farm to the Smart Farming System.

## Prerequisites

- ESP32/ESP8266 devices
- Sensors (soil moisture, temperature, etc.)
- Network connectivity (WiFi)
- MQTT broker access
- Cloud backend credentials

## Step 1: Farm Configuration

Create a farm configuration file:

**`deployments/farm_002_config.yaml`**

```yaml
farm:
  farm_id: "farm_002"
  name: "Green Valley Farm"
  location:
    latitude: 40.7128
    longitude: -74.0060
    address: "123 Farm Road, Rural County, State"
    timezone: "America/New_York"
  
  area_sqm: 5000
  crop_type: "tomato"
  planting_date: "2024-03-01"
  
  characteristics:
    soil_type: "loamy"
    irrigation_system: "drip"
    greenhouse: false
    organic: true

edge_devices:
  - device_id: "sf-edge-farm002-01"
    device_type: "ESP32"
    firmware_version: "1.0.0"
    wifi:
      ssid: "FarmNetwork"
      # Password set via environment variable
    
    sensors:
      - sensor_id: "soil_moisture_34"
        sensor_type: "soil_moisture"
        pin: 34
        calibration:
          air_value: 2950
          water_value: 1350
        reading_interval_sec: 300  # 5 minutes
      
      - sensor_id: "dht_15"
        sensor_type: "dht22"
        pin: 15
        calibration:
          temperature_offset: -0.5
          humidity_offset: 0.0
        reading_interval_sec: 600  # 10 minutes
      
      - sensor_id: "ph_35"
        sensor_type: "ph"
        pin: 35
        calibration:
          point1: {raw: 2015, actual: 4.0}
          point2: {raw: 1500, actual: 7.0}
          point3: {raw: 1010, actual: 10.0}
        reading_interval_sec: 1800  # 30 minutes
    
    actuators:
      - actuator_id: "valve_01"
        actuator_type: "irrigation_valve"
        pin: 25
        max_runtime_ms: 300000  # 5 minutes max
      
      - actuator_id: "fan_01"
        actuator_type: "ventilation_fan"
        pin: 26
        max_runtime_ms: 3600000  # 1 hour max
    
    power:
      battery_monitoring: true
      battery_adc_pin: 36
      deep_sleep_enabled: true
      sleep_duration_sec: 300  # 5 minutes

mqtt:
  broker: "fog-gateway.local"
  port: 1883
  username: "farm_002"
  # Password set via environment variable
  qos: 1

cloud:
  backend_url: "https://api.smartfarming.com"
  api_key_env: "CLOUD_API_KEY"

fog_gateway:
  gateway_id: "fog-002"
  location: "on-site"
  buffer:
    hot_buffer_hours: 1
    cold_buffer_days: 7
  
  emergency_control:
    enabled: true
    rules:
      - name: "Auto-irrigation"
        condition: "soil_moisture < 30"
        action: "activate_valve_01"
        duration_sec: 30
        cooldown_sec: 600
      
      - name: "Heat protection"
        condition: "temperature > 35"
        action: "activate_fan_01"
        duration_sec: 1800
        cooldown_sec: 300

digital_twin:
  enabled: true
  simulation_interval_sec: 300
  
  models:
    - model_type: "soil_water_balance"
      enabled: true
    
    - model_type: "evapotranspiration"
      enabled: true
      parameters:
        crop_coefficient: 1.15  # Mature tomato
    
    - model_type: "yield_prediction"
      enabled: true
      model_version: "lstm_v1"
  
  recalibration:
    divergence_threshold: 0.15
    auto_recalibrate: true

alerts:
  channels:
    - type: "email"
      recipient: "farmer@example.com"
    
    - type: "sms"
      phone: "+1234567890"
    
    - type: "dashboard"
      enabled: true
  
  rules:
    - alert_type: "low_soil_moisture"
      threshold: 25
      severity: "warning"
    
    - alert_type: "high_temperature"
      threshold: 38
      severity: "critical"
    
    - alert_type: "sensor_offline"
      duration_min: 30
      severity: "warning"

monitoring:
  health_check_interval_sec: 60
  metrics:
    - sensor_readings
    - actuator_activations
    - mqtt_messages
    - device_uptime
    - battery_level
```

## Step 2: Device Provisioning

### Flash Edge Firmware

```bash
cd edge

# Copy configuration
cp deployments/farm_002_config.yaml configs/farm_002.h

# Set secrets
export WIFI_PASSWORD="your_wifi_password"
export MQTT_PASSWORD="farm002_mqtt_password"

# Build and flash
pio run --environment esp32prod --target upload

# Monitor
pio device monitor
```

### Generate Configuration Header

```python
# scripts/generate_edge_config.py
import yaml

with open('deployments/farm_002_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Generate config.h
with open('edge/include/config.h', 'w') as f:
    f.write(f"#define FARM_ID \"{config['farm']['farm_id']}\"\n")
    f.write(f"#define DEVICE_ID \"{config['edge_devices'][0]['device_id']}\"\n")
    # ... generate all config defines
```

## Step 3: Cloud Backend Setup

### Register Farm via API

```bash
curl -X POST "https://api.smartfarming.com/api/v1/farms" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "farm_id": "farm_002",
    "name": "Green Valley Farm",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "address": "123 Farm Road"
    },
    "area_sqm": 5000,
    "crop_type": "tomato",
    "planting_date": "2024-03-01"
  }'
```

### Register Sensors

```bash
for sensor in soil_moisture_34 dht_15 ph_35; do
  curl -X POST "https://api.smartfarming.com/api/v1/farms/farm_002/sensors" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d @deployments/farm_002_sensors_$sensor.json
done
```

## Step 4: Fog Gateway Setup

### Deploy Fog Service

```bash
cd fog

# Copy configuration
cp ../deployments/farm_002_config.yaml configs/farm_002.yaml

# Set environment variables
cp .env.example .env.farm_002
# Edit .env.farm_002 with farm-specific values

# Run fog gateway
python main.py --config configs/farm_002.yaml
```

### Docker Deployment

```yaml
# docker-compose.farm_002.yml
version: '3.8'

services:
  fog-farm-002:
    build: ./fog
    container_name: fog-farm-002
    environment:
      - FARM_ID=farm_002
      - DEVICE_ID=fog-002
      - MQTT_BROKER=mqtt-broker
      - CLOUD_API_URL=https://api.smartfarming.com
    volumes:
      - ./fog/configs/farm_002.yaml:/app/config.yaml
      - fog_002_data:/app/data
    networks:
      - smart-farming-network
    restart: unless-stopped

volumes:
  fog_002_data:

networks:
  smart-farming-network:
    external: true
```

```bash
docker-compose -f docker-compose.farm_002.yml up -d
```

## Step 5: Verification

### Check Device Connectivity

```bash
# Subscribe to all farm topics
mosquitto_sub -h localhost -t 'farms/farm_002/#' -v
```

Expected output:
```
farms/farm_002/sensors/soil_moisture/data {"value":45.2,...}
farms/farm_002/status {"uptime":12345,...}
```

### Verify Cloud Sync

```bash
# Check farm status
curl -X GET "https://api.smartfarming.com/api/v1/farms/farm_002" \
  -H "Authorization: Bearer $TOKEN"

# Check recent sensor data
curl -X GET "https://api.smartfarming.com/api/v1/sensors/farm_002/soil_moisture?hours=1" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Digital Twin

```bash
# Get twin state
curl -X GET "https://api.smartfarming.com/api/v1/digital-twin/farm_002/state" \
  -H "Authorization: Bearer $TOKEN"
```

## Step 6: Dashboard Access

1. Log in to dashboard: `https://dashboard.smartfarming.com`
2. Navigate to "Farms" → "farm_002"
3. Verify sensor readings appear in real-time
4. Check digital twin visualization
5. Test actuator control

## Deployment Checklist

- [ ] Farm configuration file created
- [ ] Edge devices flashed with firmware
- [ ] Sensors installed and calibrated
- [ ] Actuators wired and tested
- [ ] WiFi connectivity verified
- [ ] MQTT connection established
- [ ] Fog gateway deployed
- [ ] Farm registered in cloud backend
- [ ] Sensors registered in database
- [ ] Digital twin enabled
- [ ] Alert rules configured
- [ ] Dashboard access verified
- [ ] Emergency control tested
- [ ] Documentation updated

## Troubleshooting

### Edge Device Not Connecting

```bash
# Check WiFi
pio device monitor  # Look for WiFi connection logs

# Check MQTT
mosquitto_sub -h <broker> -t 'farms/farm_002/#' -v -u farm_002 -P <password>

# Verify DNS
ping fog-gateway.local
```

### Sensor Data Not Appearing

1. Check sensor wiring
2. Verify calibration values
3. Monitor serial output for errors
4. Check MQTT topic subscriptions
5. Verify fog gateway is running

### Fog Gateway Not Syncing

```bash
# Check fog logs
docker logs fog-farm-002

# Check cloud connectivity
curl -I https://api.smartfarming.com/health

# Manually trigger sync
curl -X POST "http://localhost:8001/api/sync/trigger"
```

## Scaling

### Adding More Farms

1. Copy `farm_002_config.yaml` → `farm_003_config.yaml`
2. Update farm_id and device_ids
3. Repeat deployment steps
4. Each farm can have its own fog gateway or share

### Multi-Device Farms

For large farms with multiple edge devices:

```yaml
edge_devices:
  - device_id: "sf-edge-farm002-01"
    zone: "zone_a"
    # ... sensors for zone A
  
  - device_id: "sf-edge-farm002-02"
    zone: "zone_b"
    # ... sensors for zone B
```

## Maintenance

### OTA Firmware Updates

```bash
# Trigger OTA update
mosquitto_pub -h localhost -t 'farms/farm_002/commands/ota_update' \
  -m '{"firmware_url":"http://server/firmware_v1.1.bin","version":"1.1.0"}'
```

### Backup Configuration

```bash
# Backup farm config
cp deployments/farm_002_config.yaml backups/farm_002_$(date +%Y%m%d).yaml

# Export farm data from cloud
curl -X GET "https://api.smartfarming.com/api/v1/farms/farm_002/export" \
  -H "Authorization: Bearer $TOKEN" \
  -o backups/farm_002_data_$(date +%Y%m%d).json
```

## Support

For deployment assistance, contact: support@smartfarming.com
