# Psychrometric parameters data class

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PsychrometricParameters:
    """
    Complete set of psychrometric parameters
    
    Based on Paper 10: These 6 derived parameters provide
    comprehensive climate understanding
    """
    # Input parameters
    temperature: float  # °C
    relative_humidity: float  # %
    pressure: float = 101.325  # kPa
    
    # Calculated parameters
    dew_point: float = None  # °C
    wet_bulb_temperature: float = None  # °C
    absolute_humidity: float = None  # g/m³
    specific_enthalpy: float = None  # kJ/kg
    vapor_pressure: float = None  # kPa
    specific_volume: float = None  # m³/kg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "input": {
                "temperature": self.temperature,
                "relative_humidity": self.relative_humidity,
                "pressure": self.pressure
            },
            "calculated": {
                "dew_point": self.dew_point,
                "wet_bulb_temperature": self.wet_bulb_temperature,
                "absolute_humidity": self.absolute_humidity,
                "specific_enthalpy": self.specific_enthalpy,
                "vapor_pressure": self.vapor_pressure,
                "specific_volume": self.specific_volume
            }
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = []
        lines.append("Psychrometric Parameters:")
        lines.append(f"  Temperature: {self.temperature:.1f}°C")
        lines.append(f"  Relative Humidity: {self.relative_humidity:.1f}%")
        lines.append(f"  Dew Point: {self.dew_point:.1f}°C")
        lines.append(f"  Wet Bulb: {self.wet_bulb_temperature:.1f}°C")
        lines.append(f"  Absolute Humidity: {self.absolute_humidity:.2f} g/m³")
        lines.append(f"  Enthalpy: {self.specific_enthalpy:.1f} kJ/kg")
        return "\n".join(lines)
