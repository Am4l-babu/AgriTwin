/**
 * @file DHTSensor.h
 * @brief DHT11/DHT22 temperature and humidity sensor
 */

#ifndef DHT_SENSOR_H
#define DHT_SENSOR_H

#include "SensorBase.h"
#include <DHT.h>

class DHTSensor : public SensorBase
{
private:
  DHT *dht;
  int pin;
  uint8_t dhtType;
  float temperature;
  float humidity;

public:
  DHTSensor(String id, int dataPin, uint8_t type = DHT22)
      : SensorBase(id, "dht"), pin(dataPin), dhtType(type),
        temperature(0), humidity(0)
  {
    dht = new DHT(pin, dhtType);
  }

  ~DHTSensor()
  {
    delete dht;
  }

  bool begin() override
  {
    dht->begin();
    delay(2000); // DHT needs time to stabilize
    initialized = true;
    status = SENSOR_OK;
    return true;
  }

  float read() override
  {
    // Returns temperature by default
    readBoth();
    return temperature;
  }

  void readBoth()
  {
    if (!initialized)
    {
      status = SENSOR_NOT_INITIALIZED;
      return;
    }

    humidity = dht->readHumidity();
    temperature = dht->readTemperature();

    if (isnan(humidity) || isnan(temperature))
    {
      status = SENSOR_ERROR;
      return;
    }

    lastValue = temperature;
    lastReadTime = millis();
    status = SENSOR_OK;
  }

  float getTemperature()
  {
    return temperature;
  }

  float getHumidity()
  {
    return humidity;
  }

  void printDiagnostics() override
  {
    Serial.printf("[%s] Temp: %.1f°C, Humidity: %.1f%%, Status: %d\n",
                  sensorId.c_str(), temperature, humidity, status);
  }
};

#endif
