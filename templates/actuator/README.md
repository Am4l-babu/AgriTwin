# Actuator Module Template

This template helps you add actuator control to the edge firmware.

## Supported Actuator Types

- **Irrigation valves** (solenoid, servo)
- **Water pumps** (DC, relay-controlled)
- **Ventilation fans**
- **Shade cloth motors**
- **LED grow lights**

## Step 1: Create Actuator Class (`lib/ActuatorBase/YourActuator.h`)

```cpp
#ifndef YOUR_ACTUATOR_H
#define YOUR_ACTUATOR_H

#include "ActuatorBase.h"

class YourActuator : public ActuatorBase {
private:
    int controlPin;
    bool isActive;
    unsigned long activationTime;
    
public:
    YourActuator(int pin, String id);
    
    bool begin() override;
    bool activate(uint32_t duration_ms = 0) override;
    bool deactivate() override;
    bool isRunning() override;
    String getStatus() override;
};

#endif
```

## Step 2: Implement Actuator (`lib/ActuatorBase/YourActuator.cpp`)

```cpp
#include "YourActuator.h"

YourActuator::YourActuator(int pin, String id)
    : ActuatorBase(id, "your_actuator_type")
    , controlPin(pin)
    , isActive(false)
    , activationTime(0)
{
}

bool YourActuator::begin() {
    pinMode(controlPin, OUTPUT);
    digitalWrite(controlPin, LOW);  // Default off
    
    Log.notice(F("✓ Actuator %s initialized on pin %d" CR), actuatorId.c_str(), controlPin);
    return true;
}

bool YourActuator::activate(uint32_t duration_ms) {
    if (isActive) {
        Log.warning(F("Actuator %s already active" CR), actuatorId.c_str());
        return false;
    }
    
    digitalWrite(controlPin, HIGH);
    isActive = true;
    activationTime = millis();
    
    if (duration_ms > 0) {
        // Schedule automatic deactivation
        scheduledStopTime = millis() + duration_ms;
    }
    
    Log.notice(F("✓ Actuator %s activated for %d ms" CR), actuatorId.c_str(), duration_ms);
    
    // Publish status to MQTT
    publishStatus();
    
    return true;
}

bool YourActuator::deactivate() {
    if (!isActive) {
        return true;  // Already off
    }
    
    digitalWrite(controlPin, LOW);
    isActive = false;
    
    uint32_t runDuration = millis() - activationTime;
    Log.notice(F("✓ Actuator %s deactivated after %d ms" CR), actuatorId.c_str(), runDuration);
    
    publishStatus();
    
    return true;
}

bool YourActuator::isRunning() {
    // Check if scheduled stop time has passed
    if (isActive && scheduledStopTime > 0 && millis() >= scheduledStopTime) {
        deactivate();
    }
    
    return isActive;
}

String YourActuator::getStatus() {
    JsonDocument doc;
    doc["actuator_id"] = actuatorId;
    doc["type"] = actuatorType;
    doc["active"] = isActive;
    doc["pin"] = controlPin;
    
    if (isActive) {
        doc["runtime_ms"] = millis() - activationTime;
    }
    
    String status;
    serializeJson(doc, status);
    return status;
}
```

## Step 3: Register Actuator in Main (`src/main.cpp`)

```cpp
#include "actuators/YourActuator.h"

YourActuator* myActuator;

void setupActuators() {
    #ifdef ENABLE_YOUR_ACTUATOR
    myActuator = new YourActuator(YOUR_ACTUATOR_PIN, "actuator_01");
    if (myActuator->begin()) {
        actuatorManager.addActuator(myActuator);
    }
    #endif
}

void loop() {
    // Check for scheduled stops
    actuatorManager.update();
    
    // Handle MQTT commands
    // (implemented in MQTT callback)
}
```

## Step 4: MQTT Command Handling

### Subscribe to Command Topic

```cpp
void setupMQTT() {
    // ... existing code ...
    
    // Subscribe to actuator commands
    String commandTopic = String(TOPIC_COMMANDS) + "#";
    mqttClient.subscribe(commandTopic.c_str());
}
```

### Handle Commands

```cpp
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String topicStr = String(topic);
    
    // Parse JSON payload
    JsonDocument doc;
    deserializeJson(doc, payload, length);
    
    // Check if it's an actuator command
    if (topicStr.indexOf("/commands/") > 0) {
        String command = doc["command"];
        String actuatorId = doc["actuator_id"];
        
        if (command == "activate") {
            uint32_t duration = doc["duration_ms"] | 0;
            
            if (actuatorId == "actuator_01") {
                myActuator->activate(duration);
            }
        }
        else if (command == "deactivate") {
            if (actuatorId == "actuator_01") {
                myActuator->deactivate();
            }
        }
    }
}
```

## Example: Irrigation Valve

### Hardware Connection

```
ESP32 Pin 25 → Relay IN
Relay COM → 12V Power Supply +
Relay NO → Solenoid Valve +
Solenoid Valve - → Power Supply -
```

