"""
SoilMoistureSensor - Concrete implementation using CalibrationManager

Example of proper sensor abstraction with JSON calibration.
"""

#ifndef SOIL_MOISTURE_SENSOR_H
#define SOIL_MOISTURE_SENSOR_H

#include "sensor_base.h"
#include "calibration.h"

class SoilMoistureSensor : public Sensor {
private:
    int pin;
    CalibrationManager* calibrationManager;
    float lastRawValue;
    
public:
    SoilMoistureSensor(int analogPin, CalibrationManager* calManager, 
                      const String& sensorId = "soil_01")
        : Sensor(sensorId), pin(analogPin), calibrationManager(calManager), 
          lastRawValue(0) {
    }
    
    bool begin() override {
        pinMode(pin, INPUT);
        Serial.printf("[SoilMoisture] Initialized on pin %d\n", pin);
        return true;
    }
    
    float readRaw() override {
        // Read analog value (0-4095 for ESP32)
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
            // Fallback if no calibration manager
            Serial.println("[SoilMoisture] WARNING: No calibration manager!");
            return map(rawValue, 0, 4095, 0, 100);  // Simple linear mapping
        }
        
        // Use two-point calibration from JSON file
        float calibrated = calibrationManager->calibrateTwoPoint(
            rawValue, "soil_moisture"
        );
        
        // Clamp to 0-100%
        if (calibrated < 0) calibrated = 0;
        if (calibrated > 100) calibrated = 100;
        
        return calibrated;
    }
    
    String getType() override {
        return "soil_moisture";
    }
    
    String getId() override {
        return sensorId;
    }
    
    float getLastRaw() const {
        return lastRawValue;
    }
    
    void printStatus() {
        Serial.println("=== Soil Moisture Sensor ===");
        Serial.printf("ID: %s\n", sensorId.c_str());
        Serial.printf("Pin: %d\n", pin);
        Serial.printf("Last Raw: %.0f ADC\n", lastRawValue);
        Serial.printf("Last Reading: %.1f %%\n", read());
        Serial.printf("Valid: %s\n", lastReadingValid ? "Yes" : "No");
        if (!lastError.isEmpty()) {
            Serial.printf("Error: %s\n", lastError.c_str());
        }
    }
};

#endif // SOIL_MOISTURE_SENSOR_H
