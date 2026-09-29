/**
 * @file SoilMoistureSensor.h
 * @brief Capacitive Soil Moisture Sensor Implementation
 */

#ifndef SOIL_MOISTURE_SENSOR_H
#define SOIL_MOISTURE_SENSOR_H

#include "SensorBase.h"

class SoilMoistureSensor : public SensorBase {
private:
    int pin;
    int airValue;      // ADC value in air (0% moisture)
    int waterValue;    // ADC value in water (100% moisture)
    
    float rawToPercent(int rawValue);
    
public:
    SoilMoistureSensor(int analogPin);
    
    bool begin() override;
    float readRaw() override;
    float readCalibrated() override;
    
    void calibrateAirValue(int value);
    void calibrateWaterValue(int value);
    void twoPointCalibration(int air, int water);
};

#endif
