"""
Complete Digital Twin API Routes

Integrates with the DigitalTwinPhysics simulation engine.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import digital twin components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from cloud.digital_twin.twin_state_manager.twin_manager import TwinStateManager
from cloud.digital_twin.physics_model.comprehensive_physics import SoilProperties

router = APIRouter()

# Global twin manager instance
twin_manager = TwinStateManager()


class SensorUpdate(BaseModel):
    """Sensor data update"""
    soil: Optional[float] = None
    temp: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None
    ph: Optional[float] = None


class ScenarioRequest(BaseModel):
    """What-if scenario request"""
    name: str
    days: int = 7
    irrigation_schedule: Optional[List[float]] = None


@router.post("/{farm_id}/update")
async def update_twin_from_sensors(
    farm_id: str,
    sensor_data: SensorUpdate
):
    """
    Update digital twin with real sensor data
    
    This synchronizes the simulation with actual measurements.
    """
    try:
        # Convert Pydantic model to dict, filter None values
        data = {k: v for k, v in sensor_data.dict().items() if v is not None}
        
        # Update twin
        twin_state = await twin_manager.update_twin(farm_id, data)
        
        if twin_state is None:
            raise HTTPException(status_code=500, detail="Failed to update twin")
        
        return {
            "status": "success",
            "farm_id": farm_id,
            "timestamp": datetime.now().isoformat(),
            "twin_state": twin_state
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{farm_id}/state")
async def get_twin_state(farm_id: str):
    """
    Get current digital twin state
    
    Returns complete state including water balance, crop growth,
    and recommendations.
    """
    try:
        twin = twin_manager.get_or_create_twin(farm_id)
        state = twin.get_current_state()
        recommendations = twin.get_recommendations()
        
        return {
            "farm_id": farm_id,
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "recommendations": recommendations
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{farm_id}/scenario")
async def run_scenario_simulation(
    farm_id: str,
    scenario: ScenarioRequest
):
    """
    Run "what-if" scenario simulation
    
    Examples:
    - "What if I don't irrigate for 7 days?"
    - "What if I irrigate 5mm every other day?"
    - "How will drought conditions affect growth?"
    
    Returns predicted outcomes.
    """
    try:
        twin = twin_manager.get_or_create_twin(farm_id)
        
        results = twin.run_scenario(
            scenario_name=scenario.name,
            days=scenario.days,
            irrigation_schedule=scenario.irrigation_schedule
        )
        
        return {
            "farm_id": farm_id,
            "scenario": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{farm_id}/predictions")
async def get_predictions(farm_id: str, days_ahead: int = 7):
    """
    Get future predictions
    
    Predicts soil moisture, irrigation needs, and crop development.
    """
    try:
        twin = twin_manager.get_or_create_twin(farm_id)
        predictions = twin.twin.predict_future(days_ahead)
        
        return {
            "farm_id": farm_id,
            "days_ahead": days_ahead,
            "predictions": predictions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all/states")
async def get_all_twin_states():
    """
    Get states of all farms
    
    Useful for dashboard overview.
    """
    states = twin_manager.get_all_twin_states()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "farms": states,
        "total_farms": len(states)
    }


@router.post("/{farm_id}/calibrate")
async def calibrate_twin(
    farm_id: str,
    soil_properties: Dict[str, float]
):
    """
    Calibrate twin with specific soil properties
    
    Example:
    {
        "field_capacity": 0.35,
        "wilting_point": 0.15,
        "saturation": 0.45
    }
    """
    try:
        twin = twin_manager.get_or_create_twin(farm_id)
        
        # Update soil properties
        if "field_capacity" in soil_properties:
            twin.twin.soil.field_capacity = soil_properties["field_capacity"]
        if "wilting_point" in soil_properties:
            twin.twin.soil.wilting_point = soil_properties["wilting_point"]
        if "saturation" in soil_properties:
            twin.twin.soil.saturation = soil_properties["saturation"]
        
        return {
            "status": "success",
            "farm_id": farm_id,
            "updated_properties": soil_properties
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
