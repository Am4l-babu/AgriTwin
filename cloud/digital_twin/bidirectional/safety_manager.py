# Safety manager - Safety checks for actuation

from typing import Dict, Any, List
from datetime import datetime
from enum import Enum


class SafetyLevel(Enum):
    """Safety check severity levels"""
    SAFE = "safe"
    WARNING = "warning"
    UNSAFE = "unsafe"
    CRITICAL = "critical"


class SafetyManager:
    """
    Safety checks before actuating physical devices
    
    Prevents:
    - Over-irrigation
    - Excessive fertilization
    - Dangerous temperature conditions
    - System failures
    """
    
    def __init__(self):
        self.safety_rules = self._initialize_safety_rules()
        self.safety_log: List[Dict] = []
    
    def _initialize_safety_rules(self) -> Dict[str, Any]:
        """Initialize safety rules"""
        return {
            "irrigation": {
                "max_daily_amount": 50,  # mm
                "max_single_duration": 3600,  # seconds
                "min_soil_moisture_for_irrigation": 20,  # %
                "max_soil_moisture_for_irrigation": 80  # %
            },
            "fertilization": {
                "max_daily_amount": 200,  # kg/ha
                "min_interval_hours": 24,
                "max_applications_per_week": 2
            },
            "temperature": {
                "min_safe_temp": 5,  # °C
                "max_safe_temp": 45,  # °C
                "critical_low": 0,  # °C (frost)
                "critical_high": 50  # °C (heat damage)
            }
        }
    
    def check_irrigation_safety(self, duration: int, current_soil_moisture: float,
                               daily_total: float = 0) -> Dict[str, Any]:
        """
        Check if irrigation is safe
        
        Args:
            duration: Proposed irrigation duration (seconds)
            current_soil_moisture: Current soil moisture (%)
            daily_total: Total irrigation today (mm)
        """
        rules = self.safety_rules["irrigation"]
        issues = []
        warnings = []
        
        # Check duration
        if duration > rules["max_single_duration"]:
            issues.append(f"Duration {duration}s exceeds max {rules['max_single_duration']}s")
        
        # Check soil moisture
        if current_soil_moisture < rules["min_soil_moisture_for_irrigation"]:
            warnings.append(f"Soil very dry ({current_soil_moisture}%) - irrigation recommended")
        elif current_soil_moisture > rules["max_soil_moisture_for_irrigation"]:
            issues.append(f"Soil already wet ({current_soil_moisture}%) - irrigation not needed")
        
        # Check daily total
        estimated_amount = duration / 60 * 0.5  # Rough estimate: 0.5mm per minute
        if daily_total + estimated_amount > rules["max_daily_amount"]:
            issues.append(f"Would exceed daily limit ({rules['max_daily_amount']}mm)")
        
        # Determine safety level
        if issues:
            level = SafetyLevel.UNSAFE
        elif warnings:
            level = SafetyLevel.WARNING
        else:
            level = SafetyLevel.SAFE
        
        result = {
            "safe": level in [SafetyLevel.SAFE, SafetyLevel.WARNING],
            "level": level.value,
            "issues": issues,
            "warnings": warnings,
            "recommendation": self._get_recommendation(level, "irrigation")
        }
        
        self._log_safety_check("irrigation", result)
        return result
    
    def check_temperature_safety(self, current_temp: float) -> Dict[str, Any]:
        """
        Check if temperature is safe for operations
        """
        rules = self.safety_rules["temperature"]
        issues = []
        warnings = []
        
        if current_temp <= rules["critical_low"]:
            issues.append(f"CRITICAL: Frost risk at {current_temp}°C")
            level = SafetyLevel.CRITICAL
        elif current_temp >= rules["critical_high"]:
            issues.append(f"CRITICAL: Extreme heat at {current_temp}°C")
            level = SafetyLevel.CRITICAL
        elif current_temp < rules["min_safe_temp"]:
            warnings.append(f"Low temperature: {current_temp}°C")
            level = SafetyLevel.WARNING
        elif current_temp > rules["max_safe_temp"]:
            warnings.append(f"High temperature: {current_temp}°C")
            level = SafetyLevel.WARNING
        else:
            level = SafetyLevel.SAFE
        
        return {
            "safe": level != SafetyLevel.CRITICAL,
            "level": level.value,
            "issues": issues,
            "warnings": warnings,
            "current_temperature": current_temp
        }
    
    def check_system_health(self, device_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if device is healthy enough for actuation
        """
        issues = []
        warnings = []
        
        # Check battery
        battery = device_status.get("battery_level")
        if battery is not None:
            if battery < 10:
                issues.append(f"Critical battery: {battery}%")
            elif battery < 20:
                warnings.append(f"Low battery: {battery}%")
        
        # Check signal
        rssi = device_status.get("rssi")
        if rssi is not None:
            if rssi < -90:
                issues.append(f"Very weak signal: {rssi} dBm")
            elif rssi < -80:
                warnings.append(f"Weak signal: {rssi} dBm")
        
        # Check memory
        free_heap = device_status.get("free_heap")
        if free_heap is not None:
            if free_heap < 10000:
                warnings.append(f"Low memory: {free_heap} bytes")
        
        level = SafetyLevel.UNSAFE if issues else (
            SafetyLevel.WARNING if warnings else SafetyLevel.SAFE
        )
        
        return {
            "safe": level != SafetyLevel.UNSAFE,
            "level": level.value,
            "issues": issues,
            "warnings": warnings
        }
    
    def _get_recommendation(self, level: SafetyLevel, action: str) -> str:
        """Get safety recommendation"""
        recommendations = {
            (SafetyLevel.SAFE, "irrigation"): "Safe to proceed",
            (SafetyLevel.WARNING, "irrigation"): "Proceed with caution",
            (SafetyLevel.UNSAFE, "irrigation"): "Do not irrigate",
            (SafetyLevel.CRITICAL, "irrigation"): "STOP - Critical condition"
        }
        return recommendations.get((level, action), "Review conditions")
    
    def _log_safety_check(self, check_type: str, result: Dict[str, Any]):
        """Log safety check for audit"""
        self.safety_log.append({
            "timestamp": datetime.now().isoformat(),
            "check_type": check_type,
            "result": result
        })
    
    def get_safety_log(self, limit: int = 100) -> List[Dict]:
        """Get recent safety checks"""
        return self.safety_log[-limit:]
