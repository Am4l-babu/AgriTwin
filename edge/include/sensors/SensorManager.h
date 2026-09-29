/**
 * @file SensorManager.h
 * @brief Manages multiple sensors
 */

#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include "SensorBase.h"
#include <vector>

class SensorManager {
private:
    std::vector<SensorBase*> sensors;
    
public:
    SensorManager();
    ~SensorManager();
    
    void addSensor(SensorBase* sensor);
    void removeSensor(String sensorId);
    
    SensorBase* getSensor(int index);
    SensorBase* getSensorById(String sensorId);
    
    int getSensorCount() const { return sensors.size(); }
    
    void readAll();
    void printAllDiagnostics();
};

#endif
