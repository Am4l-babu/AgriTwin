# Data validator - Quality checks and validation

from typing import Dict, Any
from .schemas import StandardSensorReading, SensorType, DataQuality


class DataValidator:
    """
    Validate sensor data quality
    """
    
    # Valid ranges for each sensor type
    VALID_RANGES = {
        SensorType.TEMPERATURE: (-40.0, 80.0),
        SensorType.HUMIDITY: (0.0, 100.0),
        SensorType.SOIL_MOISTURE: (0.0, 100.0),
        SensorType.LIGHT: (0.0, 100.0),
        SensorType.PH: (0.0, 14.0),
        SensorType.EC: (0.0, 10.0),
        SensorType.PRESSURE: (800.0, 1200.0),  # hPa
        SensorType.CO2: (300.0, 5000.0),  # ppm
        SensorType.WIND_SPEED: (0.0, 50.0),  # m/s
        SensorType.RAINFALL: (0.0, 500.0)  # mm
    }
    
    @staticmethod
    def validate(reading: StandardSensorReading) -> Dict[str, Any]:
        """
        Validate a sensor reading
        
        Returns:
        {
            "valid": bool,
            "quality_score": float (0-100),
            "issues": List[str],
            "warnings": List[str]
        }
        """
        issues = []
        warnings = []
        quality_score = 100.0
        
        # Check 1: Value in valid range
        if reading.sensor_type in DataValidator.VALID_RANGES:
            min_val, max_val = DataValidator.VALID_RANGES[reading.sensor_type]
            if not (min_val <= reading.value <= max_val):
                issues.append(f"Value {reading.value} outside valid range [{min_val}, {max_val}]")
                quality_score -= 50
        
        # Check 2: Confidence level
        if reading.confidence < 0.5:
            warnings.append(f"Low confidence: {reading.confidence}")
            quality_score -= 20
        
        # Check 3: Signal strength (if available)
        if reading.signal_strength is not None:
            if reading.signal_strength < -80:  # dBm
                warnings.append(f"Weak signal: {reading.signal_strength} dBm")
                quality_score -= 10
        
        # Check 4: Timestamp freshness
        from datetime import datetime, timedelta
        age = datetime.now() - reading.timestamp
        if age > timedelta(hours=1):
            warnings.append(f"Stale data: {age.total_seconds()/3600:.1f} hours old")
            quality_score -= 15
        
        # Check 5: Calibration offset
        if abs(reading.calibration_offset) > 10:
            warnings.append(f"Large calibration offset: {reading.calibration_offset}")
            quality_score -= 5
        
        quality_score = max(0, quality_score)
        
        return {
            "valid": len(issues) == 0,
            "quality_score": quality_score,
            "issues": issues,
            "warnings": warnings,
            "recommended_quality": DataValidator._score_to_quality(quality_score)
        }
    
    @staticmethod
    def _score_to_quality(score: float) -> DataQuality:
        """Convert quality score to quality enum"""
        if score >= 95:
            return DataQuality.EXCELLENT
        elif score >= 80:
            return DataQuality.GOOD
        elif score >= 60:
            return DataQuality.FAIR
        elif score >= 40:
            return DataQuality.POOR
        else:
            return DataQuality.INVALID
    
    @staticmethod
    def validate_batch(readings: list) -> Dict[str, Any]:
        """Validate a batch of readings"""
        results = [DataValidator.validate(r) for r in readings]
        
        valid_count = sum(1 for r in results if r["valid"])
        avg_quality = sum(r["quality_score"] for r in results) / len(results) if results else 0
        
        return {
            "total_readings": len(readings),
            "valid_readings": valid_count,
            "invalid_readings": len(readings) - valid_count,
            "average_quality_score": avg_quality,
            "individual_results": results
        }
