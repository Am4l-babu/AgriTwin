"""
Multi-Agent System API Endpoints

Provides REST API for:
- System status and health
- Agent metrics
- Task management
- Decision history
- Sensor data injection
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path

# Add parent directory to path to import multi_agent_system
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from multi_agent_system.agent_coordinator import get_coordinator, start_multi_agent_system, stop_multi_agent_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mas", tags=["Multi-Agent System"])


# ==================== Request/Response Models ====================

class SensorDataInput(BaseModel):
    """Sensor data input model"""
    temperature: float = Field(..., ge=-10, le=50, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    light: float = Field(..., ge=0, le=100000, description="Light in lux")
    soil_moisture: float = Field(..., ge=0, le=100, description="Soil moisture percentage")


class TaskCreate(BaseModel):
    """Task creation model"""
    task_type: str = Field(..., description="Task type: irrigation, fertilization, inspection, etc.")
    priority: str = Field(default="medium", description="Priority: low, medium, high, urgent")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")


class SystemStatus(BaseModel):
    """System status response"""
    status: str
    farm_id: str
    uptime_seconds: float
    total_agents: int
    agents_healthy: bool
    timestamp: str


# ==================== System Management ====================

@router.post("/start", summary="Start Multi-Agent System")
async def start_system(background_tasks: BackgroundTasks, farm_id: str = "farm_001", use_ml: bool = True):
    """
    Start the Multi-Agent System
    
    Initializes and starts all agents:
    - Field Agent
    - Sensor Harvester Agent
    - Decision Agent (ML-enhanced if use_ml=True)
    - Task Agent
    
    Args:
        farm_id: Farm identifier
        use_ml: Use ML-enhanced decision agent (default: True)
    """
    try:
        coordinator = get_coordinator(farm_id, use_ml)
        if coordinator.running:
            return {
                "message": "Multi-Agent System already running", 
                "farm_id": farm_id,
                "ml_enabled": coordinator.use_ml
            }
        
        # Start in background
        background_tasks.add_task(start_multi_agent_system, farm_id, use_ml)
        
        return {
            "message": "Multi-Agent System starting",
            "farm_id": farm_id,
            "ml_enabled": use_ml,
            "agents": list(coordinator.agents.keys())
        }
    except Exception as e:
        logger.error(f"Error starting MAS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", summary="Stop Multi-Agent System")
async def stop_system():
    """Stop the Multi-Agent System"""
    try:
        await stop_multi_agent_system()
        return {"message": "Multi-Agent System stopped"}
    except Exception as e:
        logger.error(f"Error stopping MAS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SystemStatus, summary="Get System Status")
async def get_status():
    """Get current system status"""
    try:
        coordinator = get_coordinator()
        metrics = coordinator.get_system_metrics()
        
        return SystemStatus(
            status="running" if coordinator.running else "stopped",
            farm_id=coordinator.farm_id,
            uptime_seconds=metrics["uptime_seconds"],
            total_agents=metrics["total_agents"],
            agents_healthy=coordinator.is_healthy(),
            timestamp=metrics["timestamp"]
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Get Health Report")
async def get_health():
    """Get detailed health report of all agents"""
    try:
        coordinator = get_coordinator()
        return coordinator.get_health_report()
    except Exception as e:
        logger.error(f"Error getting health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="Get System Metrics")
async def get_metrics():
    """Get comprehensive system metrics"""
    try:
        coordinator = get_coordinator()
        return coordinator.get_system_metrics()
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent Management ====================

@router.get("/agents", summary="Get All Agent States")
async def get_agents():
    """Get states of all agents"""
    try:
        coordinator = get_coordinator()
        return coordinator.get_all_agent_states()
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", summary="Get Agent Status")
async def get_agent_status(agent_id: str):
    """Get detailed status of specific agent"""
    try:
        coordinator = get_coordinator()
        status = coordinator.get_agent_status(agent_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Sensor Data ====================

@router.post("/sensor-data", summary="Send Sensor Data")
async def send_sensor_data(data: SensorDataInput):
    """
    Send sensor data to the Multi-Agent System
    
    The data will be processed by:
    1. Sensor Harvester Agent (validation)
    2. Field Agent (health calculation)
    3. Decision Agent (decision making)
    4. Task Agent (task execution if needed)
    """
    try:
        coordinator = get_coordinator()
        
        if not coordinator.running:
            raise HTTPException(status_code=503, detail="Multi-Agent System not running")
        
        await coordinator.send_sensor_data(data.dict())
        
        return {
            "message": "Sensor data received and processing",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Field Status ====================

@router.get("/field-status", summary="Get Field Status")
async def get_field_status():
    """Get current field status from Field Agent"""
    try:
        coordinator = get_coordinator()
        status = await coordinator.get_field_status()
        
        if status is None:
            # Return default status if field agent hasn't processed data yet
            return {
                "farm_id": "farm_001",
                "timestamp": datetime.now().isoformat(),
                "crop_health_score": 100.0,
                "crop_growth_stage": "unknown",
                "anomaly_detected": False,
                "conditions": {
                    "temperature": None,
                    "humidity": None,
                    "light": None,
                    "soil_moisture": None,
                }
            }
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crop-health", summary="Get Crop Health Score")
async def get_crop_health():
    """Get current crop health score"""
    try:
        coordinator = get_coordinator()
        health = await coordinator.get_crop_health()
        
        if health is None:
            raise HTTPException(status_code=404, detail="Crop health not available")
        
        return {
            "health_score": health,
            "status": "excellent" if health >= 90 else "good" if health >= 70 else "fair" if health >= 50 else "poor",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting crop health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Task Management ====================

@router.get("/tasks/pending", summary="Get Pending Tasks")
async def get_pending_tasks():
    """Get list of pending tasks"""
    try:
        coordinator = get_coordinator()
        tasks = await coordinator.get_pending_tasks()
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Error getting pending tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/active", summary="Get Active Tasks")
async def get_active_tasks():
    """Get list of currently executing tasks"""
    try:
        coordinator = get_coordinator()
        tasks = await coordinator.get_active_tasks()
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks", summary="Create Manual Task")
async def create_task(task: TaskCreate):
    """
    Manually create a task
    
    Task types:
    - irrigation: Water the crops
    - fertilization: Apply fertilizer
    - inspection: Inspect field conditions
    - pruning: Prune plants
    - harvesting: Harvest crops
    """
    try:
        coordinator = get_coordinator()
        
        if not coordinator.running:
            raise HTTPException(status_code=503, detail="Multi-Agent System not running")
        
        await coordinator.create_manual_task(
            task_type=task.task_type,
            priority=task.priority,
            parameters=task.parameters
        )
        
        return {
            "message": "Task created successfully",
            "task_type": task.task_type,
            "priority": task.priority,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Decision History ====================

@router.get("/decisions", summary="Get Decision History")
async def get_decisions(
    decision_type: Optional[str] = None,
    days: int = 7
):
    """
    Get decision history from Decision Agent
    
    Args:
        decision_type: Filter by type (irrigation, fertilization, etc.)
        days: Number of days to look back (default: 7)
    """
    try:
        coordinator = get_coordinator()
        decisions = await coordinator.get_decision_history(decision_type, days)
        
        return {
            "decisions": decisions,
            "count": len(decisions),
            "decision_type": decision_type,
            "days": days
        }
    except Exception as e:
        logger.error(f"Error getting decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/summary", summary="Get Decision Summary")
async def get_decision_summary(days: int = 7):
    """Get summary of decisions made in the last N days"""
    try:
        coordinator = get_coordinator()
        all_decisions = await coordinator.get_decision_history(days=days)
        
        # Count by type
        summary = {}
        for decision in all_decisions:
            dtype = decision.get("type", "unknown")
            if dtype not in summary:
                summary[dtype] = {"total": 0, "executed": 0}
            summary[dtype]["total"] += 1
            if decision.get("should_irrigate") or decision.get("should_fertilize"):
                summary[dtype]["executed"] += 1
        
        return {
            "summary": summary,
            "total_decisions": len(all_decisions),
            "days": days,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting decision summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
