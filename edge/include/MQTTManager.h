/**
 * @file MQTTManager.h
 * @brief MQTT connection and publish/subscribe management
 */

#ifndef MQTT_MANAGER_H
#define MQTT_MANAGER_H

#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"
#include "mqtt_topics.h"

typedef void (*MQTTMessageCallback)(String topic, String payload);

class MQTTManager
{
private:
  PubSubClient &client;
  MQTTMessageCallback messageCallback;
  unsigned long lastReconnectAttempt;
  int reconnectAttempts;

public:
  MQTTManager(PubSubClient &mqttClient)
      : client(mqttClient), messageCallback(nullptr),
        lastReconnectAttempt(0), reconnectAttempts(0) {}

  void setCallback(MQTTMessageCallback callback)
  {
    messageCallback = callback;
  }

  void handleMessage(char *topic, byte *payload, unsigned int length)
  {
    if (messageCallback != nullptr)
    {
      String topicStr = String(topic);
      String payloadStr = "";
      for (unsigned int i = 0; i < length; i++)
      {
        payloadStr += (char)payload[i];
      }
      messageCallback(topicStr, payloadStr);
    }
  }

  bool connect()
  {
    if (client.connected())
    {
      return true;
    }

    Serial.print("Connecting to MQTT broker ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.print(MQTT_PORT);
    Serial.print(" ... ");

    String clientId = String(MQTT_CLIENT_ID) + "_" + String(ESP.getEfuseMac(), HEX);

    bool connected = false;
    if (strlen(MQTT_USERNAME) > 0)
    {
      connected = client.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD);
    }
    else
    {
      connected = client.connect(clientId.c_str());
    }

    if (connected)
    {
      Serial.println("✓ Connected!");
      reconnectAttempts = 0;

      // Subscribe to command topics
      subscribeToTopics();

      return true;
    }
    else
    {
      Serial.print("✗ Failed! RC=");
      Serial.println(client.state());
      reconnectAttempts++;
      return false;
    }
  }

  void subscribeToTopics()
  {
    // Subscribe to device-specific commands
    String commandTopic = String(MQTT_TOPIC_COMMANDS) + "/" + FARM_ID + "/" + MQTT_CLIENT_ID;
    client.subscribe(commandTopic.c_str());
    Serial.printf("Subscribed to: %s\n", commandTopic.c_str());

    // Subscribe to broadcast commands
    String broadcastTopic = String(MQTT_TOPIC_COMMANDS) + "/" + FARM_ID + "/all";
    client.subscribe(broadcastTopic.c_str());
    Serial.printf("Subscribed to: %s\n", broadcastTopic.c_str());
  }

  bool publish(const char *topic, const char *payload, bool retained = false)
  {
    if (!client.connected())
    {
      Serial.println("MQTT not connected, cannot publish");
      return false;
    }

    bool success = client.publish(topic, payload, retained);
    if (success)
    {
      Serial.printf("Published to %s\n", topic);
    }
    else
    {
      Serial.printf("Failed to publish to %s\n", topic);
    }
    return success;
  }

  bool publishJson(const char *topic, JsonDocument &doc, bool retained = false)
  {
    String payload;
    serializeJson(doc, payload);
    return publish(topic, payload.c_str(), retained);
  }

  void loop()
  {
    if (!client.connected())
    {
      unsigned long now = millis();
      if (now - lastReconnectAttempt > 5000)
      {
        lastReconnectAttempt = now;
        if (reconnectAttempts < MQTT_MAX_RETRIES)
        {
          connect();
        }
      }
    }
    else
    {
      client.loop();
    }
  }

  bool isConnected()
  {
    return client.connected();
  }

  int getReconnectAttempts()
  {
    return reconnectAttempts;
  }
};

#endif
