"""
AgriTwin Real-Time Data Collector
Collects sensor data from ESP32 via MQTT and saves to CSV
"""

import paho.mqtt.client as mqtt
import json
import csv
from datetime import datetime
import os
from loguru import logger

# Configuration
MQTT_BROKER = "192.168.1.2"
MQTT_PORT = 1883
MQTT_TOPIC = "farm/001/device/+/sensors/data"
CSV_FILE = "sensor_data_real.csv"

# Create CSV file with headers if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp', 'device_id', 'farm_id', 
            'temperature', 'humidity', 'light_level',
            'rssi', 'free_heap', 'uptime'
        ])
    logger.info(f"Created new CSV file: {CSV_FILE}")

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        logger.success(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when message received"""
    try:
        # Parse JSON payload
        data = json.loads(msg.payload.decode())
        
        # Extract values
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        device_id = data.get('device_id', 'unknown')
        farm_id = 'farm_001'
        
        sensors = data.get('sensors', {})
        temperature = sensors.get('temperature', None)
        humidity = sensors.get('humidity', None)
        light_level = sensors.get('light_level', None)
        
        system = data.get('system', {})
        rssi = system.get('rssi', None)
        free_heap = system.get('free_heap', None)
        uptime = system.get('uptime', None)
        
        # Write to CSV
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, device_id, farm_id,
                temperature, humidity, light_level,
                rssi, free_heap, uptime
            ])
        
        # Print to console
        logger.info(
            f"{timestamp} | T:{temperature}°C H:{humidity}% L:{light_level}% | "
            f"RSSI:{rssi}dBm Heap:{free_heap}B"
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        logger.warning(f"Unexpected disconnection (code {rc}). Reconnecting...")

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Start collection
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AgriTwin Real-Time Data Collector")
    logger.info("=" * 60)
    logger.info(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Topic: {MQTT_TOPIC}")
    logger.info(f"Output File: {CSV_FILE}")
    logger.info("=" * 60)
    logger.info("Starting data collection...")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("\nStopping data collection...")
        client.disconnect()
        logger.success(f"Data saved to: {CSV_FILE}")
    except Exception as e:
        logger.error(f"Connection error: {e}")
        logger.info("Make sure:")
        logger.info("1. MQTT broker is running")
        logger.info("2. ESP32 is connected and publishing")
        logger.info("3. Network connectivity is available")
