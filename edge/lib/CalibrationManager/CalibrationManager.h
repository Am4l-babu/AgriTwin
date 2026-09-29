/**
 * @file CalibrationManager.h
 * @brief Handles sensor calibration storage and retrieval
 */

#ifndef CALIBRATION_MANAGER_H
#define CALIBRATION_MANAGER_H

#include <Arduino.h>
#include <Preferences.h>
#include <ArduinoJson.h>

struct CalibrationData {
    float offset;
    float multiplier;
    int airValue;      // For soil moisture
    int waterValue;    // For soil moisture
    unsigned long timestamp;
    bool valid;
};

class CalibrationManager {
private:
    Preferences preferences;
    
public:
    CalibrationManager();
    
    bool saveCalibration(String sensorId, CalibrationData data);
    CalibrationData loadCalibration(String sensorId);
    
    bool hasCalibration(String sensorId);
    void clearCalibration(String sensorId);
    void clearAll();
    
    String exportToJSON();
    bool importFromJSON(String json);
};

#endif
