# Edge Layer - ESP32-S3 Sense

## Overview

This is the **Edge Layer** of the Smart Farming Digital Twin System, designed specifically for **ESP32-S3 Sense** development boards.

### Why ESP32-S3 Sense?

The ESP32-S3 Sense is powerful and provides:

- **WiFi + Bluetooth** connectivity
- **MQTT** communication
- **Basic filtering** and edge processing
- **TinyML** support for on-device machine learning
- **Camera module** (OV2640) for future plant disease detection 👀
- **2 MB PSRAM** for complex operations
- **Dual-core** CPU for parallel processing

## Features

✅ **Sensor Abstraction Layer** - Clean class-based design  
✅ **JSON-based Calibration** - No hardcoded values  
✅ **Noise Filtering** - Moving average smoothing  
✅ **MQTT Communication** - QoS 1 with reconnection  
✅ **OTA Updates** - Wireless firmware updates  
✅ **Power Management** - Deep sleep support  
✅ **TinyML Ready** - Camera + inference capability  

## Project Structure

```
edge/
├── platformio.ini                 # PlatformIO configuration (ESP32-S3 Sense)
├── include/
│   ├── config.h                   # Main configuration
│   ├── sensor_base.h              # Abstract sensor class
│   ├── calibration.h              # Calibration manager
│   └── mqtt_topics.h              # MQTT topic definitions
├── src/
│   ├── main.cpp                   # Main firmware
│   ├── mqtt_manager.cpp           # MQTT connection & publishing
│   ├── sensor_manager.cpp         # Sensor reading orchestration
│   └── calibration.cpp            # Calibration implementation
├── lib/
│   └── SensorBase/                # Sensor implementations
│       ├── SoilMoistureSensor.*
│       ├── DHTSensor.*
│       ├── PHSensor.*
│       └── LightSensor.*
├── calibration_profiles/          # JSON calibration files
│   ├── soil_calibration.json      # Dry/wet values
│   ├── ph_calibration.json        # 3-point calibration
│   └── temperature_calibration.json
├── test/                          # Unit tests
└── data/                          # SPIFFS filesystem
```

## Sensor Abstraction Design

### ✨ No Spaghetti Code!

Instead of reading sensors directly in `main.cpp`, we use **abstraction**:

```cpp
class Sensor {
public:
    virtual float readRaw() = 0;      // Read ADC
    virtual float calibrate(float raw) = 0;  // Apply calibration
    virtual float read() {             // Read + calibrate + smooth
        float raw = readRaw();
        float calibrated = calibrate(raw);
        return applySmoothing(calibrated);
    }
};
```

### Sensor Implementations

Each sensor class implements:

1. **Noise filtering** - Moving average with configurable window
2. **Offset correction** - From calibration profiles
3. **Smoothing** - Reduces jitter in readings
4. **Validation** - Range checking and error detection

**Supported Sensors:**

- `SoilMoistureSensor` - Capacitive soil moisture (two-point calibration)
- `DHTSensor` - Temperature + Humidity (offset calibration)
- `PHSensor` - pH probe (three-point polynomial calibration)
- `LightSensor` - Light intensity (lux conversion)

## Calibration Strategy

### 🔬 Most student projects fail here!

**Never hardcode calibration values.**

### Soil Moisture Example

1. **Measure dry soil value** (sensor in air):
   ```
   Raw ADC = 3200
   ```

2. **Measure wet soil value** (sensor in water):
   ```
   Raw ADC = 1200
   ```

3. **Store in `calibration_profiles/soil_calibration.json`:**
   ```json
   {
     "dry_value": 3200,
     "wet_value": 1200
   }
   ```

4. **Firmware automatically converts** raw ADC to percentage:
   ```cpp
   percentage = ((raw - dry) / (wet - dry)) * 100
   ```

### pH Sensor (3-Point Calibration)

```json
{
  "point1": {"raw": 2015, "actual": 4.0},
  "point2": {"raw": 1500, "actual": 7.0},
  "point3": {"raw": 1010, "actual": 10.0}
}
```

Firmware applies **piecewise linear interpolation** or polynomial fit.

## Getting Started

### 1. Install PlatformIO

```bash
# VS Code Extension (recommended)
# OR
pip install platformio
```

### 2. Configure Your Farm

Edit `include/config.h`:

```cpp
#define FARM_ID "farm_001"
#define DEVICE_ID "esp32s3_001"
#define WIFI_SSID "YourWiFi"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER "agritwin-fog.local"  // Raspberry Pi fog node (mDNS)
```

### 3. Upload Calibration Files

```bash
# Upload SPIFFS filesystem with calibration profiles
pio run --target uploadfs
```

### 4. Build & Flash

```bash
# Build firmware
pio run --environment esp32s3

# Flash to device
pio run --environment esp32s3 --target upload

# Monitor serial output
pio device monitor
```

## ESP32-S3 Sense Pinout

### Default Pin Configuration

