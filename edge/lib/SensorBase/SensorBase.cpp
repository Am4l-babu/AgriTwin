/**
 * @file SensorBase.cpp
 * @brief Implementation of SensorBase class
 */

#include "SensorBase.h"
#include <numeric>
#include <algorithm>

SensorBase::SensorBase(String id, String type, String unit)
    : sensorId(id)
    , sensorType(type)
    , unit(unit)
    , lastValue(0.0)
    , minValue(-INFINITY)
    , maxValue(INFINITY)
    , status(SENSOR_NOT_INITIALIZED)
    , quality(QUALITY_UNKNOWN)
    , calibrationOffset(0.0)
    , calibrationMultiplier(1.0)
    , calibrated(false)
    , smoothingSamples(5)
    , consecutiveErrors(0)
    , lastReadTime(0)
{
    valueBuffer.reserve(smoothingSamples);
}

void SensorBase::calibrate(float offset, float multiplier) {
    calibrationOffset = offset;
    calibrationMultiplier = multiplier;
    calibrated = true;
    
    Serial.print("Sensor ");
    Serial.print(sensorId);
    Serial.print(" calibrated: offset=");
    Serial.print(offset);
    Serial.print(", multiplier=");
    Serial.println(multiplier);
}

void SensorBase::setSmoothingSamples(int samples) {
    smoothingSamples = max(1, min(samples, 20));  // Limit 1-20 samples
    valueBuffer.clear();
    valueBuffer.reserve(smoothingSamples);
}

void SensorBase::setRange(float min, float max) {
    minValue = min;
    maxValue = max;
}

float SensorBase::calculateMovingAverage() {
    if (valueBuffer.empty()) {
        return lastValue;
    }
    
    float sum = std::accumulate(valueBuffer.begin(), valueBuffer.end(), 0.0f);
    return sum / valueBuffer.size();
}

bool SensorBase::isOutlier(float value) {
    if (valueBuffer.size() < 3) {
        return false;  // Not enough data to determine outliers
    }
    
    // Calculate mean and standard deviation
    float mean = calculateMovingAverage();
    
    float sumSquaredDiff = 0.0;
    for (float v : valueBuffer) {
        float diff = v - mean;
        sumSquaredDiff += diff * diff;
    }
    
    float stdDev = sqrt(sumSquaredDiff / valueBuffer.size());
    
    // Check if value is more than 2.5 standard deviations from mean
    float deviation = abs(value - mean);
    return (deviation > 2.5 * stdDev);
}

float SensorBase::applyCalibration(float rawValue) {
    return (rawValue * calibrationMultiplier) + calibrationOffset;
}

bool SensorBase::isValueValid(float value) {
    // Check for NaN or infinity
    if (isnan(value) || isinf(value)) {
        return false;
    }
    
    // Check if within valid range
    if (value < minValue || value > maxValue) {
        return false;
    }
    
    return true;
}

void SensorBase::updateQuality() {
    // Quality based on consecutive errors and data stability
    if (consecutiveErrors == 0) {
        if (valueBuffer.size() >= smoothingSamples) {
            float mean = calculateMovingAverage();
            float variance = 0.0;
            
            for (float v : valueBuffer) {
                float diff = v - mean;
                variance += diff * diff;
            }
            variance /= valueBuffer.size();
            float stdDev = sqrt(variance);
            
            // Lower variance = better quality
            float coefficientOfVariation = (mean != 0) ? (stdDev / abs(mean)) : 0;
            
            if (coefficientOfVariation < 0.05) {
                quality = QUALITY_EXCELLENT;
            } else if (coefficientOfVariation < 0.10) {
                quality = QUALITY_GOOD;
            } else if (coefficientOfVariation < 0.20) {
                quality = QUALITY_FAIR;
            } else {
                quality = QUALITY_POOR;
            }
        } else {
            quality = QUALITY_UNKNOWN;
        }
    } else if (consecutiveErrors < 3) {
        quality = QUALITY_FAIR;
    } else {
        quality = QUALITY_POOR;
    }
}

void SensorBase::printDiagnostics() {
    Serial.println("========================================");
    Serial.print("Sensor: ");
    Serial.println(sensorId);
    Serial.print("Type: ");
    Serial.println(sensorType);
    Serial.print("Last Value: ");
    Serial.print(lastValue);
    Serial.print(" ");
    Serial.println(unit);
    Serial.print("Status: ");
    Serial.println(status);
    Serial.print("Quality: ");
    Serial.println(quality);
    Serial.print("Calibrated: ");
    Serial.println(calibrated ? "Yes" : "No");
    Serial.print("Consecutive Errors: ");
    Serial.println(consecutiveErrors);
    Serial.print("Buffer Size: ");
    Serial.println(valueBuffer.size());
    Serial.println("========================================");
}
