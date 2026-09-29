"""
Digital Twin State Manager

Synchronizes real sensor data with the physics simulation to create
an accurate digital twin that tracks actual farm conditions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import asyncio

from  ..physics_model.comprehensive_physics import (
    DigitalTwinPhysics,
    SoilProperties,
    WeatherData
)


class TwinStateSynchronizer:
    """
    Synchronizes real-world data with digital twin simulation
    """
    
    def __init__(self, farm_id: str):
        self.farm_id = farm_id
        self.twin = DigitalTwinPhysics()
        self.last_sync = datetime.now()
        self.sync_interval = timedelta(minutes=5)
        
    async def update_from_sensors(self, sensor_data: Dict[str, float]):
        """
        Update twin state with real sensor data
        
        Args:
            sensor_data: Dictionary containing sensor readings
                {
                    'soil': 45.2,      # % moisture
                    'temp': 28.5,      # °C
                    'humidity': 65.0,  # %
                    'light': 750       # lux
                }
        """
        try:
            # Run simulation step
            twin_state = self.twin.simulate_step(sensor_data)
            
            # Compare predicted vs actual
            predicted_moisture = twin_state["water"]["moisture_percent"]
            actual_moisture = sensor_data.get("soil", 0)
            
            error = abs(predicted_moisture - actual_moisture)
            
            if error > 10.0:
                logger.warning(
                    f"Twin prediction error: {error:.1f}% "
                    f"(predicted: {predicted_moisture:.1f}%, actual: {actual_moisture:.1f}%)"
                )
                # Calibrate/adjust twin model
                self._calibrate_model(sensor_data, twin_state)
            
            self.last_sync = datetime.now()
            
            return twin_state
            
        except Exception as e:
            logger.error(f"Error updating twin state: {e}")
            return None
    
    def _calibrate_model(self, actual: Dict, predicted: Dict):
        """Adjust model parameters based on prediction error"""
        # Simple Kalman filter-like adjustment
        actual_moisture = actual.get("soil", 50) / 100.0  # Convert % to fraction
        predicted_moisture = predicted["water"]["moisture"]
        
        # Adjust current moisture toward actual
        adjustment_rate = 0.3  # 30% correction
        self.twin.water_balance.current_moisture = (
            predicted_moisture * (1 - adjustment_rate) +
            actual_moisture * adjustment_rate
        )
        
        logger.info(f"Model calibrated: adjusted moisture to {actual_moisture:.3f}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current twin state"""
        return {
            "farm_id": self.farm_id,
            "last_sync": self.last_sync.isoformat(),
            "moisture": self.twin.water_balance.current_moisture,
            "moisture_percent": (
                self.twin.water_balance.current_moisture /
                self.twin.soil.saturation
            ) * 100,
            "growth_stage": self.twin.crop_growth.growth_stage,
            "gdd_accumulated": self.twin.crop_growth.accumulated_gdd
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get current recommendations"""
        water_state = {
            "moisture": self.twin.water_balance.current_moisture,
            "water_deficit": max(
                0,
                (self.twin.soil.field_capacity - self.twin.water_balance.current_moisture) *
                self.twin.soil.rooting_depth * 1000
            )
        }
        
        growth_state = {
            "growth_stage": self.twin.crop_growth.growth_stage,
            "gdd_accumulated": self.twin.crop_growth.accumulated_gdd
        }
        
        return self.twin._generate_recommendations(water_state, growth_state)
    
    def run_scenario(
        self,
        scenario_name: str,
        days: int = 7,
        irrigation_schedule: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Run "what-if" scenario simulation
        
        Args:
            scenario_name: Name of scenario (e.g., "no_irrigation", "daily_irrigation")
            days: Number of days to simulate
            irrigation_schedule: List of irrigation amounts (mm) for each day
        
        Returns:
            Scenario results
        """
        logger.info(f"Running scenario: {scenario_name} ({days} days)")
        
        # Create a copy of the twin for scenario
        import copy
        scenario_twin = copy.deepcopy(self.twin)
        
        results = []
        
        for day in range(days):
            # Use irrigation schedule or default
            irrigation = 0.0
            if irrigation_schedule and day < len(irrigation_schedule):
                irrigation = irrigation_schedule[day]
            
            # Simulate one day
            # (Would use weather forecast here in production)
            fake_weather = {
                "temp": 25.0,
                "humidity": 60.0,
                "light": 600
            }
            
            state = scenario_twin.simulate_step(fake_weather, irrigation, timestep_hours=24)
            results.append(state)
        
        return {
            "scenario_name": scenario_name,
            "days_simulated": days,
            "final_moisture": results[-1]["water"]["moisture_percent"],
            "total_irrigation": sum(irrigation_schedule or []),
            "results": results
        }


class TwinStateManager:
    """
    Manages multiple farm digital twins
    """
    
    def __init__(self):
        self.twins: Dict[str, TwinStateSynchronizer] = {}
    
    def get_or_create_twin(self, farm_id: str) -> TwinStateSynchronizer:
        """Get existing twin or create new one"""
        if farm_id not in self.twins:
            logger.info(f"Creating new digital twin for farm: {farm_id}")
            self.twins[farm_id] = TwinStateSynchronizer(farm_id)
        return self.twins[farm_id]
    
    async def update_twin(self, farm_id: str, sensor_data: Dict[str, float]):
        """Update a specific farm's twin"""
        twin = self.get_or_create_twin(farm_id)
        return await twin.update_from_sensors(sensor_data)
    
    def get_all_twin_states(self) -> Dict[str, Dict]:
        """Get states of all twins"""
        return {
            farm_id: twin.get_current_state()
            for farm_id, twin in self.twins.items()
        }
