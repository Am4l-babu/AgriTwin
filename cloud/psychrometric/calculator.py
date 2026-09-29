# Psychrometric calculator
# Based on Paper 10: Calculate 6 derived parameters from temp + humidity

import math
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PsychrometricParameters:
    """Complete psychrometric parameters"""
    # Input parameters
    temperature: float  # °C
    relative_humidity: float  # %
    pressure: float = 101.325  # kPa (standard atmospheric pressure)
    
    # Calculated parameters
    dew_point: float = None  # °C
    wet_bulb_temperature: float = None  # °C
    absolute_humidity: float = None  # g/m³
    specific_enthalpy: float = None  # kJ/kg
    vapor_pressure: float = None  # kPa
    specific_volume: float = None  # m³/kg


class PsychrometricCalculator:
    """
    Calculate psychrometric parameters from temperature and humidity
    
    Based on Paper 10: 6 derived parameters provide comprehensive
    climate understanding for precision agriculture
    
    Parameters calculated:
    1. Dew Point Temperature
    2. Wet Bulb Temperature
    3. Absolute Humidity
    4. Specific Enthalpy
    5. Vapor Pressure
    6. Specific Volume
    """
    
    @staticmethod
    def calculate_all(temperature: float, relative_humidity: float,
                     pressure: float = 101.325) -> PsychrometricParameters:
        """
        Calculate all psychrometric parameters
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
            pressure: Atmospheric pressure (kPa)
        
        Returns:
            Complete psychrometric parameters
        """
        params = PsychrometricParameters(
            temperature=temperature,
            relative_humidity=relative_humidity,
            pressure=pressure
        )
        
        # Calculate each parameter
        params.vapor_pressure = PsychrometricCalculator.vapor_pressure(
            temperature, relative_humidity
        )
        params.dew_point = PsychrometricCalculator.dew_point(
            temperature, relative_humidity
        )
        params.wet_bulb_temperature = PsychrometricCalculator.wet_bulb_temperature(
            temperature, relative_humidity, pressure
        )
        params.absolute_humidity = PsychrometricCalculator.absolute_humidity(
            temperature, relative_humidity, pressure
        )
        params.specific_enthalpy = PsychrometricCalculator.specific_enthalpy(
            temperature, relative_humidity, pressure
        )
        params.specific_volume = PsychrometricCalculator.specific_volume(
            temperature, pressure
        )
        
        return params
    
    @staticmethod
    def saturation_vapor_pressure(temperature: float) -> float:
        """
        Calculate saturation vapor pressure using Magnus formula
        
        Args:
            temperature: Air temperature (°C)
        
        Returns:
            Saturation vapor pressure (kPa)
        """
        # Magnus formula
        return 0.61094 * math.exp((17.625 * temperature) / (temperature + 243.04))
    
    @staticmethod
    def vapor_pressure(temperature: float, relative_humidity: float) -> float:
        """
        Calculate actual vapor pressure
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
        
        Returns:
            Vapor pressure (kPa)
        """
        es = PsychrometricCalculator.saturation_vapor_pressure(temperature)
        return (relative_humidity / 100.0) * es
    
    @staticmethod
    def dew_point(temperature: float, relative_humidity: float) -> float:
        """
        Calculate dew point temperature
        
        The temperature at which air becomes saturated and dew forms
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
        
        Returns:
            Dew point temperature (°C)
        """
        # Constants for Magnus formula
        a = 17.625
        b = 243.04
        
        # Calculate alpha
        alpha = math.log(relative_humidity / 100.0) + (a * temperature) / (b + temperature)
        
        # Calculate dew point
        dew_point = (b * alpha) / (a - alpha)
        
        return dew_point
    
    @staticmethod
    def wet_bulb_temperature(temperature: float, relative_humidity: float,
                            pressure: float = 101.325) -> float:
        """
        Calculate wet bulb temperature (approximation)
        
        The temperature a parcel of air would have if cooled to saturation
        by evaporation of water into it
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
            pressure: Atmospheric pressure (kPa)
        
        Returns:
            Wet bulb temperature (°C)
        """
        # Simplified Stull formula
        tw = temperature * math.atan(0.151977 * math.sqrt(relative_humidity + 8.313659)) + \
             math.atan(temperature + relative_humidity) - \
             math.atan(relative_humidity - 1.676331) + \
             0.00391838 * (relative_humidity ** 1.5) * math.atan(0.023101 * relative_humidity) - \
             4.686035
        
        return tw
    
    @staticmethod
    def absolute_humidity(temperature: float, relative_humidity: float,
                         pressure: float = 101.325) -> float:
        """
        Calculate absolute humidity (water vapor density)
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
            pressure: Atmospheric pressure (kPa)
        
        Returns:
            Absolute humidity (g/m³)
        """
        # Vapor pressure
        e = PsychrometricCalculator.vapor_pressure(temperature, relative_humidity)
        
        # Absolute humidity using ideal gas law
        # AH = (e * 1000) / (461.5 * (T + 273.15))
        # where 461.5 is specific gas constant for water vapor
        ah = (e * 1000) / (461.5 * (temperature + 273.15))
        
        return ah
    
    @staticmethod
    def specific_enthalpy(temperature: float, relative_humidity: float,
                         pressure: float = 101.325) -> float:
        """
        Calculate specific enthalpy (total heat content)
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
            pressure: Atmospheric pressure (kPa)
        
        Returns:
            Specific enthalpy (kJ/kg)
        """
        # Humidity ratio
        w = PsychrometricCalculator.humidity_ratio(
            temperature, relative_humidity, pressure
        )
        
        # Specific enthalpy
        # h = 1.006*T + w*(2501 + 1.86*T)
        h = 1.006 * temperature + w * (2501 + 1.86 * temperature)
        
        return h
    
    @staticmethod
    def humidity_ratio(temperature: float, relative_humidity: float,
                      pressure: float = 101.325) -> float:
        """
        Calculate humidity ratio (mixing ratio)
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
            pressure: Atmospheric pressure (kPa)
        
        Returns:
            Humidity ratio (kg water / kg dry air)
        """
        # Vapor pressure
        e = PsychrometricCalculator.vapor_pressure(temperature, relative_humidity)
        
        # Humidity ratio
        # w = 0.622 * e / (P - e)
        w = 0.622 * e / (pressure - e)
        
        return w
    
    @staticmethod
    def specific_volume(temperature: float, pressure: float = 101.325) -> float:
        """
        Calculate specific volume of dry air
        
        Args:
            temperature: Air temperature (°C)
            pressure: Atmospheric pressure (kPa)
        
        Returns:
            Specific volume (m³/kg)
        """
        # Specific volume using ideal gas law
        # v = (287.05 * (T + 273.15)) / (P * 1000)
        # where 287.05 is specific gas constant for dry air
        v = (287.05 * (temperature + 273.15)) / (pressure * 1000)
        
        return v
    
    @staticmethod
    def comfort_index(temperature: float, relative_humidity: float) -> Dict[str, Any]:
        """
        Calculate human comfort index
        
        Useful for greenhouse workers and plant stress assessment
        
        Args:
            temperature: Air temperature (°C)
            relative_humidity: Relative humidity (%)
        
        Returns:
            Comfort assessment
        """
        # Heat Index (simplified)
        hi = temperature + 0.5555 * (
            (6.11 * math.exp(5417.7530 * ((1/273.16) - (1/(273.15 + temperature)))) * 
             (relative_humidity / 100)) - 10
        )
        
        # Classify comfort
        if hi < 27:
            comfort = "comfortable"
            risk = "low"
        elif hi < 32:
            comfort = "caution"
            risk = "medium"
        elif hi < 41:
            comfort = "extreme_caution"
            risk = "high"
        else:
            comfort = "danger"
            risk = "extreme"
        
        return {
            "heat_index": round(hi, 1),
            "comfort_level": comfort,
            "heat_stress_risk": risk,
            "recommendation": PsychrometricCalculator._get_comfort_recommendation(comfort)
        }
    
    @staticmethod
    def _get_comfort_recommendation(comfort: str) -> str:
        """Get recommendation based on comfort level"""
        recommendations = {
            "comfortable": "Conditions are comfortable for work and plant growth",
            "caution": "Monitor workers and plants, ensure adequate hydration",
            "extreme_caution": "Limit outdoor work, increase ventilation, monitor plants closely",
            "danger": "Avoid outdoor work, emergency cooling measures needed"
        }
        return recommendations.get(comfort, "Monitor conditions")
    
    @staticmethod
    def to_dict(params: PsychrometricParameters) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "temperature": round(params.temperature, 2),
            "relative_humidity": round(params.relative_humidity, 1),
            "pressure": round(params.pressure, 2),
            "dew_point": round(params.dew_point, 2),
            "wet_bulb_temperature": round(params.wet_bulb_temperature, 2),
            "absolute_humidity": round(params.absolute_humidity, 2),
            "specific_enthalpy": round(params.specific_enthalpy, 2),
            "vapor_pressure": round(params.vapor_pressure, 3),
            "specific_volume": round(params.specific_volume, 3)
        }


