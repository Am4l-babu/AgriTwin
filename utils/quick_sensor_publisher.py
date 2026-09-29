"""
Quick MQTT Test Publisher
Simulates ESP32 sensor data to test dashboard.

Publishes to the MQTT broker on the Raspberry Pi fog node.
Run this from any machine on the same WiFi network.

Usage:
    python quick_sensor_publisher.py
    MQTT_BROKER=agritwin-fog.local python quick_sensor_publisher.py
"""

import os
import paho.mqtt.client as mqtt
import json
import time
import random

# Use agritwin-fog.local to reach the Raspberry Pi MQTT broker via mDNS.
# Override with MQTT_BROKER env var if needed.
MQTT_BROKER = os.environ.get("MQTT_BROKER", "agritwin-fog.local")
MQTT_PORT = 1883
TOPIC = "farm/001/device/001/sensors/data"

def publish_sensor_data():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    print(f"Publishing to {TOPIC} every 3 seconds...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            data = {
                "device_id": "esp32_edge_001",
                "timestamp": int(time.time()),
                "sensors": {
                    "temperature": round(25 + random.uniform(-2, 5), 1),
                    "humidity": round(40 + random.uniform(-10, 30), 0),
                    "light_level": round(200 + random.uniform(-50, 200), 0),
                    "soil_moisture": round(random.uniform(30, 70), 0)
                },
                "system": {
                    "rssi": -45,
                    "free_heap": 240000,
                    "uptime": int(time.time())
                }
            }
            
            payload = json.dumps(data)
            client.publish(TOPIC, payload)
            print(f"📡 Published: Temp={data['sensors']['temperature']}°C, Humidity={data['sensors']['humidity']}%")
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    publish_sensor_data()
