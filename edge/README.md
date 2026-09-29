# Edge Layer - ESP32/ESP8266 Firmware

Industrial-grade firmware for IoT edge devices in the Smart Farming Digital Twin System.

## Features

- **Modular Sensor Architecture**: Plug-and-play sensor integration
- **Auto-Calibration**: Two-point and multi-point calibration support
- **MQTT Communication**: Reliable IoT messaging with QoS levels
- **Power Management**: Deep sleep for battery-powered deployments
- **OTA Updates**: Remote firmware updates
- **Offline Buffering**: Local storage when connectivity is lost
- **Watchdog Timer**: Auto-recovery from crashes
- **LED Status Indicators**: Visual system status

## Hardware Support

- ESP32 (recommended)
- ESP8266
- ESP32-S2
- ESP32-C3

## Supported Sensors

- Soil Moisture (Capacitive/Resistive)
- DHT22 (Temperature & Humidity)
- BMP280 (Pressure & Temperature)
- BH1750 (Light Intensity)
- pH Sensor (Analog)
- EC Sensor (Electrical Conductivity)
- Water Level Sensor
- Rain Sensor

## Quick Start

1. **Install PlatformIO**
   ```bash
   pip install platformio
   ```

2. **Configure WiFi and MQTT**
   ```bash
   cp configs/config_template.h include/config.h
   # Edit include/config.h with your credentials
   ```

3. **Build and Upload**
   ```bash
   pio run --target upload
   pio device monitor
   ```

## Configuration

Edit `include/config.h`:

```cpp
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER "agritwin-fog.local"  // Raspberry Pi fog node (mDNS)
#define MQTT_PORT 1883
#define FARM_ID "farm_001"
```

## Calibration

### Two-Point Calibration (pH Sensor)

1. Set `CALIBRATION_MODE` to `true` in config.h
2. Upload firmware
3. Place sensor in pH 4.0 buffer solution
4. Send MQTT command: `farms/farm_001/calibrate/ph/low`
5. Place sensor in pH 10.0 buffer solution
6. Send MQTT command: `farms/farm_001/calibrate/ph/high`
7. Calibration saved to EEPROM

### Load Calibration Profile

```bash
# Copy calibration file to device SPIFFS
pio run --target uploadfs
```

## MQTT Topics

### Published (Device → Cloud)

- `farms/{farm_id}/sensors/soil_moisture/data`
- `farms/{farm_id}/sensors/temperature/data`
- `farms/{farm_id}/sensors/humidity/data`
- `farms/{farm_id}/status`
- `farms/{farm_id}/diagnostics`

### Subscribed (Cloud → Device)

- `farms/{farm_id}/commands/+`
- `farms/{farm_id}/config/update`
- `farms/{farm_id}/ota/update`

## Power Management

```cpp
// Deep sleep for 5 minutes
#define DEEP_SLEEP_DURATION_SECONDS 300
```

Battery-powered mode automatically enables:
- Reduced sensor sampling frequency
- WiFi power saving
- Deep sleep between readings

## OTA Updates

### Via MQTT
```json
{
  "command": "ota_update",
  "firmware_url": "http://server.com/firmware.bin",
  "version": "1.2.0"
}
```

### Via Web Server
Access `http://<device-ip>/update` when device is in OTA mode

## Testing

```bash
# Run unit tests
pio test

# Run specific test
pio test -f test_sensor_calibration

# Test on hardware
pio test --upload-port /dev/ttyUSB0
```

## Troubleshooting

### WiFi Connection Issues
- Check SSID and password
- Ensure 2.4GHz WiFi (ESP8266 doesn't support 5GHz)
- Check signal strength (RSSI should be > -70 dBm)

### MQTT Connection Issues
- Verify broker IP and port
- Check firewall settings
- Test with MQTT Explorer

### Sensor Reading Errors
- Check wiring and power supply
- Verify I2C address (use i2c_scanner example)
- Check calibration values

## File Structure

```
edge/
├── platformio.ini          # PlatformIO configuration
├── src/
│   └── main.cpp           # Main firmware entry point
├── include/
│   ├── config.h           # User configuration
│   ├── sensors/           # Sensor interface headers
│   └── mqtt_topics.h      # Topic definitions
├── lib/
│   ├── SensorBase/        # Base sensor class
│   ├── CalibrationManager/ # Calibration logic
│   ├── MQTTManager/       # MQTT wrapper
│   └── PowerManager/      # Power management
├── test/                  # Unit tests
├── calibration_profiles/  # Pre-configured calibrations
└── configs/              # Example configurations
```

## License

MIT License - see LICENSE file
