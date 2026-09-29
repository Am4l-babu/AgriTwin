/**
 * @file OTAManager.h
 * @brief Over-The-Air firmware update manager
 */

#ifndef OTA_MANAGER_H
#define OTA_MANAGER_H

#include <Arduino.h>
#include <ArduinoOTA.h>
#include <HTTPUpdate.h>

class OTAManager {
private:
    String hostname;
    bool otaEnabled;
    
    static void onStart();
    static void onEnd();
    static void onProgress(unsigned int progress, unsigned int total);
    static void onError(ota_error_t error);
    
public:
    OTAManager();
    
    void begin(String deviceHostname);
    void handle();
    
    bool updateFromURL(String firmwareURL);
    void disable();
};

#endif
