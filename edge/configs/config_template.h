/**
 * @file config.h
 * @brief Configuration template for Smart Farming Edge Device
 *
 * Copy this file and rename to config.h
 * Fill in your specific values
 * DO NOT commit config.h to version control
 */

#ifndef CONFIG_H
#define CONFIG_H

// ========================================
// DEVICE IDENTIFICATION
// ========================================
#define FARM_ID "farm_001"
#define DEVICE_HOSTNAME "sf-edge-001"
#define VERSION "1.0.0"

// ========================================
// WIFI CONFIGURATION
// ⚠️ IMPORTANT: Copy this file to edge/include/config.h and update with your credentials
// ========================================
#define WIFI_SSID "YOUR_WIFI_SSID"         // Your WiFi network name
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD" // Your WiFi password
#define WIFI_MAX_RETRIES 20
#define WIFI_CHECK_INTERVAL 30000 // Check WiFi every 30 seconds
#define WIFI_POWER_SAVE false     // Enable WiFi power saving

// ========================================
// MQTT CONFIGURATION
// The ESP32 connects to the Raspberry Pi fog node via mDNS hostname.
// Do NOT hardcode an IP address here — use the hostname so it works
// across dynamic IP environments.
// ========================================
#define MQTT_BROKER "agritwin-fog.local" // Raspberry Pi fog node (mDNS/Avahi)
#define MQTT_PORT 1883
#define MQTT_USERNAME "" // Leave empty if no authentication
#define MQTT_PASSWORD "" // Leave empty if no authentication
#define MQTT_CLIENT_ID "edge_device"
#define MQTT_MAX_RETRIES 5
#define MQTT_MAX_PACKET_SIZE 512
#define MQTT_KEEPALIVE 60

// ========================================
// TIME CONFIGURATION
// ========================================
#define NTP_SERVER "pool.ntp.org"
#define TIMEZONE_OFFSET 0 // UTC offset in hours

#define WIFI_SSID "YOUR_WIFI_SSID" // Your WiFi network name
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"      // Your WiFi password
// ========================================

// Enable/Disable Sensors
#define ENABLE_SOIL_MOISTURE true
#define ENABLE_DHT22 true
#define ENABLE_LIGHT_SENSOR true
#define ENABLE_PH_SENSOR false
#define ENABLE_EC_SENSOR false
#define ENABLE_WATER_LEVEL false

// Sensor Pins
#define SOIL_MOISTURE_PIN 34 // ADC pin
#define DHT_PIN 15           // Digital pin
#define DHT_TYPE DHT22       // DHT11 or DHT22
#define PH_SENSOR_PIN 35     // ADC pin
#define EC_SENSOR_PIN 32     // ADC pin
#define WATER_LEVEL_PIN 33   // ADC pin
#define LIGHT_SENSOR_SDA 21  // I2C SDA (BH1750)
#define LIGHT_SENSOR_SCL 22  // I2C SCL (BH1750)

// Sensor Reading Intervals
#define SENSOR_READ_INTERVAL 5000      // Read sensors every 5 seconds
#define MQTT_PUBLISH_INTERVAL 60000    // Publish data every 60 seconds
#define STATUS_PUBLISH_INTERVAL 300000 // Publish status every 5 minutes

// Data Smoothing
#define SENSOR_SMOOTHING_SAMPLES 5   // Average of N samples
#define SENSOR_OUTLIER_THRESHOLD 2.5 // Standard deviations

// ========================================
// CALIBRATION
// ========================================
#define CALIBRATION_MODE false

// Soil Moisture Calibration (ADC values)
#define SOIL_MOISTURE_AIR_VALUE 3100   // Sensor in air
#define SOIL_MOISTURE_WATER_VALUE 1400 // Sensor in water
#define SOIL_MOISTURE_MIN_PERCENT 0.0
#define SOIL_MOISTURE_MAX_PERCENT 100.0

// pH Calibration
#define PH_NEUTRAL_VOLTAGE 1500 // mV at pH 7.0
#define PH_ACID_VOLTAGE 2032    // mV at pH 4.0
#define PH_SLOPE -59.16         // mV per pH unit (Nernstian)

// Temperature Compensation
#define ENABLE_TEMP_COMPENSATION true

// ========================================
// POWER MANAGEMENT
// ========================================
#define BATTERY_POWERED false
#define BATTERY_VOLTAGE_PIN 35
#define BATTERY_LOW_THRESHOLD 3.3 // Volts
#define BATTERY_DIVIDER_RATIO 2.0 // Voltage divider ratio

// Deep Sleep Configuration
#define DEEP_SLEEP_ENABLED false
#define DEEP_SLEEP_DURATION_SECONDS 300 // 5 minutes
#define DEEP_SLEEP_AFTER_MILLIS 0       // Sleep immediately after publish

// ========================================
// OTA (Over-The-Air) UPDATES
// ========================================
#define OTA_ENABLED true
#define OTA_PASSWORD "smart_farming_ota_password"
#define OTA_PORT 3232

// ========================================
// LED INDICATORS
// ========================================
#define ENABLE_LED_INDICATORS true
#define LED_WIFI_PIN 2 // Built-in LED (ESP32)
#define LED_MQTT_PIN 4
#define LED_ERROR_PIN 5
#define LED_BLINK_INTERVAL 500

// ========================================
// SERIAL CONFIGURATION
// ========================================
#define SERIAL_BAUDRATE 115200
#define LOG_LEVEL LOG_LEVEL_VERBOSE // VERBOSE, NOTICE, WARNING, ERROR, FATAL

// ========================================
// WATCHDOG TIMER
// ========================================
#define ENABLE_WATCHDOG true
#define WATCHDOG_TIMEOUT_SECONDS 30

// ========================================
// DATA BUFFERING (for offline mode)
// ========================================
#define ENABLE_LOCAL_BUFFER true
#define BUFFER_MAX_RECORDS 100
#define BUFFER_FLASH_ENABLED true // Save to SPIFFS/LittleFS

// ========================================
// ADVANCED FEATURES
// ========================================
#define ENABLE_EDGE_AI false         // Edge ML inference
#define ENABLE_LOCAL_DECISION false  // Autonomous irrigation triggers
#define IRRIGATION_THRESHOLD 30.0    // Soil moisture % threshold
#define IRRIGATION_PIN 25            // Relay control pin
#define IRRIGATION_DURATION_MS 30000 // 30 seconds

// ========================================
// ALERTS
// ========================================
#define ENABLE_ALERTS true
#define ALERT_SOIL_MOISTURE_LOW 20.0
#define ALERT_SOIL_MOISTURE_HIGH 80.0
#define ALERT_TEMPERATURE_LOW 10.0
#define ALERT_TEMPERATURE_HIGH 35.0
#define ALERT_PH_LOW 5.5
#define ALERT_PH_HIGH 7.5

#endif // CONFIG_H
