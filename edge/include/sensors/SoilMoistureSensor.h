/**
 * @file SoilMoistureSensor.h
 * @brief Soil moisture sensor (capacitive or resistive)
 */

#ifndef SOIL_MOISTURE_SENSOR_H
#define SOIL_MOISTURE_SENSOR_H

#include "SensorBase.h"

class SoilMoistureSensor : public SensorBase
{
private:
  int pin;
  int minValue; // Air value (dry)
  int maxValue; // Water value (wet)
  int numSamples;

public:
  SoilMoistureSensor(String id, int analogPin, int minVal = 0, int maxVal = 4095, int samples = 10)
      : SensorBase(id, "soil_moisture"), pin(analogPin),
        minValue(minVal), maxValue(maxVal), numSamples(samples) {}

  bool begin() override
  {
    pinMode(pin, INPUT);
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

    // Average multiple samples to reduce noise
    long sum = 0;
    for (int i = 0; i < numSamples; i++)
    {
      sum += analogRead(pin);
      delay(10);
    }
    int rawValue = sum / numSamples;

    // Map to percentage (0-100%)
    // Note: Lower ADC value = more moisture for typical capacitive sensors
    float percentage = map(rawValue, minValue, maxValue, 100, 0);
    percentage = constrain(percentage, 0, 100);

    lastValue = percentage;
    lastReadTime = millis();
    status = SENSOR_OK;

    return percentage;
  }

  void calibrate(int airValue, int waterValue)
  {
    minValue = airValue;
    maxValue = waterValue;
  }

  int getRawValue()
  {
    return analogRead(pin);
  }
};

#endif
