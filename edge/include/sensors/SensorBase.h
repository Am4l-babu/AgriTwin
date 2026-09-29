/**
 * @file SensorBase.h
 * @brief Abstract base class for all sensors
 */

#ifndef SENSOR_BASE_H
#define SENSOR_BASE_H

#include <Arduino.h>

enum SensorStatus
{
  SENSOR_OK = 0,
  SENSOR_ERROR = 1,
  SENSOR_NOT_INITIALIZED = 2,
  SENSOR_TIMEOUT = 3,
  SENSOR_OUT_OF_RANGE = 4
};

class SensorBase
{
protected:
  String sensorId;
  String sensorType;
  bool initialized;
  SensorStatus status;
  unsigned long lastReadTime;
  float lastValue;

public:
  SensorBase(String id, String type)
      : sensorId(id), sensorType(type), initialized(false),
        status(SENSOR_NOT_INITIALIZED), lastReadTime(0), lastValue(0.0) {}

  virtual ~SensorBase() {}

  // Pure virtual functions - must be implemented
  virtual bool begin() = 0;
  virtual float read() = 0;

  // Common functions
  virtual String getId() const { return sensorId; }
  virtual String getType() const { return sensorType; }
  virtual SensorStatus getStatus() const { return status; }
  virtual bool isInitialized() const { return initialized; }
  virtual float getLastValue() const { return lastValue; }
  virtual unsigned long getLastReadTime() const { return lastReadTime; }

  virtual void printDiagnostics()
  {
    Serial.printf("[%s] Type: %s, Status: %d, Last: %.2f\n",
                  sensorId.c_str(), sensorType.c_str(), status, lastValue);
  }
};

#endif
