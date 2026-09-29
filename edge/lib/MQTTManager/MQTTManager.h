/**
 * @file MQTTManager.h
 * @brief MQTT communication wrapper with reconnection logic
 */

#ifndef MQTT_MANAGER_H
#define MQTT_MANAGER_H

#include <Arduino.h>
#include <PubSubClient.h>

class MQTTManager {
private:
    PubSubClient& client;
    String farmId;
    
public:
    MQTTManager(PubSubClient& mqttClient);
    
    void setFarmId(String id);
    String buildTopic(String baseTopic, String subTopic = "");
    
    bool publish(String topic, String payload, bool retained = false);
    bool publishJSON(String topic, StaticJsonDocument<512>& doc, bool retained = false);
    
    bool subscribe(String topic);
    void unsubscribe(String topic);
};

#endif
