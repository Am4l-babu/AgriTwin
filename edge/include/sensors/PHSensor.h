/**
 * @file PHSensor.h
 * @brief Analog pH sensor with calibration
 */

#ifndef PH_SENSOR_H
#define PH_SENSOR_H

#include "SensorBase.h"

class PHSensor : public SensorBase
{
private:
  int pin;
  float acidVoltage;    // Voltage at pH 4.0
  float neutralVoltage; // Voltage at pH 7.0
  int numSamples;

public:
  PHSensor(String id, int analogPin, int samples = 10)
      : SensorBase(id, "ph"), pin(analogPin), numSamples(samples),
        acidVoltage(2.0), neutralVoltage(1.5) {} // Default calibration

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

    // Average multiple samples
    long sum = 0;
    for (int i = 0; i < numSamples; i++)
    {
      sum += analogRead(pin);
      delay(10);
    }
    int rawValue = sum / numSamples;

    // Convert ADC to voltage (ESP32 ADC is 12-bit, 0-3.3V)
    float voltage = (rawValue / 4095.0) * 3.3;

    // Calculate pH from voltage using two-point calibration
    float slope = (7.0 - 4.0) / (neutralVoltage - acidVoltage);
    float ph = 7.0 - slope * (voltage - neutralVoltage);

    // Constrain to valid pH range
    ph = constrain(ph, 0, 14);

    lastValue = ph;
    lastReadTime = millis();
    status = SENSOR_OK;

    return ph;
  }

  void calibrate(float ph4Voltage, float ph7Voltage)
  {
    acidVoltage = ph4Voltage;
    neutralVoltage = ph7Voltage;
  }

  int getRawValue()
  {
    return analogRead(pin);
  }

  float getVoltage()
  {
    return (analogRead(pin) / 4095.0) * 3.3;
  }
};

#endif
