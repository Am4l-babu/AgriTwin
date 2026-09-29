"""
Realistic ESP32 Sensor Data Simulator
Simulates realistic sensor readings with natural variations and day/night cycles
"""
import paho.mqtt.client as mqtt
import json
import time
import math
from datetime import datetime

class SensorSimulator:
    def __init__(self):
        # Base values with realistic ranges
        self.time_offset = 0
        self.soil_moisture = 45.0  # Starting soil moisture
        
    def get_realistic_readings(self):
        """Generate realistic sensor readings with natural patterns"""
        
        # Simulate time of day (0-24 hours cycle, accelerated)
        self.time_offset += 0.1
        hour_of_day = (self.time_offset % 24)
        
        # Temperature: varies with time of day (cooler at night, warmer during day)
        # Range: 18°C (night) to 32°C (midday)
        temp_base = 25.0
        temp_variation = 7.0 * math.sin((hour_of_day - 6) * math.pi / 12)
        temperature = round(temp_base + temp_variation + (math.sin(self.time_offset) * 0.5), 1)
        temperature = max(18.0, min(35.0, temperature))
        
        # Humidity: inversely related to temperature
        # Range: 40% (hot day) to 85% (cool night)
        humidity_base = 65.0
        humidity_variation = -15.0 * math.sin((hour_of_day - 6) * math.pi / 12)
        humidity = round(humidity_base + humidity_variation + (math.cos(self.time_offset * 1.3) * 3), 1)
        humidity = max(35.0, min(90.0, humidity))
        
        # Light level: follows day/night cycle
        # 0% at night, 100% at noon
        if 6 <= hour_of_day <= 18:  # Daytime
            light_base = 50.0 * (1 + math.sin((hour_of_day - 6) * math.pi / 12))
            light_level = round(light_base + (math.sin(self.time_offset * 2) * 5), 0)
        else:  # Nighttime
            light_level = round(5.0 + (math.sin(self.time_offset * 3) * 3), 0)
        light_level = max(0, min(100, int(light_level)))
        
        # Soil moisture: slowly decreases during day, can increase with "watering"
        # Simulate gradual water loss during day, slower at night
        if 8 <= hour_of_day <= 16:  # More evaporation during day
            self.soil_moisture -= 0.05
        else:
            self.soil_moisture -= 0.01
        
        # Simulate occasional watering
        if self.soil_moisture < 30:  # Auto-irrigation trigger
            self.soil_moisture += 5.0
        
        # Add small random variation
        soil_moisture = round(self.soil_moisture + (math.sin(self.time_offset * 0.5) * 2), 1)
        soil_moisture = max(25.0, min(70.0, soil_moisture))
        
        return {
            "temperature": temperature,
            "humidity": humidity,
            "light_level": light_level,
            "soil_moisture": soil_moisture,
            "hour_of_day": round(hour_of_day, 1)
        }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"\u2713 Connected to MQTT Broker ({MQTT_BROKER}:1883)")
        print("✓ Publishing realistic sensor data")
        print("=" * 70)
    else:
        print(f"✗ Failed to connect, return code {rc}")

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect

# Create simulator
simulator = SensorSimulator()

try:
    print("\n🌱 Smart Farming - Realistic Sensor Simulator")
    print("=" * 70)
    print("Connecting to MQTT broker...")
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()
    
    time.sleep(1)
    
    print("\n📊 Simulating ESP32 sensor data with natural patterns:")
    print("   • Temperature: Day/night cycle (18-32°C)")
    print("   • Humidity: Inverse to temperature (40-85%)")
    print("   • Light: Solar cycle (0-100%)")
    print("   • Soil Moisture: Gradual depletion + auto-watering (25-70%)")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 70)
    
    count = 0
    while True:
        # Get realistic readings
        readings = simulator.get_realistic_readings()
        
        # Create ESP32-format message
        sensor_data = {
            "device_id": "esp32_device_001",
            "timestamp": int(time.time()),
            "sensors": {
                "temperature": readings["temperature"],
                "humidity": readings["humidity"],
                "light_level": readings["light_level"],
                "soil_moisture": readings["soil_moisture"]
            }
        }
        
        # Publish to the topic the backend listens to
        topic = "farm/001/device/001/sensors/data"
        payload = json.dumps(sensor_data)
        
        result = client.publish(topic, payload)
        
        count += 1
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            time_of_day = "🌅 Dawn" if 5 <= readings["hour_of_day"] < 8 else \
                         "☀️ Day" if 8 <= readings["hour_of_day"] < 17 else \
                         "🌇 Dusk" if 17 <= readings["hour_of_day"] < 20 else \
                         "🌙 Night"
            
            print(f"#{count:03d} [{time_of_day}] " + 
                  f"🌡️ {readings['temperature']:4.1f}°C  " +
                  f"💧 {readings['humidity']:4.1f}%  " +
                  f"☀️ {readings['light_level']:3d}%  " +
                  f"🌱 {readings['soil_moisture']:4.1f}%")
        
        time.sleep(5)  # Update every 5 seconds
        
except KeyboardInterrupt:
    print("\n\n" + "=" * 70)
    print("⏹️  Stopping sensor simulator...")
except Exception as e:
    print(f"\n✗ Error: {e}")
finally:
    client.loop_stop()
    client.disconnect()
    print("✓ Disconnected from MQTT broker")
    print("=" * 70)
