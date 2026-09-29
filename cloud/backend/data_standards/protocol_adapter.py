# Protocol adapter - Convert AgriTwin format to standard format

from typing import Dict, List, Any
from datetime import datetime
from .schemas import StandardSensorReading, SensorType, DataQuality


class StandardProtocol:
    """
    Convert between AgriTwin format and universal standard format
    """
    
    @staticmethod
    def from_agritwin_format(mqtt_data: Dict[str, Any]) -> List[StandardSensorReading]:
        """
        Convert AgriTwin MQTT message to standard format
        
        Input (AgriTwin format):
        {
            "device_id": "ESP32_001",
            "timestamp": 1234567890,
            "sensors": {
                "temperature": 28.5,
                "humidity": 65,
                "light_level": 42
            },
            "system": {
                "rssi": -45,
                "free_heap": 123456,
                "uptime": 3600
            }
        }
        
        Output: List of StandardSensorReading objects
        """
        readings = []
        device_id = mqtt_data.get("device_id", "unknown")
        timestamp_ms = mqtt_data.get("timestamp", 0)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)
        
        sensors = mqtt_data.get("sensors", {})
        system = mqtt_data.get("system", {})
        
        # Map AgriTwin sensor names to standard types
        sensor_mapping = {
            "temperature": (SensorType.TEMPERATURE, "celsius"),
            "humidity": (SensorType.HUMIDITY, "percent"),
            "light_level": (SensorType.LIGHT, "percent"),
            "soil_moisture": (SensorType.SOIL_MOISTURE, "percent")
        }
        
        # Convert each sensor reading
        for sensor_name, value in sensors.items():
            if sensor_name in sensor_mapping:
                sensor_type, unit = sensor_mapping[sensor_name]
                
                reading = StandardSensorReading(
                    farm_id="farm_001",  # Default farm ID
                    device_id=device_id,
                    sensor_id=f"{device_id}_{sensor_name}",
                    sensor_type=sensor_type,
                    value=value,
                    unit=unit,
                    timestamp=timestamp,
                    quality=StandardProtocol._assess_quality(value, sensor_type),
                    signal_strength=system.get("rssi"),
                    metadata={
                        "free_heap": system.get("free_heap"),
                        "uptime": system.get("uptime")
                    }
                )
                readings.append(reading)
        
        return readings
    
    @staticmethod
    def to_agritwin_format(readings: List[StandardSensorReading]) -> Dict[str, Any]:
        """
        Convert standard format back to AgriTwin format
        """
        if not readings:
            return {}
        
        # Group by device
        device_id = readings[0].device_id
        timestamp = int(readings[0].timestamp.timestamp() * 1000)
        
        sensors = {}
        system = {}
        
        for reading in readings:
            # Map standard type back to AgriTwin name
            sensor_name = {
                SensorType.TEMPERATURE: "temperature",
                SensorType.HUMIDITY: "humidity",
                SensorType.LIGHT: "light_level",
                SensorType.SOIL_MOISTURE: "soil_moisture"
            }.get(reading.sensor_type)
            
            if sensor_name:
                sensors[sensor_name] = reading.value
            
            # Extract system info from first reading
            if reading.signal_strength:
                system["rssi"] = reading.signal_strength
            if reading.metadata.get("free_heap"):
                system["free_heap"] = reading.metadata["free_heap"]
            if reading.metadata.get("uptime"):
                system["uptime"] = reading.metadata["uptime"]
        
        return {
            "device_id": device_id,
            "timestamp": timestamp,
            "sensors": sensors,
            "system": system
        }
    
    @staticmethod
    def _assess_quality(value: float, sensor_type: SensorType) -> DataQuality:
        """
        Assess data quality based on value and sensor type
        """
        # Check if value is within expected range
        ranges = {
            SensorType.TEMPERATURE: (-40, 80),
            SensorType.HUMIDITY: (0, 100),
            SensorType.SOIL_MOISTURE: (0, 100),
            SensorType.LIGHT: (0, 100),
            SensorType.PH: (0, 14),
            SensorType.EC: (0, 10)
        }
        
        if sensor_type in ranges:
            min_val, max_val = ranges[sensor_type]
            if min_val <= value <= max_val:
                return DataQuality.GOOD
            else:
                return DataQuality.INVALID
        
        return DataQuality.GOOD
