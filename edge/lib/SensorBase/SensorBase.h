/**
 * @file SensorBase.h
 * @brief Base class for all sensor implementations
 * 
 * Provides a common interface for sensor management with:
 * - Calibration support
 * - Data smoothing and filtering
 * - Error handling
 * - Quality metrics
 */

#ifndef SENSOR_BASE_H
#define SENSOR_BASE_H

#include <Arduino.h>
#include <vector>

enum SensorStatus {
    SENSOR_OK,
    SENSOR_ERROR,
    SENSOR_NOT_INITIALIZED,
    SENSOR_CALIBRATION_NEEDED,
    SENSOR_OUT_OF_RANGE
};

enum SensorQuality {
    QUALITY_EXCELLENT,
    QUALITY_GOOD,
    QUALITY_FAIR,
    QUALITY_POOR,
    QUALITY_UNKNOWN
};

class SensorBase {
protected:
    String sensorId;
    String sensorType;
    String unit;
    
    float lastValue;
    float minValue;
    float maxValue;
    
    SensorStatus status;
    SensorQuality quality;
    
    // Calibration parameters
    float calibrationOffset;
    float calibrationMultiplier;
    bool calibrated;
    
    // Smoothing buffer
    std::vector<float> valueBuffer;
    int smoothingSamples;
    
    // Error tracking
    int consecutiveErrors;
    unsigned long lastReadTime;
    
    // Moving average calculation
    float calculateMovingAverage();
    
    // Outlier detection
    bool isOutlier(float value);
    
    // Apply calibration
    float applyCalibration(float rawValue);
    
public:
    SensorBase(String id, String type, String unit);
    virtual ~SensorBase() {}
    
    // Pure virtual methods (must be implemented by derived classes)
    virtual bool begin() = 0;
    virtual float readRaw() = 0;
    virtual float readCalibrated() = 0;
    
    // Common methods
    virtual void calibrate(float offset, float multiplier);
    virtual void setSmoothingSamples(int samples);
    virtual void setRange(float min, float max);
    
    // Getters
    String getSensorId() const { return sensorId; }
    String getSensorType() const { return sensorType; }
    String getUnit() const { return unit; }
    float getLastValue() const { return lastValue; }
    SensorStatus getStatus() const { return status; }
    SensorQuality getQuality() const { return quality; }
    bool isCalibrated() const { return calibrated; }
    
    // Validation
    bool isValueValid(float value);
    void updateQuality();
    
    // Diagnostics
    virtual void printDiagnostics();
};

#endif // SENSOR_BASE_H