```cpp
// Sensors
#define SOIL_MOISTURE_PIN 1    // ADC1_CH0
#define DHT_PIN 2              // GPIO2
#define PH_SENSOR_PIN 3        // ADC1_CH2
#define LIGHT_SENSOR_PIN 4     // ADC1_CH3

// Actuators
#define IRRIGATION_VALVE_PIN 5  // GPIO5
#define FAN_PIN 6              // GPIO6

// Camera (built-in on ESP32-S3 Sense)
#define CAMERA_ENABLED true
```

### Camera Module (Future: Plant Disease Detection)

The ESP32-S3 Sense has an **OV2640 camera** that can be used for:

- 📸 Plant health monitoring
- 🦠 Disease detection (using TinyML)
- 🍃 Growth tracking
- 🐛 Pest identification

**Example TinyML Integration:**

```cpp
#include <EloquentTinyML.h>
#include <eloquent_tinyml/tensorflow.h>

// Load plant disease model
Eloquent::TinyML::TensorFlow::TensorFlow<NUMBER_OF_INPUTS, 
                                          NUMBER_OF_OUTPUTS, 
                                          TENSOR_ARENA_SIZE> ml;

void detectPlantDisease() {
    camera.capture();
    float* input = preprocessImage(camera.getFramebuffer());
    float* output = ml.predict(input);
    
    if (output[0] > 0.8) {
        Serial.println("⚠ Disease detected!");
        publishAlert("disease_detected");
    }
}
```

## MQTT Topics

### Publishing (Edge → Fog)

```
farms/{farm_id}/sensors/soil_moisture/data
farms/{farm_id}/sensors/temperature/data
farms/{farm_id}/sensors/humidity/data
farms/{farm_id}/status
```

### Subscribing (Fog → Edge)

```
farms/{farm_id}/commands/irrigation
farms/{farm_id}/commands/ota_update
farms/{farm_id}/commands/calibrate
```

## Data Flow

```
1. ESP32-S3 reads sensors (every 5 minutes)
   ↓
2. Apply calibration (from JSON profiles)
   ↓
3. Apply smoothing (moving average)
   ↓
4. Publish MQTT JSON:
   {
     "farm_id": "farm_01",
     "soil_moisture": 32.5,
     "temperature": 29.3,
     "humidity": 68.2,
     "light": 540
   }
   ↓
5. Raspberry Pi (Fog) receives and processes
   ↓
6. Digital Twin updates
   ↓
7. Decision sent back via MQTT
   ↓
8. ESP32-S3 executes (e.g., activate irrigation)
```

This is a **real feedback cyber loop**! 🔄

## Power Management

For battery-powered deployments:

```cpp
// Deep sleep between readings
esp_sleep_enable_timer_wakeup(SLEEP_DURATION_SEC * 1000000ULL);
esp_deep_sleep_start();
```

**Typical power consumption:**
- Active (WiFi + sensors): ~160 mA
- Deep sleep: ~10 µA
- Battery life (2500 mAh): ~3-6 months with 5-min intervals

## OTA Updates

```bash
# Trigger OTA via MQTT
mosquitto_pub -h localhost -t 'farms/farm_001/commands/ota_update' \
  -m '{"firmware_url":"http://192.168.1.100/firmware_v1.1.bin"}'
```

Firmware automatically:
1. Downloads new binary
2. Verifies checksum
3. Flashes OTA partition
4. Reboots

## Testing

```bash
# Run unit tests (native environment)
pio test --environment native

# Run on-device tests
pio test --environment esp32s3
```

## Troubleshooting

### Sensor readings are noisy
- ✅ Check wiring (use twisted pair for long cables)
- ✅ Increase smoothing window in `sensor_base.h`
- ✅ Add hardware filtering (capacitor)

### MQTT not connecting
- ✅ Check WiFi credentials
- ✅ Verify broker IP address
- ✅ Check firewall settings on laptop
- ✅ Monitor serial output: `pio device monitor`

### Calibration not loading
- ✅ Upload SPIFFS: `pio run --target uploadfs`
- ✅ Check file exists: `SPIFFS.exists("/calibration/soil_calibration.json")`
- ✅ Verify JSON syntax

## Next Steps

1. ✅ Flash firmware to ESP32-S3 Sense
2. ✅ Upload calibration profiles
3. ✅ Connect sensors
4. ✅ Start Fog layer on Raspberry Pi (see `fog/README.md`)
5. ✅ Monitor real-time data in dashboard
6. 🔬 Train TinyML model for camera-based disease detection
7. 🚀 Deploy to field!

## Resources

- [ESP32-S3 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- [PlatformIO Docs](https://docs.platformio.org/)
- [TinyML for ESP32](https://eloquentarduino.github.io/2020/08/eloquent-tinyml-tensorflow/)
- [MQTT Best Practices](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/)

---

**This edge layer prevents spaghetti firmware and enables industrial-grade reliability.** 🎯
