/**
 * @file LightSensor.h
 * @brief BH1750 or analog light sensor (LDR)
 */

#ifndef LIGHT_SENSOR_H
#define LIGHT_SENSOR_H

#include "SensorBase.h"

// Simple analog LDR version
class LightSensor : public SensorBase
{
private:
  int pin;
  int numSamples;
  bool useDigital; // If true, using BH1750; if false, using analog LDR

public:
  LightSensor(String id, int analogPin, int samples = 10)
      : SensorBase(id, "light"), pin(analogPin),
        numSamples(samples), useDigital(false) {}

  bool begin() override
  {
    if (!useDigital)
    {
      pinMode(pin, INPUT);
    }
    // For BH1750, would initialize I2C here
    initialized = true;
    status = SENSOR_OK;
    return true;
  }

  float read() override
  {
    if (!initialized)
    {
      status = SENSOR_NOT_INITIALIZED;
      return -1.0;
    }

    if (useDigital)
    {
      // BH1750 digital reading would go here
      // For now, return placeholder
      lastValue = 0;
    }
    else
    {
      // Analog LDR reading
      long sum = 0;
      for (int i = 0; i < numSamples; i++)
      {
        sum += analogRead(pin);
        delay(10);
      }
      int rawValue = sum / numSamples;

      // Convert to approximate lux (simplified)
      // This is sensor-specific and should be calibrated
      float lux = map(rawValue, 0, 4095, 0, 1000);
      lastValue = lux;
    }

    lastReadTime = millis();
    status = SENSOR_OK;

    return lastValue;
  }

  int getRawValue()
  {
    return analogRead(pin);
  }
};

#endif
