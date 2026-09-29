/**
 * @file SoilMoistureSensor.cpp
 * @brief Soil Moisture Sensor Implementation
 */

#include "SoilMoistureSensor.h"

SoilMoistureSensor::SoilMoistureSensor(int analogPin)
    : SensorBase("soil_moisture_" + String(analogPin), "soil_moisture", "%")
    , pin(analogPin)
    , airValue(3100)
    , waterValue(1400)
{
    setRange(0.0, 100.0);
}

bool SoilMoistureSensor::begin() {
    pinMode(pin, INPUT);
    status = SENSOR_OK;
    return true;
}

float SoilMoistureSensor::readRaw() {
    int rawValue = analogRead(pin);
    lastReadTime = millis();
    return rawValue;
}

float SoilMoistureSensor::readCalibrated() {
    int rawValue = analogRead(pin);
    float percent = rawToPercent(rawValue);
    
    // Validate reading
    if (!isValueValid(percent)) {
        consecutiveErrors++;
        status = SENSOR_OUT_OF_RANGE;
        return lastValue;
    }
    
    // Check for outliers
    if (isOutlier(percent)) {
        // Still use it but flag quality
        quality = QUALITY_FAIR;
    }
    
    // Add to smoothing buffer
    valueBuffer.push_back(percent);
    if (valueBuffer.size() > smoothingSamples) {
        valueBuffer.erase(valueBuffer.begin());
    }
    
    // Calculate smoothed value
    lastValue = calculateMovingAverage();
    consecutiveErrors = 0;
    status = SENSOR_OK;
    updateQuality();
    
    return lastValue;
}

float SoilMoistureSensor::rawToPercent(int rawValue) {
    // Invert: lower ADC value = more moisture
    float percent = (float)(airValue - rawValue) / (float)(airValue - waterValue) * 100.0;
    
    // Clamp to 0-100%
    percent = constrain(percent, 0.0, 100.0);
    
    return percent;
}

void SoilMoistureSensor::calibrateAirValue(int value) {
    airValue = value;
    calibrated = true;
    Serial.print("Soil moisture air value calibrated: ");
    Serial.println(airValue);
}

void SoilMoistureSensor::calibrateWaterValue(int value) {
    waterValue = value;
    calibrated = true;
    Serial.print("Soil moisture water value calibrated: ");
    Serial.println(waterValue);
}

void SoilMoistureSensor::twoPointCalibration(int air, int water) {
    airValue = air;
    waterValue = water;
    calibrated = true;
    
    Serial.println("Soil moisture two-point calibration complete:");
    Serial.print("  Air: ");
    Serial.println(airValue);
    Serial.print("  Water: ");
    Serial.println(waterValue);
}
