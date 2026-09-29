/**
 * @file CalibrationManager.h
 * @brief Manages sensor calibration values
 */

#ifndef CALIBRATION_MANAGER_H
#define CALIBRATION_MANAGER_H

#include <Arduino.h>

class CalibrationManager
{
public:
  struct SoilCalibration
  {
    int airValue = 3000;
    int waterValue = 1000;
  };

  struct PHCalibration
  {
    float ph4Voltage = 2.0;
    float ph7Voltage = 1.5;
  };

  SoilCalibration soilCal;
  PHCalibration phCal;

  void begin()
  {
    // Default values - would load from SPIFFS in full implementation
    Serial.println("✓ Calibration manager initialized (using defaults)");
  }

  SoilCalibration getSoilCalibration() { return soilCal; }
  PHCalibration getPHCalibration() { return phCal; }
};

#endif
