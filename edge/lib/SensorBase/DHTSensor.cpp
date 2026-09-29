/**
 * @file DHTSensor.cpp
 * @brief DHT Sensor Implementation
 */

#include "DHTSensor.h"

DHTSensor::DHTSensor(int digitalPin, uint8_t dhtType)
    : SensorBase("dht_" + String(digitalPin), "temperature_humidity", "°C/%")
    , pin(digitalPin)
    , type(dhtType)
    , lastTemperature(0.0)
    , lastHumidity(0.0)
{
    dht = new DHT(pin, type);
    setRange(-40.0, 80.0);  // DHT22 range
}

DHTSensor::~DHTSensor() {
    delete dht;
}

bool DHTSensor::begin() {
    dht->begin();
    delay(2000);  // DHT needs time to stabilize
    
    // Test read
    float temp = dht->readTemperature();
    if (isnan(temp)) {
        status = SENSOR_ERROR;
        return false;
    }
    
    status = SENSOR_OK;
    return true;
}

float DHTSensor::readRaw() {
    return dht->readTemperature();
}

float DHTSensor::readCalibrated() {
    return readTemperature();
}

float DHTSensor::readTemperature() {
    float temp = dht->readTemperature();
    
    if (isnan(temp)) {
        consecutiveErrors++;
        status = SENSOR_ERROR;
        return lastTemperature;
    }
    
    if (!isValueValid(temp)) {
        consecutiveErrors++;
        status = SENSOR_OUT_OF_RANGE;
        return lastTemperature;
    }
    
    // Apply calibration
    temp = applyCalibration(temp);
    
    // Smoothing
    valueBuffer.push_back(temp);
    if (valueBuffer.size() > smoothingSamples) {
        valueBuffer.erase(valueBuffer.begin());
    }
    
    lastTemperature = calculateMovingAverage();
    lastValue = lastTemperature;
    consecutiveErrors = 0;
    status = SENSOR_OK;
    updateQuality();
    
    return lastTemperature;
}

float DHTSensor::readHumidity() {
    float humidity = dht->readHumidity();
    
    if (isnan(humidity)) {
        consecutiveErrors++;
        return lastHumidity;
    }
    
    // Clamp to 0-100%
    humidity = constrain(humidity, 0.0, 100.0);
    lastHumidity = humidity;
    
    return lastHumidity;
}

float DHTSensor::readHeatIndex() {
    return dht->computeHeatIndex(lastTemperature, lastHumidity, false);
}