# Example usage
if __name__ == "__main__":
    # Example: Calculate all parameters
    temp = 28.5  # °C
    rh = 65  # %
    
    params = PsychrometricCalculator.calculate_all(temp, rh)
    
    print("="*60)
    print("PSYCHROMETRIC PARAMETERS")
    print("="*60)
    print(f"Temperature: {temp}°C")
    print(f"Relative Humidity: {rh}%")
    print(f"\nCalculated Parameters:")
    print(f"  Dew Point: {params.dew_point:.2f}°C")
    print(f"  Wet Bulb Temperature: {params.wet_bulb_temperature:.2f}°C")
    print(f"  Absolute Humidity: {params.absolute_humidity:.2f} g/m³")
    print(f"  Specific Enthalpy: {params.specific_enthalpy:.2f} kJ/kg")
    print(f"  Vapor Pressure: {params.vapor_pressure:.3f} kPa")
    print(f"  Specific Volume: {params.specific_volume:.3f} m³/kg")
    
    # Comfort index
    comfort = PsychrometricCalculator.comfort_index(temp, rh)
    print(f"\nComfort Assessment:")
    print(f"  Heat Index: {comfort['heat_index']}°C")
    print(f"  Comfort Level: {comfort['comfort_level']}")
    print(f"  Risk: {comfort['heat_stress_risk']}")
    print(f"  Recommendation: {comfort['recommendation']}")
