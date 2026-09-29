"""
Comprehensive Digital Twin Physics Model

Implements water balance, soil dynamics, and environmental physics for
realistic farm simulation.
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


@dataclass
class SoilProperties:
    """Physical properties of soil"""
    field_capacity: float = 0.35  # m³/m³
    wilting_point: float = 0.15   # m³/m³
    saturation: float = 0.45      # m³/m³
    bulk_density: float = 1.3     # g/cm³
    organic_matter: float = 0.02  # fraction
    rooting_depth: float = 0.30   # meters
    
    def available_water_capacity(self) -> float:
        """Calculate available water capacity"""
        return (self.field_capacity - self.wilting_point) * self.rooting_depth * 1000  # mm


@dataclass
class WeatherData:
    """Environmental weather data"""
    temperature: float  # °C
    humidity: float     # %
    solar_radiation: float  # MJ/m²/day
    wind_speed: float   # m/s
    precipitation: float  # mm/day
    
    @classmethod
    def from_sensors(cls, sensors: Dict[str, float]):
        """Create from sensor readings"""
        return cls(
            temperature=sensors.get('temp', 25.0),
            humidity=sensors.get('humidity', 60.0),
            solar_radiation=cls.light_to_radiation(sensors.get('light', 500)),
            wind_speed=sensors.get('wind_speed', 2.0),
            precipitation=sensors.get('rain', 0.0)
        )
    
    @staticmethod
    def light_to_radiation(lux: float) -> float:
        """Convert lux to MJ/m²/day (approximate)"""
        # Rough conversion: 1 W/m² ≈ 500 lux
        watts_per_m2 = lux / 500
        # Convert to MJ/m²/day (assume 12 hours daylight)
        mj_per_day = (watts_per_m2 * 12 * 3600) / 1_000_000
        return mj_per_day


class WaterBalanceModel:
    """
    Water balance simulation using Penman-Monteith evapotranspiration
    
    Water Balance Equation:
    ΔS = P + I - ET - D - R
    
    Where:
    ΔS = Change in soil moisture storage
    P = Precipitation
    I = Irrigation
    ET = Evapotranspiration
    D = Deep drainage
    R = Runoff
    """
    
    def __init__(self, soil: SoilProperties):
        self.soil = soil
        self.current_moisture = soil.field_capacity  # Initial moisture
        self.crop_coefficient = 1.0  # Kc value
    
    def calculate_evapotranspiration(
        self,
        weather: WeatherData,
        crop_coeff: Optional[float] = None
    ) -> float:
        """
        Calculate reference evapotranspiration using simplified Penman-Monteith
        
        Returns: ET in mm/day
        """
        if crop_coeff is None:
            crop_coeff = self.crop_coefficient
        
        # Simplified ET₀ calculation (Hargreaves equation)
        T_mean = weather.temperature
        T_max = T_mean + 5  # Assumed diurnal range
        T_min = T_mean - 5
        
        # Hargreaves equation
        ET0 = 0.0023 * (T_mean + 17.8) * (T_max - T_min) ** 0.5 * weather.solar_radiation
        
        # Adjust for humidity (simplified)
        humidity_factor = 1.0 - (weather.humidity - 50) / 200
        ET0 *= humidity_factor
        
        # Crop evapotranspiration
        ETc = crop_coeff * ET0
        
        return max(ET0, 0)
    
    def calculate_drainage(self, moisture: float) -> float:
        """Calculate deep drainage when soil is saturated"""
        if moisture > self.soil.field_capacity:
            # Excess water drains
            excess = moisture - self.soil.field_capacity
            drainage_rate = 0.1  # 10% per day
            return excess * drainage_rate * self.soil.rooting_depth * 1000
        return 0.0
    
    def calculate_runoff(self, precipitation: float, current_moisture: float) -> float:
        """Calculate surface runoff"""
        if current_moisture > self.soil.saturation:
            # Soil saturated, assume 50% of precip becomes runoff
            return precipitation * 0.5
        return 0.0
    
    def update(
        self,
        weather: WeatherData,
        irrigation: float = 0.0,
        timestep_hours: float = 24.0
    ) -> Dict[str, float]:
        """
        Update water balance for one timestep
        
        Args:
            weather: Weather conditions
            irrigation: Amount of irrigation applied (mm)
            timestep_hours: Time step in hours
        
        Returns:
            Dictionary with all water balance components
        """
        # Calculate ET
        ET = self.calculate_evapotranspiration(weather) * (timestep_hours / 24.0)
        
        # Inputs
        P = weather.precipitation
        I = irrigation
        
        # Calculate new moisture
        moisture_input = P + I
        moisture_output = ET
        
        # Update soil moisture (as volumetric fraction)
        depth_mm = self.soil.rooting_depth * 1000
        delta_moisture = (moisture_input - moisture_output) / depth_mm
        new_moisture = self.current_moisture + delta_moisture
        
        # Calculate drainage and runoff
        drainage = self.calculate_drainage(new_moisture)
        runoff = self.calculate_runoff(P, new_moisture)
        
        # Adjust for drainage and runoff
        new_moisture -= (drainage + runoff) / depth_mm
        
        # Constrain to physical limits
        new_moisture = max(self.soil.wilting_point, min(new_moisture, self.soil.saturation))
        
        self.current_moisture = new_moisture
        
        return {
            "moisture": new_moisture,
            "moisture_percent": (new_moisture / self.soil.saturation) * 100,
            "precipitation": P,
            "irrigation": I,
            "evapotranspiration": ET,
            "drainage": drainage,
            "runoff": runoff,
            "water_deficit": max(0, self.soil.field_capacity - new_moisture) * depth_mm
        }
    
    def is_irrigation_needed(self, threshold: float = 0.60) -> bool:
        """
        Check if irrigation is needed
        
        Args:
            threshold: Fraction of available water (0-1) below which irrigation is needed
        
        Returns:
            True if irrigation needed
        """
        available_water = (self.current_moisture - self.soil.wilting_point) / \
                         (self.soil.field_capacity - self.soil.wilting_point)
        
        return available_water < threshold


class CropGrowthModel:
    """
    Simple crop growth model using Growing Degree Days (GDD)
    """
    
    def __init__(
        self,
        crop_name: str = "Tomato",
        base_temp: float = 10.0,
        max_temp: float = 30.0,
        gdd_to_maturity: float = 1500.0
    ):
        self.crop_name = crop_name
        self.base_temp = base_temp
        self.max_temp = max_temp
        self.gdd_to_maturity = gdd_to_maturity
        self.accumulated_gdd = 0.0
        self.growth_stage = "vegetative"
    
    def calculate_gdd(self, t_mean: float) -> float:
        """Calculate growing degree days"""
        if t_mean < self.base_temp:
            return 0.0
        elif t_mean > self.max_temp:
            return self.max_temp - self.base_temp
        else:
            return t_mean - self.base_temp
    
    def update(self, temperature: float) -> Dict[str, any]:
        """Update crop growth"""
        gdd_today = self.calculate_gdd(temperature)
        self.accumulated_gdd += gdd_today
        
        # Determine growth stage
        progress = self.accumulated_gdd / self.gdd_to_maturity
        
        if progress < 0.25:
            self.growth_stage = "vegetative"
        elif progress < 0.5:
            self.growth_stage = "flowering"
        elif progress < 0.75:
            self.growth_stage = "fruiting"
        elif progress < 1.0:
            self.growth_stage = "ripening"
        else:
            self.growth_stage = "mature"
        
        return {
            "gdd_accumulated": self.accumulated_gdd,
            "gdd_to_maturity": self.gdd_to_maturity,
            "growth_progress": min(progress * 100, 100),
            "growth_stage": self.growth_stage,
            "days_to_harvest": max(0, (self.gdd_to_maturity - self.accumulated_gdd) / 10)  # Approx
        }


class DigitalTwinPhysics:
    """
    Complete digital twin physics engine
    """
    
    def __init__(self, soil_properties: Optional[SoilProperties] = None):
        self.soil = soil_properties or SoilProperties()
        self.water_balance = WaterBalanceModel(self.soil)
        self.crop_growth = CropGrowthModel()
        self.history = []
    
    def simulate_step(
        self,
        sensor_data: Dict[str, float],
        irrigation: float = 0.0,
        timestep_hours: float = 24.0
    ) -> Dict[str, any]:
        """
        Simulate one timestep of the digital twin
        
        Args:
            sensor_data: Current sensor readings
            irrigation: Irrigation applied (mm)
            timestep_hours: Time step
        
        Returns:
            Complete state of the twin
        """
        # Convert sensor data to weather
        weather = WeatherData.from_sensors(sensor_data)
        
        # Update water balance
        water_state = self.water_balance.update(weather, irrigation, timestep_hours)
        
        # Update crop growth
        growth_state = self.crop_growth.update(weather.temperature)
        
        # Combined state
        twin_state = {
            "timestamp": datetime.now().isoformat(),
            "water": water_state,
            "crop": growth_state,
            "weather": {
                "temperature": weather.temperature,
                "humidity": weather.humidity,
                "solar_radiation": weather.solar_radiation,
                "precipitation": weather.precipitation
            },
            "recommendations": self._generate_recommendations(water_state, growth_state)
        }
        
        self.history.append(twin_state)
        
        return twin_state
    
    def _generate_recommendations(
        self,
        water_state: Dict,
        growth_state: Dict
    ) -> list:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Water management
        if water_state["water_deficit"] > 10:
            recommendations.append({
                "type": "irrigation",
                "priority": "high",
                "message": f"Water deficit detected ({water_state['water_deficit']:.1f}mm). Consider irrigation.",
                "action": "irrigate",
                "amount_mm": water_state["water_deficit"]
            })
        
        # Growth stage recommendations
        stage = growth_state["growth_stage"]
        if stage == "flowering":
            recommendations.append({
                "type": "fertilization",
                "priority": "medium",
                "message": "Crop is flowering. Consider bloom booster fertilizer.",
                "action": "fertilize"
            })
        
        return recommendations
    
    def predict_future(self, days_ahead: int = 7) -> list:
        """Predict future states (simplified)"""
        # This would use weather forecasts and run the simulation forward
        predictions = []
        for day in range(days_ahead):
            # Placeholder - would use real forecast data
            predictions.append({
                "day": day + 1,
                "predicted_moisture": self.water_balance.current_moisture * 0.95 ** day,
                "irrigation_needed": day % 3 == 0  # Example
            })
        return predictions
