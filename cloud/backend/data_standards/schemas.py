# Standard data schemas for universal interoperability
# Based on ISO/IEC 30173 Digital Twin standards

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SensorType(Enum):
    """Standard sensor types"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SOIL_MOISTURE = "soil_moisture"
    LIGHT = "light"
    PH = "ph"
    EC = "electrical_conductivity"
    PRESSURE = "pressure"
    CO2 = "co2"
    WIND_SPEED = "wind_speed"
    RAINFALL = "rainfall"


class DataQuality(Enum):
    """Data quality indicators"""
    EXCELLENT = "excellent"  # <2% error
    GOOD = "good"  # 2-5% error
    FAIR = "fair"  # 5-10% error
    POOR = "poor"  # >10% error
    INVALID = "invalid"  # Failed validation


@dataclass
class StandardSensorReading:
    """
    Universal sensor reading format
    Compatible with any Digital Twin system
    """
    # Core identification
    farm_id: str
    device_id: str
    sensor_id: str
    sensor_type: SensorType
    
    # Measurement
    value: float
    unit: str
    timestamp: datetime
    
    # Quality & metadata
    quality: DataQuality = DataQuality.GOOD
    confidence: float = 1.0  # 0.0 to 1.0
    calibration_offset: float = 0.0
    
    # Location (optional)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[float] = None
    
    # System metadata
    firmware_version: Optional[str] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[int] = None
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "farm_id": self.farm_id,
            "device_id": self.device_id,
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "quality": self.quality.value,
            "confidence": self.confidence,
            "calibration_offset": self.calibration_offset,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation": self.elevation,
            "firmware_version": self.firmware_version,
            "battery_level": self.battery_level,
            "signal_strength": self.signal_strength,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardSensorReading':
        """Create from dictionary"""
        return cls(
            farm_id=data["farm_id"],
            device_id=data["device_id"],
            sensor_id=data["sensor_id"],
            sensor_type=SensorType(data["sensor_type"]),
            value=data["value"],
            unit=data["unit"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            quality=DataQuality(data.get("quality", "good")),
            confidence=data.get("confidence", 1.0),
            calibration_offset=data.get("calibration_offset", 0.0),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            elevation=data.get("elevation"),
            firmware_version=data.get("firmware_version"),
            battery_level=data.get("battery_level"),
            signal_strength=data.get("signal_strength"),
            metadata=data.get("metadata", {})
        )
