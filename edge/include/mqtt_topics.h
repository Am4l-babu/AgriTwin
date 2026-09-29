/**
 * @file mqtt_topics.h
 * @brief MQTT topic definitions and naming conventions
 */

#ifndef MQTT_TOPICS_H
#define MQTT_TOPICS_H

#include <Arduino.h>
#include "config.h"

// ========================================
// TOPIC NAMING CONVENTION
// ========================================
// farms/{farm_id}/category/subcategory/action
// 
// Examples:
// - farms/farm_001/sensors/soil_moisture/data
// - farms/farm_001/commands/irrigation
// - farms/farm_001/status
// ========================================

// Base topic prefix
#define TOPIC_PREFIX "farms/" FARM_ID

// Sensor data topics
#define TOPIC_SENSOR_DATA TOPIC_PREFIX "/sensors/"
#define TOPIC_SOIL_MOISTURE TOPIC_SENSOR_DATA "soil_moisture/data"
#define TOPIC_TEMPERATURE TOPIC_SENSOR_DATA "temperature/data"
#define TOPIC_HUMIDITY TOPIC_SENSOR_DATA "humidity/data"
#define TOPIC_PH TOPIC_SENSOR_DATA "ph/data"
#define TOPIC_LIGHT TOPIC_SENSOR_DATA "light/data"
#define TOPIC_EC TOPIC_SENSOR_DATA "ec/data"

// Status topics
#define TOPIC_STATUS TOPIC_PREFIX "/status"
#define TOPIC_DIAGNOSTICS TOPIC_PREFIX "/diagnostics"
#define TOPIC_ALERTS TOPIC_PREFIX "/alerts"

// Command topics (subscribed)
#define TOPIC_COMMANDS TOPIC_PREFIX "/commands"
#define TOPIC_COMMAND_IRRIGATION TOPIC_COMMANDS "/irrigation"
#define TOPIC_COMMAND_RESTART TOPIC_COMMANDS "/restart"
#define TOPIC_COMMAND_CALIBRATE TOPIC_COMMANDS "/calibrate"
#define TOPIC_COMMAND_OTA TOPIC_COMMANDS "/ota_update"

// Configuration topics (subscribed)
#define TOPIC_CONFIG TOPIC_PREFIX "/config"
#define TOPIC_CONFIG_UPDATE TOPIC_CONFIG "/update"

// Actuator topics (subscribed)
#define TOPIC_ACTUATORS TOPIC_PREFIX "/actuators"
#define TOPIC_ACTUATOR_PUMP TOPIC_ACTUATORS "/pump"
#define TOPIC_ACTUATOR_VALVE TOPIC_ACTUATORS "/valve"

// LWT (Last Will and Testament)
#define TOPIC_LWT TOPIC_PREFIX "/lwt"

// QoS Levels
#define QOS_SENSOR_DATA 0      // Fire and forget (telemetry)
#define QOS_STATUS 1           // At least once (status)
#define QOS_COMMANDS 1         // At least once (commands)
#define QOS_ALERTS 1           // At least once (alerts)

#endif // MQTT_TOPICS_H
