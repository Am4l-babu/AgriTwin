# Decision mapper
# Map problems to decisions, information, and data requirements

from typing import Dict, List, Any


# Map problems to decisions
PROBLEM_TO_DECISION = {
    "low_yield": {
        "decision": "How much fertilizer to apply?",
        "options": ["0 kg/ha", "50 kg/ha", "100 kg/ha", "150 kg/ha"],
        "information_needed": [
            "current_plant_nitrogen_status",
            "soil_nitrogen_availability",
            "expected_yield_for_zone",
            "crop_growth_stage"
        ]
    },
    
    "water_waste": {
        "decision": "When and how much to irrigate?",
        "options": ["0mm", "5mm", "10mm", "15mm", "20mm"],
        "information_needed": [
            "current_soil_moisture",
            "evapotranspiration_rate",
            "weather_forecast",
            "plant_water_stress"
        ]
    },
    
    "nutrient_deficiency": {
        "decision": "Which nutrients to apply and how much?",
        "options": ["N only", "N+P", "N+P+K", "Micronutrients"],
        "information_needed": [
            "soil_nutrient_levels",
            "plant_nutrient_status",
            "soil_ph",
            "crop_requirements"
        ]
    },
    
    "heat_stress": {
        "decision": "What cooling measures to implement?",
        "options": ["Increase irrigation", "Add shade", "Improve ventilation", "Misting"],
        "information_needed": [
            "current_temperature",
            "humidity_levels",
            "plant_canopy_temperature",
            "weather_forecast"
        ]
    },
    
    "pest_disease": {
        "decision": "What treatment to apply?",
        "options": ["Organic pesticide", "Chemical pesticide", "Biological control", "No action"],
        "information_needed": [
            "pest_identification",
            "infestation_severity",
            "crop_growth_stage",
            "weather_conditions"
        ]
    },
    
    "soil_degradation": {
        "decision": "What soil improvement measures?",
        "options": ["Add compost", "Cover crops", "Reduce tillage", "Lime application"],
        "information_needed": [
            "soil_organic_matter",
            "soil_structure",
            "soil_ph",
            "erosion_risk"
        ]
    }
}


# Map information needs to data requirements
INFORMATION_TO_DATA = {
    "current_soil_moisture": {
        "data_needed": ["soil_moisture_sensor_reading"],
        "sensors_required": ["capacitive_soil_moisture_sensor"],
        "frequency": "every_10_minutes",
        "accuracy_required": "±2%"
    },
    
    "current_plant_nitrogen_status": {
        "data_needed": ["leaf_color_ndvi", "plant_height", "chlorophyll_content"],
        "sensors_required": ["multispectral_camera", "height_sensor"],
        "frequency": "weekly",
        "accuracy_required": "±10%"
    },
    
    "soil_nitrogen_availability": {
        "data_needed": ["soil_n_content", "soil_organic_matter", "mineralization_rate"],
        "sensors_required": ["soil_lab_analysis", "soil_organic_matter_sensor"],
        "frequency": "monthly",
        "accuracy_required": "±15%"
    },
    
    "expected_yield_for_zone": {
        "data_needed": ["historical_yield_data", "soil_type", "weather_data"],
        "sensors_required": ["yield_monitor", "soil_survey", "weather_station"],
        "frequency": "per_season",
        "accuracy_required": "±20%"
    },
    
    "evapotranspiration_rate": {
        "data_needed": ["temperature", "humidity", "wind_speed", "solar_radiation"],
        "sensors_required": ["weather_station", "pyranometer"],
        "frequency": "hourly",
        "accuracy_required": "±10%"
    },
    
    "current_temperature": {
        "data_needed": ["air_temperature"],
        "sensors_required": ["temperature_sensor"],
        "frequency": "every_10_seconds",
        "accuracy_required": "±0.5°C"
    },
    
    "humidity_levels": {
        "data_needed": ["relative_humidity"],
        "sensors_required": ["humidity_sensor"],
        "frequency": "every_10_seconds",
        "accuracy_required": "±3%"
    },
    
    "plant_canopy_temperature": {
        "data_needed": ["thermal_image"],
        "sensors_required": ["thermal_camera"],
        "frequency": "daily",
        "accuracy_required": "±1°C"
    },
    
    "weather_forecast": {
        "data_needed": ["forecast_api_data"],
        "sensors_required": ["weather_api_subscription"],
        "frequency": "daily",
        "accuracy_required": "±20%"
    },
    
    "soil_nutrient_levels": {
        "data_needed": ["n_content", "p_content", "k_content", "micronutrients"],
        "sensors_required": ["soil_lab_analysis"],
        "frequency": "monthly",
        "accuracy_required": "±10%"
    },
    
    "soil_ph": {
        "data_needed": ["ph_reading"],
        "sensors_required": ["ph_sensor"],
        "frequency": "weekly",
        "accuracy_required": "±0.2"
    },
    
    "soil_organic_matter": {
        "data_needed": ["organic_matter_percentage"],
        "sensors_required": ["soil_lab_analysis"],
        "frequency": "annually",
        "accuracy_required": "±0.5%"
    }
}


def get_sensor_requirements(problem_id: str) -> Dict[str, Any]:
    """
    Get complete sensor requirements for a problem
    
    Returns exactly what sensors you need to buy
    """
    if problem_id not in PROBLEM_TO_DECISION:
        return {"error": "Problem not found"}
    
    decision = PROBLEM_TO_DECISION[problem_id]
    information_needed = decision["information_needed"]
    
    all_sensors = set()
    all_data = []
    
    for info in information_needed:
        if info in INFORMATION_TO_DATA:
            data_spec = INFORMATION_TO_DATA[info]
            all_sensors.update(data_spec["sensors_required"])
            all_data.extend(data_spec["data_needed"])
    
    return {
        "problem": problem_id,
        "decision": decision["decision"],
        "information_needed": information_needed,
        "data_needed": list(set(all_data)),
        "sensors_required": list(all_sensors),
        "estimated_cost": _estimate_sensor_cost(list(all_sensors))
    }


def _estimate_sensor_cost(sensors: List[str]) -> Dict[str, Any]:
    """Estimate cost of required sensors"""
    costs = {
        "capacitive_soil_moisture_sensor": 15,
        "temperature_sensor": 5,
        "humidity_sensor": 5,
        "multispectral_camera": 5000,
        "height_sensor": 100,
        "soil_lab_analysis": 50,
        "weather_station": 200,
        "pyranometer": 300,
        "thermal_camera": 3000,
        "ph_sensor": 30,
        "weather_api_subscription": 20
    }
    
    total = sum(costs.get(sensor, 0) for sensor in sensors)
    
    return {
        "total_usd": total,
        "breakdown": {sensor: costs.get(sensor, 0) for sensor in sensors}
    }
