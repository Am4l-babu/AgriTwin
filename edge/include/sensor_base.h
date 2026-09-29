#ifndef SENSOR_BASE_H
#define SENSOR_BASE_H

#include <Arduino.h>
#include <ArduinoJson.h>

/**
 * @brief Abstract base class for all sensors
 * 
 * Provides common interface for:
 * - Raw sensor reading
 * - Calibration
 * - Noise filtering
 * - Smoothing (moving average)
 */
class Sensor {
public:
    virtual ~Sensor() {}
    
    /**
     * @brief Initialize the sensor
     * @return true if initialization successful
     */
    virtual bool begin() = 0;
    
    /**
     * @brief Read raw ADC value from sensor
     * @return Raw sensor value (typically 0-4095 for ESP32)
     */
    virtual float readRaw() = 0;
    
    /**
     * @brief Apply calibration to raw value
     * @param raw Raw sensor reading
     * @return Calibrated value in engineering units
     */
    virtual float calibrate(float raw) = 0;
    
    /**
     * @brief Read calibrated and filtered value
     * @return Filtered, calibrated sensor value
     */
    virtual float read() {
        float raw = readRaw();
        float calibrated = calibrate(raw);
        return applySmoothing(calibrated);
    }
    
    /**
     * @brief Get sensor type identifier
     * @return Sensor type string
     */
    virtual const char* getType() = 0;
    
    /**
     * @brief Get sensor ID
     * @return Unique sensor identifier
     */
    virtual const char* getId() = 0;
    
    /**
     * @brief Check if sensor reading is valid
     * @return true if last reading was valid
     */
    virtual bool isValid() {
        return lastReadingValid;
    }
    
    /**
     * @brief Get last error message
     * @return Error string or empty if no error
     */
    virtual String getError() {
        return lastError;
    }

protected:
    bool lastReadingValid = false;
    String lastError = "";
    
    // Smoothing buffer
    static const int SMOOTHING_WINDOW = 10;
    float smoothingBuffer[SMOOTHING_WINDOW];
    int bufferIndex = 0;
    int bufferCount = 0;
    
    /**
     * @brief Apply moving average smoothing
     * @param value Current reading
     * @return Smoothed value
     */
    float applySmoothing(float value) {
        smoothingBuffer[bufferIndex] = value;
        bufferIndex = (bufferIndex + 1) % SMOOTHING_WINDOW;
        if (bufferCount < SMOOTHING_WINDOW) bufferCount++;
        
        float sum = 0;
        for (int i = 0; i < bufferCount; i++) {
            sum += smoothingBuffer[i];
        }
        return sum / bufferCount;
    }
    
    /**
     * @brief Check if value is within expected range
     * @param value Value to check
     * @param min Minimum valid value
     * @param max Maximum valid value
     * @return true if value is valid
     */
    bool validateRange(float value, float min, float max) {
        if (isnan(value) || isinf(value)) {
            lastError = "Invalid reading (NaN or Inf)";
            lastReadingValid = false;
            return false;
        }
        
        if (value < min || value > max) {
            lastError = "Value out of range: " + String(value);
            lastReadingValid = false;
            return false;
        }
        
        lastReadingValid = true;
        lastError = "";
        return true;
    }
};

#endif // SENSOR_BASE_H
