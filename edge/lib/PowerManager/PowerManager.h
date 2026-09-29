/**
 * @file PowerManager.h
 * @brief Power management for battery-powered deployments
 */

#ifndef POWER_MANAGER_H
#define POWER_MANAGER_H

#include <Arduino.h>

class PowerManager {
private:
    int batteryPin;
    float batteryVoltage;
    float voltageDividerRatio;
    
    unsigned long lastVoltageCheck;
    
public:
    PowerManager();
    
    void begin();
    void loop();
    
    float getBatteryVoltage();
    int getBatteryPercent();
    bool isBatteryLow();
    
    void enableDeepSleep(uint64_t durationMicros);
    void enableLightSleep(uint64_t durationMicros);
};

#endif
