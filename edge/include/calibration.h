#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>

/**
 * @brief Calibration data manager
 * 
 * Loads calibration profiles from JSON files stored in SPIFFS
 * Supports multiple calibration types:
 * - Two-point linear (soil moisture)
 * - Three-point polynomial (pH)
 * - Offset correction (temperature)
 */
class CalibrationManager {
public:
    CalibrationManager();
    
    /**
     * @brief Initialize calibration system and load profiles
     * @return true if initialization successful
     */
    bool begin();
    
    /**
     * @brief Load calibration profile for a sensor
     * @param sensorType Type of sensor (e.g., "soil_moisture", "ph")
     * @return true if calibration loaded successfully
     */
    bool loadCalibration(const char* sensorType);
    
    /**
     * @brief Two-point linear calibration
     * @param raw Raw ADC value
     * @param sensorType Sensor type identifier
     * @return Calibrated value
     */
    float calibrateTwoPoint(float raw, const char* sensorType);
    
    /**
     * @brief Three-point polynomial calibration (for pH)
     * @param raw Raw ADC value
     * @param sensorType Sensor type identifier
     * @return Calibrated pH value
     */
    float calibrateThreePoint(float raw, const char* sensorType);
    
    /**
     * @brief Simple offset calibration (for temperature)
     * @param raw Raw sensor value
     * @param sensorType Sensor type identifier
     * @return Calibrated value
     */
    float calibrateOffset(float raw, const char* sensorType);
    
    /**
     * @brief Save new calibration to SPIFFS
     * @param sensorType Sensor type
     * @param calibrationData JSON calibration data
     * @return true if save successful
     */
    bool saveCalibration(const char* sensorType, JsonDocument& calibrationData);
    
    /**
     * @brief Get calibration status for a sensor
     * @param sensorType Sensor type
     * @return true if calibration exists
     */
    bool hasCalibration(const char* sensorType);

private:
    struct TwoPointCalibration {
        float point1_raw;
        float point1_actual;
        float point2_raw;
        float point2_actual;
        bool loaded;
    };
    
    struct ThreePointCalibration {
        float point1_raw;
        float point1_actual;
        float point2_raw;
        float point2_actual;
        float point3_raw;
        float point3_actual;
        bool loaded;
    };
    
    struct OffsetCalibration {
        float offset;
        float multiplier;
        bool loaded;
    };
    
    // Storage for calibration data
    TwoPointCalibration soilMoistureCalib;
    ThreePointCalibration phCalib;
    OffsetCalibration temperatureCalib;
    OffsetCalibration humidityCalib;
    
    /**
     * @brief Load JSON calibration file from SPIFFS
     * @param filename Calibration file path
     * @param doc JsonDocument to load into
     * @return true if load successful
     */
    bool loadCalibrationFile(const char* filename, JsonDocument& doc);
    
    /**
     * @brief Get calibration file path for sensor type
     * @param sensorType Sensor type identifier
     * @return File path in SPIFFS
     */
    String getCalibrationPath(const char* sensorType);
};

#endif // CALIBRATION_H
