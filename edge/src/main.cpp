/**
 * @file main_simple.cpp
 * @brief Simple ESP32 firmware for LDR and DHT11
 *
 * Hardware:
 * - LDR on GPIO 4 (3.3V powered, 10k pull-down to GND)
 * - DHT11 on GPIO 27
 *
 * WiFi: set your networks in the CONFIGURATION block below
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <ESPmDNS.h> // mDNS resolution for agritwin-fog.local
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <ArduinoOTA.h>   // OTA firmware updates
#include <esp_task_wdt.h> // Hardware watchdog timer

// ========================================
// FIRMWARE VERSION
// ========================================
#define FIRMWARE_VERSION "1.1.0"
#define FIRMWARE_BUILD_DATE __DATE__ " " __TIME__

// Watchdog timeout (seconds) — resets ESP32 if loop hangs
#define WDT_TIMEOUT_S 30

// ========================================
// CONFIGURATION
// ========================================
// Multiple WiFi networks, tried in priority order (home → mobile hotspot → phone hotspot)
#define WIFI1_SSID "YOUR_WIFI_1_SSID"
#define WIFI1_PASSWORD "YOUR_WIFI_1_PASSWORD"
#define WIFI2_SSID "YOUR_WIFI_2_SSID"
#define WIFI2_PASSWORD "YOUR_WIFI_2_PASSWORD"
#define WIFI3_SSID "YOUR_WIFI_3_SSID"
#define WIFI3_PASSWORD "YOUR_WIFI_3_PASSWORD"

// ----------------------------------------
// Raspberry Pi fog node — resolve via mDNS.
// Both ESP32 and Pi must be on the same
// WiFi network for mDNS (.local) to work.
// ----------------------------------------
#define MQTT_BROKER "agritwin-fog.local"
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "esp32_edge_001"

// Sensors
#define LDR_PIN 33           // LDR on GPIO 33 (ADC1 - Compatible with WiFi)
#define SOIL_MOISTURE_PIN 34 // Soil moisture sensor on GPIO 34 (ADC1)
#define DHT_PIN 4            // DHT11 on GPIO 4
#define DHT_TYPE DHT11

// Relay outputs (active-LOW relay modules — HIGH = OFF, LOW = ON)
#define RELAY_PUMP_PIN 26  // Water pump relay on GPIO 26
#define RELAY_LIGHT_PIN 25 // Grow light relay on GPIO 25

// MQTT topics for relay state feedback
#define TOPIC_RELAY_STATE FARM_ID "/relay/state"

// Timing — defaults; can be updated at runtime by Thompson Sampling fog command
#define READ_INTERVAL_DEFAULT 5000UL     // 5 s
#define PUBLISH_INTERVAL_DEFAULT 10000UL // 10 s
#define READ_INTERVAL_MIN 5000UL         // floor: never faster than 5 s
#define READ_INTERVAL_MAX 60000UL        // ceiling: never slower than 60 s

// ----------------------------------------
// MQTT Topics
// Must match fog ingestion subscription:
//   farms/+/sensors/+/data
//   farms/+/status
// ----------------------------------------
#define FARM_ID "farms/001"
#define TOPIC_TEMP_DATA FARM_ID "/sensors/temperature/data"
#define TOPIC_HUMIDITY_DATA FARM_ID "/sensors/humidity/data"
#define TOPIC_LIGHT_DATA FARM_ID "/sensors/light/data"
#define TOPIC_STATUS FARM_ID "/status"
#define TOPIC_COMMAND FARM_ID "/commands"
#define TOPIC_LWT FARM_ID "/lwt"
#define TOPIC_SENSORS "agritwin/sensors"

// ========================================
// GLOBAL OBJECTS
// ========================================
WiFiMulti wifiMulti;
WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastRead = 0;
unsigned long lastPublish = 0;

// Adaptive intervals — written by mqttCallback when fog sends set_interval
unsigned long readInterval = READ_INTERVAL_DEFAULT;
unsigned long publishInterval = PUBLISH_INTERVAL_DEFAULT;

// Sensor data
float temperature = 0;
float humidity = 0;
int lightLevel = 0;
int soilMoisture = 0; // 0-100 % (100 = fully wet)
int rawLDRVal = 0;    // raw ADC reading (0-4095) for calibration
int rawSoilVal = 0;   // raw ADC reading (0-4095) for calibration

// Relay state (true = ON)
bool pumpState = false;
bool lightRelayState = false;

// ----------------------------------------
// Auto-control mode & thresholds
// Set auto_mode=false to use manual-only control (default: true)
// Pump:  ON  when soil < pumpOnThreshold,  OFF when soil >= pumpOffThreshold
// Light: ON  when light < lightOnThreshold, OFF when light >= lightOffThreshold
// Override: a manual relay command disables auto-mode for that relay until
//           the sensor crosses the threshold again (hysteresis re-engage).
// ----------------------------------------
bool autoMode = true;          // global auto/manual toggle
bool pumpAutoOverride = false; // true = manual command was applied, skip auto
bool lightAutoOverride = false;

int pumpOnThreshold = 30;   // % — turn pump ON  when soil moisture BELOW this
int pumpOffThreshold = 60;  // % — turn pump OFF when soil moisture AT OR ABOVE this
int lightOnThreshold = 20;  // % — turn light ON  when light level BELOW this
int lightOffThreshold = 50; // % — turn light OFF when light level AT OR ABOVE this

// ========================================
// WiFi Setup
// ========================================
void setupWiFi()
{
  Serial.println("Connecting to WiFi (multi-network scan)...");
  Serial.println("Priority: " WIFI1_SSID " → " WIFI2_SSID " → " WIFI3_SSID);

  WiFi.mode(WIFI_STA);

  // Add networks in priority order
  wifiMulti.addAP(WIFI1_SSID, WIFI1_PASSWORD);
  wifiMulti.addAP(WIFI2_SSID, WIFI2_PASSWORD);
  wifiMulti.addAP(WIFI3_SSID, WIFI3_PASSWORD);

  int attempts = 0;
  while (wifiMulti.run() != WL_CONNECTED && attempts < 30)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Connected SSID: ");
    Serial.println(WiFi.SSID());
    Serial.print("Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");

    // Start mDNS so we can resolve agritwin-fog.local
    if (!MDNS.begin("esp32-edge"))
    {
      Serial.println("[mDNS] Failed to start — .local hostnames may not resolve!");
    }
    else
    {
      Serial.println("[mDNS] Started OK (esp32-edge.local)");
    }
  }
  else
  {
    Serial.println("\nWiFi Connection Failed!");
  }
}

// ========================================
// MQTT Setup
// ========================================
void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  String message;
  for (unsigned int i = 0; i < length; i++)
    message += (char)payload[i];

  Serial.print("[MQTT cmd] ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(message);

  // Parse JSON command
  StaticJsonDocument<256> cmd;
  if (deserializeJson(cmd, message) == DeserializationError::Ok)
  {
    const char *command = cmd["command"] | "";

    // ---- Set auto-control thresholds ----
    // Expected JSON: {"command":"set_thresholds","pump_on":30,"pump_off":60,"light_on":20,"light_off":50}
    if (strcmp(command, "set_thresholds") == 0)
    {
      int po = cmd["pump_on"] | -1;
      int pf = cmd["pump_off"] | -1;
      int lo = cmd["light_on"] | -1;
      int lf = cmd["light_off"] | -1;
      if (po >= 0 && po < pf)
      {
        pumpOnThreshold = po;
        pumpOffThreshold = pf;
      }
      if (lo >= 0 && lo < lf)
      {
        lightOnThreshold = lo;
        lightOffThreshold = lf;
      }
      // Clear any manual overrides after threshold update
      pumpAutoOverride = false;
      lightAutoOverride = false;
      Serial.printf("[AUTO] Thresholds → pump ON<%d%% OFF>=%d%%  light ON<%d%% OFF>=%d%%\n",
                    pumpOnThreshold, pumpOffThreshold, lightOnThreshold, lightOffThreshold);
    }

    // ---- Thompson Sampling adaptive-interval command ----
    // Expected JSON: {"command":"set_interval","read_ms":10000,"publish_ms":20000}
    if (strcmp(command, "set_interval") == 0)
    {
      unsigned long newRead = cmd["read_ms"] | 0UL;
      unsigned long newPublish = cmd["publish_ms"] | 0UL;

      if (newRead >= READ_INTERVAL_MIN && newRead <= READ_INTERVAL_MAX)
      {
        readInterval = newRead;
        publishInterval = (newPublish >= newRead) ? newPublish : newRead * 2;
        Serial.printf("[TS] Intervals updated → read=%lus  publish=%lus\n",
                      readInterval / 1000, publishInterval / 1000);
      }
      else
      {
        Serial.printf("[TS] set_interval out of bounds (read_ms=%lu) — ignored\n",
                      newRead);
      }
    }

    // ---- Relay control command ----
    // Expected JSON: {"command":"relay","relay":"pump","state":"on"}
    //                {"command":"relay","relay":"light","state":"off"}
    else if (strcmp(command, "relay") == 0)
    {
      const char *relayName = cmd["relay"] | "";
      const char *state = cmd["state"] | "";
      bool turnOn = (strcmp(state, "on") == 0);

      if (strcmp(relayName, "pump") == 0)
      {
        pumpState = turnOn;
        pumpAutoOverride = true; // manual command — pause auto for pump
        // Active-LOW relay: LOW = energised (ON), HIGH = de-energised (OFF)
        digitalWrite(RELAY_PUMP_PIN, turnOn ? LOW : HIGH);
        Serial.printf("[RELAY] Pump → %s (manual)\n", turnOn ? "ON" : "OFF");
      }
      else if (strcmp(relayName, "light") == 0)
      {
        lightRelayState = turnOn;
        lightAutoOverride = true; // manual command — pause auto for light
        digitalWrite(RELAY_LIGHT_PIN, turnOn ? LOW : HIGH);
        Serial.printf("[RELAY] Light → %s (manual)\n", turnOn ? "ON" : "OFF");
      }
      else if (strcmp(relayName, "auto_mode") == 0)
      {
        autoMode = turnOn;
        if (autoMode)
        {
          pumpAutoOverride = false;
          lightAutoOverride = false;
        }
        Serial.printf("[AUTO] Auto-mode → %s\n", autoMode ? "ON" : "OFF");
      }

      // Publish relay state back so dashboard can confirm
      StaticJsonDocument<128> stateDoc;
      stateDoc["pump"] = pumpState ? "on" : "off";
      stateDoc["light"] = lightRelayState ? "on" : "off";
      char stateBuf[128];
      serializeJson(stateDoc, stateBuf, sizeof(stateBuf));
      mqttClient.publish(TOPIC_RELAY_STATE, stateBuf, true); // retained
    }
  }
}

void setupMQTT()
{
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(60);
  mqttClient.setSocketTimeout(15);

  Serial.print("Connecting to MQTT broker: ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_PORT);

  // Last Will and Testament — published automatically if ESP32 drops
  const char *lwtPayload = "{\"device_id\":\"esp32_edge_001\",\"status\":\"offline\"}";

  if (mqttClient.connect(MQTT_CLIENT_ID,
                         nullptr, nullptr,   // no auth
                         TOPIC_LWT, 0, true, // LWT: topic, QoS, retain
                         lwtPayload))
  {
    Serial.println("MQTT Connected!");
    mqttClient.subscribe(TOPIC_COMMAND);

    // Publish online status
    StaticJsonDocument<200> doc;
    doc["device_id"] = MQTT_CLIENT_ID;
    doc["status"] = "online";
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["build_date"] = FIRMWARE_BUILD_DATE;
    doc["timestamp"] = millis();

    String output;
    serializeJson(doc, output);
    mqttClient.publish(TOPIC_STATUS, output.c_str(), true); // retained
    Serial.println("Status published: " + output);
  }
  else
  {
    Serial.print("MQTT Connection Failed! State: ");
    Serial.println(mqttClient.state());
    Serial.println("Hint: check that agritwin-fog.local is reachable and port 1883 is open.");
  }
}

void reconnectMQTT()
{
  if (mqttClient.connected())
    return;

  static unsigned long lastAttempt = 0;
  static int backoff = 2000; // start at 2 s, double each failure up to 30 s

  if (millis() - lastAttempt < (unsigned long)backoff)
    return;
  lastAttempt = millis();

  Serial.println("Reconnecting to MQTT...");
  const char *lwtPayload = "{\"device_id\":\"esp32_edge_001\",\"status\":\"offline\"}";

  if (mqttClient.connect(MQTT_CLIENT_ID,
                         nullptr, nullptr,
                         TOPIC_LWT, 0, true, lwtPayload))
  {
    Serial.println("MQTT Reconnected!");
    mqttClient.subscribe(TOPIC_COMMAND);
    backoff = 2000; // reset on success
  }
  else
  {
    backoff = min(backoff * 2, 30000); // exponential back-off, cap 30 s
    Serial.printf("MQTT reconnect failed (state=%d), retrying in %d ms\n",
                  mqttClient.state(), backoff);
  }
}

// ========================================
// Sensor Reading
// ========================================
int dhtErrors = 0; // consecutive DHT read failures

void readSensors()
{
  // Read DHT11 with retry (DHT11 can occasionally return NaN)
  float t = NAN, h = NAN;
  for (int attempt = 0; attempt < 3 && (isnan(t) || isnan(h)); attempt++)
  {
    t = dht.readTemperature();
    h = dht.readHumidity();
    if (isnan(t) || isnan(h))
      delay(100);
  }

  if (!isnan(t) && !isnan(h))
  {
    temperature = t;
    humidity = h;
    dhtErrors = 0;
  }
  else
  {
    dhtErrors++;
    Serial.printf("DHT read failed (%d consecutive)\n", dhtErrors);
    // Keep previous valid values if available, otherwise leave NaN
  }

  // Average 5 ADC samples for analog sensors to reduce noise
  long sumLDR = 0, sumSoil = 0;
  for (int i = 0; i < 5; i++)
  {
    sumLDR += analogRead(LDR_PIN);
    sumSoil += analogRead(SOIL_MOISTURE_PIN);
    delay(2);
  }
  int rawLDR = sumLDR / 5;
  int rawSoil = sumSoil / 5;

  // Store raw ADC values globally so publishData() can include them
  rawLDRVal = rawLDR;
  rawSoilVal = rawSoil;

  lightLevel = map(rawLDR, 0, 4095, 0, 100);
  soilMoisture = constrain(map(rawSoil, 4095, 0, 0, 100), 0, 100);

  // Print to serial
  Serial.println("\n=== Sensor Readings ===");
  Serial.print("Temperature: ");
  if (!isnan(temperature))
  {
    Serial.print(temperature);
    Serial.println(" °C");
  }
  else
  {
    Serial.println("ERROR");
  }

  Serial.print("Humidity: ");
  if (!isnan(humidity))
  {
    Serial.print(humidity);
    Serial.println(" %");
  }
  else
  {
    Serial.println("ERROR");
  }

  Serial.print("Light Level: ");
  Serial.print(lightLevel);
  Serial.print(" % (Raw: ");
  Serial.print(rawLDR);
  Serial.println(")");
  Serial.print("Soil Moisture: ");
  Serial.print(soilMoisture);
  Serial.print(" % (Raw: ");
  Serial.print(rawSoil);
  Serial.println(")");
  Serial.println("====================");
}

// ========================================
// Auto Control Logic
// Called after every sensor read.
// Pump:  hysteresis band [pumpOnThreshold, pumpOffThreshold]
// Light: hysteresis band [lightOnThreshold, lightOffThreshold]
// Manual MQTT commands set the override flag; when the sensor re-crosses
// the threshold band the override is cleared and auto resumes.
// ========================================
void autoControl()
{
  if (!autoMode)
    return;

  // ── Pump ──────────────────────────────────────────────────────────────
  // Clear manual override once soil returns to a "neutral" level
  if (pumpAutoOverride && soilMoisture >= pumpOnThreshold && soilMoisture < pumpOffThreshold)
    pumpAutoOverride = false;

  if (!pumpAutoOverride)
  {
    bool shouldBeOn = (soilMoisture < pumpOnThreshold)     ? true
                      : (soilMoisture >= pumpOffThreshold) ? false
                                                           : pumpState; // inside hysteresis band → hold current state
    if (shouldBeOn != pumpState)
    {
      pumpState = shouldBeOn;
      digitalWrite(RELAY_PUMP_PIN, shouldBeOn ? LOW : HIGH);
      Serial.printf("[AUTO] Pump → %s (soil=%d%%)\n", shouldBeOn ? "ON" : "OFF", soilMoisture);
      // Publish updated relay state
      StaticJsonDocument<128> s;
      s["pump"] = pumpState ? "on" : "off";
      s["light"] = lightRelayState ? "on" : "off";
      char buf[128];
      serializeJson(s, buf, sizeof(buf));
      mqttClient.publish(TOPIC_RELAY_STATE, buf, true);
    }
  }

  // ── Light ─────────────────────────────────────────────────────────────
  if (lightAutoOverride && lightLevel >= lightOnThreshold && lightLevel < lightOffThreshold)
    lightAutoOverride = false;

  if (!lightAutoOverride)
  {
    bool shouldBeOn = (lightLevel < lightOnThreshold)     ? true
                      : (lightLevel >= lightOffThreshold) ? false
                                                          : lightRelayState;
    if (shouldBeOn != lightRelayState)
    {
      lightRelayState = shouldBeOn;
      digitalWrite(RELAY_LIGHT_PIN, shouldBeOn ? LOW : HIGH);
      Serial.printf("[AUTO] Light → %s (light=%d%%)\n", shouldBeOn ? "ON" : "OFF", lightLevel);
      StaticJsonDocument<128> s;
      s["pump"] = pumpState ? "on" : "off";
      s["light"] = lightRelayState ? "on" : "off";
      char buf[128];
      serializeJson(s, buf, sizeof(buf));
      mqttClient.publish(TOPIC_RELAY_STATE, buf, true);
    }
  }
}

// ========================================
// Publish Data
// ========================================

// Helper: publish a single sensor reading to farms/001/sensors/<type>/data
// Payload format required by fog validator: {sensor_type, value, timestamp, device_id}
static void publishSensor(const char *sensorType, float value, unsigned long ts)
{
  char topic[64];
  snprintf(topic, sizeof(topic), FARM_ID "/sensors/%s/data", sensorType);

  StaticJsonDocument<128> doc;
  doc["sensor_type"] = sensorType;
  doc["value"] = value;
  doc["timestamp"] = ts;
  doc["device_id"] = MQTT_CLIENT_ID;

  char payload[128];
  serializeJson(doc, payload, sizeof(payload));

  bool ok = mqttClient.publish(topic, payload);
  Serial.printf("  %s [%s] → %s\n", ok ? "OK" : "FAIL", topic, payload);
}

void publishData()
{
  if (!mqttClient.connected())
  {
    Serial.println("Cannot publish - MQTT not connected");
    return;
  }

  Serial.println("\n=== Publishing to MQTT ===");
  unsigned long ts = millis();

  // Publish individual sensor topics consumed by the fog node
  if (!isnan(temperature))
    publishSensor("temperature", temperature, ts);
  if (!isnan(humidity))
    publishSensor("humidity", humidity, ts);
  publishSensor("light", (float)lightLevel, ts);
  publishSensor("soil_moisture", (float)soilMoisture, ts);

  // Also publish combined payload for cloud/dashboard legacy consumers
  StaticJsonDocument<400> doc;
  doc["device_id"] = MQTT_CLIENT_ID;
  doc["farm_id"] = "farms/001";
  doc["timestamp"] = ts;
  doc["rssi"] = WiFi.RSSI();
  if (!isnan(temperature))
    doc["temperature"] = temperature;
  if (!isnan(humidity))
    doc["humidity"] = humidity;
  doc["light_level"] = lightLevel;
  doc["soil_moisture"] = soilMoisture;
  doc["raw_ldr"] = rawLDRVal;
  doc["raw_soil"] = rawSoilVal;
  doc["pump"] = pumpState ? "on" : "off";
  doc["light_relay"] = lightRelayState ? "on" : "off";
  doc["auto_mode"] = autoMode;
  doc["firmware_version"] = FIRMWARE_VERSION;

  String combined;
  serializeJson(doc, combined);
  bool ok = mqttClient.publish(TOPIC_SENSORS, combined.c_str());
  Serial.printf("  %s [%s] → %s\n", ok ? "OK" : "FAIL", TOPIC_SENSORS, combined.c_str());

  Serial.println("========================");
}

// ========================================
// SETUP
// ========================================
void setup()
{
  Serial.begin(115200);
  delay(2000);

  Serial.println("\n\n");
  Serial.println("========================================");
  Serial.println("   ESP32 Smart Farming - AgriTwin      ");
  Serial.printf("   Firmware v%s\n", FIRMWARE_VERSION);
  Serial.printf("   Built: %s\n", FIRMWARE_BUILD_DATE);
  Serial.println("========================================");
  Serial.println("LDR:   GPIO 33");
  Serial.println("DHT11: GPIO 4");
  Serial.println("RELAY PUMP:  GPIO 26");
  Serial.println("RELAY LIGHT: GPIO 25");
  Serial.printf("WiFi:  %s / %s / %s (multi)\n", WIFI1_SSID, WIFI2_SSID, WIFI3_SSID);
  Serial.printf("Broker: %s:%d\n", MQTT_BROKER, MQTT_PORT);
  Serial.println("AUTO:  Pump ON<30% OFF>=60%  Light ON<20% OFF>=50%");
  Serial.println("========================================\n");

  // Initialize sensors
  pinMode(LDR_PIN, INPUT);
  dht.begin();

  // Initialize relay pins — start OFF (HIGH for active-LOW relay modules)
  pinMode(RELAY_PUMP_PIN, OUTPUT);
  pinMode(RELAY_LIGHT_PIN, OUTPUT);
  digitalWrite(RELAY_PUMP_PIN, HIGH);  // pump OFF
  digitalWrite(RELAY_LIGHT_PIN, HIGH); // light OFF

  // Connect to WiFi
  setupWiFi();

  // Connect to MQTT
  if (WiFi.status() == WL_CONNECTED)
  {
    setupMQTT();
  }

  // ── OTA (Over-The-Air) firmware updates ──
  ArduinoOTA.setHostname("esp32-agritwin");
  ArduinoOTA.setPassword("CHANGE_ME_OTA_PASSWORD");
  ArduinoOTA.onStart([]()
                     {
    String type = (ArduinoOTA.getCommand() == U_FLASH) ? "firmware" : "filesystem";
    Serial.printf("[OTA] Start updating %s\n", type.c_str()); });
  ArduinoOTA.onEnd([]()
                   { Serial.println("\n[OTA] Update complete — rebooting."); });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total)
                        { Serial.printf("[OTA] Progress: %u%%\r", (progress / (total / 100))); });
  ArduinoOTA.onError([](ota_error_t error)
                     {
    Serial.printf("[OTA] Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed"); });
  ArduinoOTA.begin();
  Serial.println("[OTA] Ready (hostname: esp32-agritwin)");

  // ── Hardware Watchdog Timer ──
  esp_task_wdt_init(WDT_TIMEOUT_S, true); // true = panic (reset) on timeout
  esp_task_wdt_add(NULL);                 // subscribe main loop task
  Serial.printf("[WDT] Watchdog enabled (%ds timeout)\n", WDT_TIMEOUT_S);

  Serial.printf("\nSetup complete! Firmware v%s starting main loop...\n\n", FIRMWARE_VERSION);
}

// ========================================
// LOOP
// ========================================
void loop()
{
  unsigned long now = millis();

  // Feed the watchdog — must occur every WDT_TIMEOUT_S seconds or ESP32 resets
  esp_task_wdt_reset();

  // Handle OTA updates
  ArduinoOTA.handle();

  // Reconnect WiFi if needed (wifiMulti.run() handles re-scanning all networks)
  if (wifiMulti.run() != WL_CONNECTED)
  {
    Serial.println("WiFi disconnected! Reconnecting...");
    delay(500);
  }

  // Reconnect MQTT if needed
  if (WiFi.status() == WL_CONNECTED && !mqttClient.connected())
  {
    reconnectMQTT();
  }

  // Handle MQTT
  mqttClient.loop();

  // Read sensors (interval updated by Thompson Sampling fog command)
  if (now - lastRead >= readInterval)
  {
    readSensors();
    autoControl(); // apply threshold-based automation after fresh sensor data
    lastRead = now;
  }

  // Publish data (interval updated by Thompson Sampling fog command)
  if (now - lastPublish >= publishInterval)
  {
    publishData();
    lastPublish = now;
  }

  delay(10);
}
