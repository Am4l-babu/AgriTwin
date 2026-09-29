# New Sensor Module Template

This template helps you quickly add a new sensor to the edge firmware.

## Steps to Add a New Sensor

### 1. Create Sensor Header (`lib/SensorBase/NewSensor.h`)

```cpp
#ifndef NEW_SENSOR_H
#define NEW_SENSOR_H

#include "SensorBase.h"

class NewSensor : public SensorBase {
private:
    int pin;
    // Add sensor-specific fields
    
public:
    NewSensor(int analogPin);
    
    bool begin() override;
    float readRaw() override;
    float readCalibrated() override;
    
    // Add sensor-specific methods
    void calibrate(float value1, float value2);
};

#endif
```

### 2. Implement Sensor (`lib/SensorBase/NewSensor.cpp`)

```cpp
#include "NewSensor.h"

NewSensor::NewSensor(int analogPin)
    : SensorBase("new_sensor_" + String(analogPin), "new_sensor_type", "unit")
    , pin(analogPin)
{
    setRange(MIN_VALUE, MAX_VALUE);
}

bool NewSensor::begin() {
    pinMode(pin, INPUT);
    // Initialize sensor
    status = SENSOR_OK;
    return true;
}

float NewSensor::readRaw() {
    int rawValue = analogRead(pin);
    return rawValue;
}

float NewSensor::readCalibrated() {
    float rawValue = readRaw();
    
    // Convert raw to engineering units
    float calibratedValue = rawValue * CONVERSION_FACTOR;
    
    // Validate
    if (!isValueValid(calibratedValue)) {
        consecutiveErrors++;
        return lastValue;
    }
    
    // Smooth
    valueBuffer.push_back(calibratedValue);
    if (valueBuffer.size() > smoothingSamples) {
        valueBuffer.erase(valueBuffer.begin());
    }
    
    lastValue = calculateMovingAverage();
    consecutiveErrors = 0;
    updateQuality();
    
    return lastValue;
}

void NewSensor::calibrate(float value1, float value2) {
    // Implement calibration logic
    calibrated = true;
}
```

### 3. Add to Configuration (`include/config.h`)

```cpp
// Enable new sensor
#define ENABLE_NEW_SENSOR true

// Sensor pin
#define NEW_SENSOR_PIN 36

// Calibration values
#define NEW_SENSOR_CAL_OFFSET 0.0
#define NEW_SENSOR_CAL_MULTIPLIER 1.0
```

### 4. Register in Main (`src/main.cpp`)

```cpp
#include "sensors/NewSensor.h"

void setupSensors() {
    // ... existing sensors ...
    
    #ifdef ENABLE_NEW_SENSOR
    NewSensor* newSensor = new NewSensor(NEW_SENSOR_PIN);
    if (newSensor->begin()) {
        sensorManager.addSensor(newSensor);
        Log.notice(F("✓ New Sensor initialized" CR));
    } else {
        Log.error(F("✗ New Sensor failed" CR));
    }
    #endif
}
```

### 5. Update MQTT Topics (`include/mqtt_topics.h`)

```cpp
#define TOPIC_NEW_SENSOR TOPIC_SENSOR_DATA "new_sensor/data"
```

### 6. Add to Backend Schema (`cloud/backend/schemas/sensor.py`)

```python
class SensorType(str, Enum):
    SOIL_MOISTURE = "soil_moisture"
    TEMPERATURE = "temperature"
    # ... existing types ...
    NEW_SENSOR = "new_sensor"  # Add new type
```

### 7. Add to Fog Validator (`fog/src/preprocessing/validator.py`)

```python
self.sensor_ranges = {
    # ... existing sensors ...
    "new_sensor": {"min": 0.0, "max": 100.0, "unit": "unit"},
}
```

## Example: Adding a pH Sensor

See `lib/SensorBase/PHSensor.h` and `lib/SensorBase/PHSensor.cpp` for a complete example.

## Testing

1. Flash firmware to ESP32
2. Monitor serial output
3. Verify sensor readings in MQTT Explorer
4. Check data in cloud dashboard

## Documentation

Update documentation in:
- `edge/README.md`
- `docs/sensors/new_sensor.md`
- API documentation
