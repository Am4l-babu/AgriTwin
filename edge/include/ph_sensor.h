"""
PHSensor - Three-point calibration for accurate pH measurement

Uses piecewise linear interpolation between three calibration points
to handle non-linear sensor response.
"""

#ifndef PH_SENSOR_H
#define PH_SENSOR_H

#include "sensor_base.h"
#include "calibration.h"

class PHSensor : public Sensor {
private:
    int pin;
    CalibrationManager* calibrationManager;
    float lastRawValue;
    float temperatureCompensation;  // For temperature-compensated pH
    
public:
    PHSensor(int analogPin, CalibrationManager* calManager,
            const String& sensorId = "ph_01")
        : Sensor(sensorId), pin(analogPin), calibrationManager(calManager),
          lastRawValue(0), temperatureCompensation(25.0) {
    }
    
    bool begin() override {
        pinMode(pin, INPUT);
        Serial.printf("[pH Sensor] Initialized on pin %d\n", pin);
        return true;
    }
    
    float readRaw() override {
        // Read analog value
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
            Serial.println("[pH] WARNING: No calibration manager!");
            // Fallback: simple linear mapping (very inaccurate!)
            return map(rawValue, 0, 4095, 0, 14);
        }
        
        // Use three-point calibration for accurate pH
        float ph = calibrationManager->calibrateThreePoint(
            rawValue, "ph"
        );
        
        // Apply temperature compensation (if available)
        // Formula: pH_compensated = pH_raw + 0.03 * (25 - temperature)
        float tempOffset = 0.03 * (25.0 - temperatureCompensation);
        ph += tempOffset;
        
        // Clamp to valid pH range (0-14)
        if (ph < 0) ph = 0;
        if (ph > 14) ph = 14;
        
        return ph;
    }
    
    String getType() override {
        return "ph";
    }
    
    String getId() override {
        return sensorId;
    }
    
    void setTemperature(float temp) {
        temperatureCompensation = temp;
    }
    
    float getLastRaw() const {
        return lastRawValue;
    }
    
    void printStatus() {
        Serial.println("=== pH Sensor ===");
        Serial.printf("ID: %s\n", sensorId.c_str());
        Serial.printf("Pin: %d\n", pin);
        Serial.printf("Last Raw: %.0f ADC\n", lastRawValue);
        Serial.printf("Last Reading: %.2f pH\n", read());
        Serial.printf("Temp Compensation: %.1f°C\n", temperatureCompensation);
        Serial.printf("Valid: %s\n", lastReadingValid ? "Yes" : "No");
        if (!lastError.isEmpty()) {
            Serial.printf("Error: %s\n", lastError.c_str());
        }
    }
};

#endif // PH_SENSOR_H
