/**
 * @file DHTSensor.h
 * @brief DHT22/DHT11 Temperature and Humidity Sensor
 */

#ifndef DHT_SENSOR_H
#define DHT_SENSOR_H

#include "SensorBase.h"
#include <DHT.h>

class DHTSensor : public SensorBase {
private:
    DHT* dht;
    int pin;
    uint8_t type;
    
    float lastTemperature;
    float lastHumidity;
    
public:
    DHTSensor(int digitalPin, uint8_t dhtType);
    ~DHTSensor();
    
    bool begin() override;
    float readRaw() override;
    float readCalibrated() override;
    
    float readTemperature();
    float readHumidity();
    float readHeatIndex();
};

#endif
