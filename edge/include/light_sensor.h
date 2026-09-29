"""
LightSensor - LDR or BH1750 light intensity sensor

Measures light intensity for optimal plant growth monitoring.
"""

#ifndef LIGHT_SENSOR_H
#define LIGHT_SENSOR_H

#include "sensor_base.h"
#include "calibration.h"

class LightSensor : public Sensor {
private:
    int pin;
    bool isDigital;  // true for I2C sensors like BH1750, false for LDR
    CalibrationManager* calibrationManager;
    float lastRawValue;
    
public:
    LightSensor(int analogPin, CalibrationManager* calManager,
               const String& sensorId = "light_01", bool digital = false)
        : Sensor(sensorId), pin(analogPin), isDigital(digital),
          calibrationManager(calManager), lastRawValue(0) {
    }
    
    bool begin() override {
        if (!isDigital) {
            pinMode(pin, INPUT);
            Serial.printf("[Light] Initialized (LDR) on pin %d\n", pin);
        } else {
            // TODO: Initialize I2C sensor (BH1750)
            Serial.println("[Light] WARNING: Digital mode not yet implemented");
        }
        return true;
    }
    
    float readRaw() override {
        if (isDigital) {
            // TODO: Read from I2C sensor
            lastError = "Digital light sensor not implemented";
            lastReadingValid = false;
            return NAN;
        }
        
        // Read LDR (analog)
        int raw = analogRead(pin);
        lastRawValue = static_cast<float>(raw);
        
        // Validate range
        if (raw < 0 || raw > 4095) {
            lastError = "ADC reading out of range";
            lastReadingValid = false;
            return NAN;
        }
        
        return lastRawValue;
    }
    
    float calibrate(float rawValue) override {
        if (!calibrationManager) {
            // Fallback: convert to approximate lux
            // (very rough estimate for LDR)
            float lux = map(rawValue, 0, 4095, 0, 10000);
            return lux;
        }
        
        // Use offset calibration for light sensor
        float lux = calibrationManager->calibrateOffset(
            rawValue, "light"
        );
        
        // Clamp to reasonable range
        if (lux < 0) lux = 0;
        if (lux > 100000) lux = 100000;  // Max ~100k lux
        
        return lux;
    }
    
    String getType() override {
        return "light";
    }
    
    String getId() override {
        return sensorId;
    }
    
    float getLastRaw() const {
        return lastRawValue;
    }
    
    String getLightLevel() {
        float lux = read();
        
        if (lux < 100) return "Dark";
        if (lux < 500) return "Dim";
        if (lux < 2000) return "Normal";
        if (lux < 10000) return "Bright";
        return "Very Bright";
    }
    
    void printStatus() {
        Serial.println("=== Light Sensor ===");
        Serial.printf("ID: %s\n", sensorId.c_str());
        Serial.printf("Pin: %d\n", pin);
        Serial.printf("Type: %s\n", isDigital ? "Digital (I2C)" : "Analog (LDR)");
        Serial.printf("Last Raw: %.0f ADC\n", lastRawValue);
        Serial.printf("Last Reading: %.0f lux (%s)\n", 
                     read(), getLightLevel().c_str());
        Serial.printf("Valid: %s\n", lastReadingValid ? "Yes" : "No");
        if (!lastError.isEmpty()) {
            Serial.printf("Error: %s\n", lastError.c_str());
        }
    }
};

#endif // LIGHT_SENSOR_H
