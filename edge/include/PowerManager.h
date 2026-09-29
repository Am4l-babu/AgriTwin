/**
 * @file PowerManager.h
 * @brief Power management and deep sleep control
 */

#ifndef POWER_MANAGER_H
#define POWER_MANAGER_H

#include <Arduino.h>
#include "config.h"

class PowerManager
{
private:
  int batteryPin;
  float batteryVoltage;
  bool batteryMonitoringEnabled;

public:
  PowerManager(int batPin = BATTERY_MONITOR_PIN)
      : batteryPin(batPin), batteryVoltage(0),
        batteryMonitoringEnabled(false) {}

  void begin()
  {
    if (batteryPin > 0)
    {
      pinMode(batteryPin, INPUT);
      batteryMonitoringEnabled = true;
    }
  }

  float readBatteryVoltage()
  {
    if (!batteryMonitoringEnabled)
    {
      return -1.0;
    }

    // Read battery voltage through voltage divider
    // Adjust multiplier based on your voltage divider ratio
    int rawValue = analogRead(batteryPin);
    batteryVoltage = (rawValue / 4095.0) * 3.3 * 2.0; // Adjust multiplier for your circuit
    return batteryVoltage;
  }

  float getBatteryPercentage()
  {
    if (batteryVoltage < 3.0)
      return 0;
    if (batteryVoltage > 4.2)
      return 100;
    return ((batteryVoltage - 3.0) / 1.2) * 100.0;
  }

  void enterDeepSleep(uint64_t sleepTimeSeconds)
  {
    Serial.printf("Entering deep sleep for %llu seconds...\n", sleepTimeSeconds);
    Serial.flush();
    delay(100);

#ifdef ESP32
    esp_sleep_enable_timer_wakeup(sleepTimeSeconds * 1000000ULL);
    esp_deep_sleep_start();
#else
    ESP.deepSleep(sleepTimeSeconds * 1000000ULL);
#endif
  }

  void enterLightSleep(uint64_t sleepTimeSeconds)
  {
    Serial.printf("Entering light sleep for %llu seconds...\n", sleepTimeSeconds);
    Serial.flush();
    delay(100);

#ifdef ESP32
    esp_sleep_enable_timer_wakeup(sleepTimeSeconds * 1000000ULL);
    esp_light_sleep_start();
#endif
  }

  bool shouldEnterLowPower()
  {
    float percentage = getBatteryPercentage();
    return (percentage > 0 && percentage < LOW_BATTERY_THRESHOLD);
  }

  bool isCriticalBattery()
  {
    float percentage = getBatteryPercentage();
    return (percentage > 0 && percentage < CRITICAL_BATTERY_THRESHOLD);
  }
};

#endif
