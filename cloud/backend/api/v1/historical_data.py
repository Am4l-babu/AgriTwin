"""
Historical Plant Health Data API

Provides access to plant_health_data.csv for:
- Dashboard visualization
- ML model training
- System validation
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import logging
from pathlib import Path

router = APIRouter(prefix="/historical", tags=["Historical Data"])
logger = logging.getLogger(__name__)

# Path to dataset - use absolute path for Windows
import os
DATA_PATH = Path(r"C:\projects\DT\data\plant_health_data.csv")

# Verify path exists at module load
if DATA_PATH.exists():
    logger.info(f"✓ Historical data found: {DATA_PATH}")
else:
    logger.warning(f"✗ Historical data not found at: {DATA_PATH}")

class HistoricalDataPoint(BaseModel):
    timestamp: str
    plant_id: int
    soil_moisture: float
    ambient_temperature: float
    soil_temperature: float
    humidity: float
    light_intensity: float
    soil_ph: float
    nitrogen_level: float
    phosphorus_level: float
    potassium_level: float
    chlorophyll_content: float
    electrochemical_signal: float
    plant_health_status: str

class DataStatistics(BaseModel):
    total_records: int
    plants: int
    date_range: Dict[str, str]
    health_distribution: Dict[str, int]
    averages_by_health: Dict[str, Dict[str, float]]

@router.get("/data", summary="Get Historical Plant Health Data")
async def get_historical_data(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID (1-10)"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip")
) -> Dict[str, Any]:
    """
    Get historical plant health data from dataset
    
    Filters:
    - plant_id: 1-10
    - health_status: "Healthy", "Moderate Stress", "High Stress"
    - limit: max records (default 100)
    - offset: pagination offset
    """
    try:
        if not DATA_PATH.exists():
            raise HTTPException(status_code=404, detail="Historical data file not found")
        
        # Load data
        df = pd.read_csv(DATA_PATH)
        
        # Apply filters
        if plant_id is not None:
            df = df[df['Plant_ID'] == plant_id]
        
        if health_status:
            df = df[df['Plant_Health_Status'] == health_status]
        
        # Pagination
        total = len(df)
        df = df.iloc[offset:offset + limit]
        
        # Convert to records
        records = df.to_dict('records')
        
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "count": len(records),
            "data": records
        }
    
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", summary="Get Dataset Statistics")
async def get_statistics() -> DataStatistics:
    """Get statistical summary of the historical dataset"""
    try:
        if not DATA_PATH.exists():
            raise HTTPException(status_code=404, detail="Historical data file not found")
        
        df = pd.read_csv(DATA_PATH)
        
        # Health distribution
        health_dist = df['Plant_Health_Status'].value_counts().to_dict()
        
        # Averages by health status
        averages = {}
        for status in ['Healthy', 'Moderate Stress', 'High Stress']:
            subset = df[df['Plant_Health_Status'] == status]
            if len(subset) > 0:
                averages[status] = {
                    'soil_moisture': round(subset['Soil_Moisture'].mean(), 2),
                    'temperature': round(subset['Ambient_Temperature'].mean(), 2),
                    'humidity': round(subset['Humidity'].mean(), 2),
                    'light': round(subset['Light_Intensity'].mean(), 0),
                    'nitrogen': round(subset['Nitrogen_Level'].mean(), 2),
                    'phosphorus': round(subset['Phosphorus_Level'].mean(), 2),
                    'potassium': round(subset['Potassium_Level'].mean(), 2),
                    'chlorophyll': round(subset['Chlorophyll_Content'].mean(), 2)
                }
        
        return DataStatistics(
            total_records=len(df),
            plants=df['Plant_ID'].nunique(),
            date_range={
                "start": df['Timestamp'].min(),
                "end": df['Timestamp'].max()
            },
            health_distribution=health_dist,
            averages_by_health=averages
        )
    
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/thresholds", summary="Get Calibrated Thresholds")
async def get_thresholds() -> Dict[str, Any]:
    """
    Get calibrated thresholds from dataset analysis
    
    These thresholds are used by the Multi-Agent System for autonomous decisions
    """
    try:
        if not DATA_PATH.exists():
            raise HTTPException(status_code=404, detail="Historical data file not found")
        
        df = pd.read_csv(DATA_PATH)
        healthy = df[df['Plant_Health_Status'] == 'Healthy']
        
        return {
            "irrigation_threshold": {
                "value": 32.2,
                "unit": "% soil moisture",
                "description": "Trigger irrigation when below this value",
                "source": "25th percentile of healthy plants"
            },
            "fertilization_threshold": {
                "value": 26.7,
                "unit": "nitrogen level",
                "description": "Trigger fertilization when below this value",
                "source": "25th percentile of healthy plants"
            },
            "temperature_anomaly": {
                "value": 29.4,
                "unit": "°C",
                "description": "Trigger anomaly alert when above this value",
                "source": "95th percentile of healthy plants"
            },
            "optimal_ranges": {
                "soil_moisture": {
                    "min": round(healthy['Soil_Moisture'].min(), 1),
                    "max": round(healthy['Soil_Moisture'].max(), 1),
                    "optimal": round(healthy['Soil_Moisture'].mean(), 1)
                },
                "temperature": {
                    "min": round(healthy['Ambient_Temperature'].min(), 1),
                    "max": round(healthy['Ambient_Temperature'].max(), 1),
                    "optimal": round(healthy['Ambient_Temperature'].mean(), 1)
                },
                "nitrogen": {
                    "min": round(healthy['Nitrogen_Level'].min(), 1),
                    "max": round(healthy['Nitrogen_Level'].max(), 1),
                    "optimal": round(healthy['Nitrogen_Level'].mean(), 1)
                }
            },
            "correlation_with_health": {
                "soil_moisture": 0.775,
                "nitrogen_level": 0.269,
                "phosphorus_level": 0.059
            }
        }
    
    except Exception as e:
        logger.error(f"Error calculating thresholds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plant/{plant_id}/timeline", summary="Get Plant Timeline")
async def get_plant_timeline(plant_id: int) -> Dict[str, Any]:
    """Get health timeline for a specific plant"""
    try:
        if not DATA_PATH.exists():
            raise HTTPException(status_code=404, detail="Historical data file not found")
        
        if plant_id < 1 or plant_id > 10:
            raise HTTPException(status_code=400, detail="Plant ID must be between 1 and 10")
        
        df = pd.read_csv(DATA_PATH)
        plant_data = df[df['Plant_ID'] == plant_id].sort_values('Timestamp')
        
        if len(plant_data) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for plant {plant_id}")
        
        timeline = []
        for _, row in plant_data.iterrows():
            timeline.append({
                "timestamp": row['Timestamp'],
                "health_status": row['Plant_Health_Status'],
                "soil_moisture": round(row['Soil_Moisture'], 2),
                "temperature": round(row['Ambient_Temperature'], 2),
                "nitrogen": round(row['Nitrogen_Level'], 2)
            })
        
        return {
            "plant_id": plant_id,
            "total_readings": len(timeline),
            "timeline": timeline
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plant timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