### Configuration

```cpp
#define ENABLE_IRRIGATION_VALVE true
#define IRRIGATION_VALVE_PIN 25
#define IRRIGATION_DEFAULT_DURATION_MS 30000  // 30 seconds
```

### Implementation

```cpp
// lib/ActuatorBase/IrrigationValve.h
class IrrigationValve : public ActuatorBase {
private:
    int relayPin;
    uint32_t totalWaterDelivered_ml;  // Track usage
    
public:
    IrrigationValve(int pin);
    
    bool activate(uint32_t duration_ms) override;
    uint32_t getTotalWaterDelivered();
    void resetWaterCounter();
};
```

## Safety Features

### Hardware Interlock

```cpp
bool YourActuator::activate(uint32_t duration_ms) {
    // Check safety conditions
    if (batteryVoltage < MIN_SAFE_VOLTAGE) {
        Log.error(F("Cannot activate: Low battery" CR));
        return false;
    }
    
    // Maximum runtime protection
    if (duration_ms > MAX_RUNTIME_MS) {
        duration_ms = MAX_RUNTIME_MS;
        Log.warning(F("Duration capped at %d ms" CR), MAX_RUNTIME_MS);
    }
    
    // Proceed with activation
    // ...
}
```

### Watchdog Timer

```cpp
void loop() {
    actuatorManager.update();
    
    // Emergency shutdown if no MQTT heartbeat
    if (millis() - lastMqttHeartbeat > MQTT_TIMEOUT_MS) {
        actuatorManager.deactivateAll();
        Log.error(F("MQTT timeout - all actuators stopped" CR));
    }
}
```

### Manual Override

```cpp
#define MANUAL_OVERRIDE_BUTTON 0  // GPIO0 (BOOT button)

void loop() {
    if (digitalRead(MANUAL_OVERRIDE_BUTTON) == LOW) {
        // Manual stop all actuators
        actuatorManager.deactivateAll();
        Log.notice(F("Manual override activated" CR));
    }
}
```

## Testing Actuators

### Unit Test

```cpp
// test/test_actuator.cpp
#include <unity.h>
#include <IrrigationValve.h>

void test_activate_deactivate() {
    IrrigationValve valve(25);
    valve.begin();
    
    TEST_ASSERT_FALSE(valve.isRunning());
    
    valve.activate(1000);
    TEST_ASSERT_TRUE(valve.isRunning());
    
    delay(1100);
    valve.isRunning();  // Should auto-stop
    TEST_ASSERT_FALSE(valve.isRunning());
}
```

### MQTT Test Command

```bash
mosquitto_pub -h localhost -t 'farms/farm_001/commands/irrigation' \
  -m '{"command":"activate","actuator_id":"valve_01","duration_ms":30000}'
```

## Cloud Integration

### Backend API Endpoint

```python
# cloud/backend/api/v1/actuators.py
@router.post("/farms/{farm_id}/actuators/activate")
async def activate_actuator(
    farm_id: str,
    actuator_id: str,
    duration_seconds: int
):
    """Send activation command to actuator via MQTT."""
    
    # Publish MQTT command
    mqtt_client.publish(
        f"farms/{farm_id}/commands/irrigation",
        {
            "command": "activate",
            "actuator_id": actuator_id,
            "duration_ms": duration_seconds * 1000
        }
    )
    
    return {"status": "command_sent"}
```

### Fog Layer Emergency Control

```python
# fog/src/emergency_control/controller.py
async def evaluate_emergency_action(self, sensor_data):
    """Automatic actuation based on rules."""
    
    if sensor_data['sensor_type'] == 'soil_moisture':
        if sensor_data['value'] < self.config.irrigation_threshold:
            # Auto-activate irrigation
            await self.activate_actuator(
                farm_id=sensor_data['farm_id'],
                actuator_id='valve_01',
                duration_ms=30000
            )
```

## Scheduling

### Cron-like Scheduling

```cpp
#include <TaskScheduler.h>

Scheduler scheduler;

void irrigationCallback() {
    myActuator->activate(IRRIGATION_DEFAULT_DURATION_MS);
}

// Schedule irrigation at 6:00 AM daily
Task irrigationTask(6 * 3600 * 1000, TASK_FOREVER, &irrigationCallback);

void setup() {
    scheduler.addTask(irrigationTask);
    irrigationTask.enable();
}

void loop() {
    scheduler.execute();
}
```

## Monitoring and Logging

```cpp
void publishActuatorLog() {
    JsonDocument doc;
    doc["farm_id"] = FARM_ID;
    doc["actuator_id"] = myActuator->getId();
    doc["activations_today"] = activationCount;
    doc["total_runtime_ms"] = totalRuntime;
    
    String payload;
    serializeJson(doc, payload);
    
    mqttClient.publish(TOPIC_ACTUATOR_LOG, payload.c_str());
}
```

## Documentation

- Update `edge/README.md` with new actuator
- Add wiring diagram
- Document safety requirements
- Include calibration procedures (if applicable)
