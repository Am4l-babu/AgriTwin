"""
Data Validator

Validates incoming sensor data against schemas and business rules.
"""

from typing import Tuple, List, Dict, Any
from loguru import logger


class DataValidator:
    """
    Validates sensor data and other incoming messages
    """
    
    def __init__(self, settings):
        self.settings = settings
        
        # Define sensor value ranges
        self.sensor_ranges = {
            "soil_moisture": {"min": 0.0, "max": 100.0, "unit": "%"},
            "temperature": {"min": -40.0, "max": 80.0, "unit": "°C"},
            "humidity": {"min": 0.0, "max": 100.0, "unit": "%"},
            "ph": {"min": 0.0, "max": 14.0, "unit": "pH"},
            "light": {"min": 0.0, "max": 100000.0, "unit": "lux"},
            "ec": {"min": 0.0, "max": 10.0, "unit": "mS/cm"},
        }
    
    def validate_sensor_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate sensor data payload
        
        Returns:
            (is_valid, list of errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["sensor_type", "value", "timestamp"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate sensor type
        sensor_type = data.get("sensor_type")
        if sensor_type not in self.sensor_ranges:
            errors.append(f"Unknown sensor type: {sensor_type}")
            return False, errors
        
        # Validate value range
        value = data.get("value")
        if not isinstance(value, (int, float)):
            errors.append(f"Value must be numeric, got {type(value)}")
            return False, errors
        
        range_config = self.sensor_ranges[sensor_type]
        if not (range_config["min"] <= value <= range_config["max"]):
            errors.append(
                f"Value {value} out of range [{range_config['min']}, {range_config['max']}]"
            )
        
        # Validate timestamp
        timestamp = data.get("timestamp")
        if not isinstance(timestamp, (int, float)):
            errors.append(f"Timestamp must be numeric, got {type(timestamp)}")
        
        # Data is valid if no errors
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.debug(f"Validation errors: {errors}")
        
        return is_valid, errors
    
    def validate_status_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate device status payload"""
        errors = []
        
        required_fields = ["device_id", "timestamp"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize and normalize data
        """
        # Remove any unexpected fields
        # Add data enrichment
        # Normalize timestamps
        return data
