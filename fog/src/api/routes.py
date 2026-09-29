"""
API Routes for Fog Gateway
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List
from loguru import logger

router = APIRouter()


@router.get("/buffer/status")
async def get_buffer_status(request: Request):
    """Get buffer status and statistics"""
    try:
        buffer = request.app.state.buffer_manager
        
        # Get statistics from SQLite
        cursor = buffer.sqlite_conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sensor_data WHERE synced = 0")
        unsynced_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sensor_data")
        total_count = cursor.fetchone()[0]
        
        return {
            "status": "healthy" if buffer.is_healthy() else "unhealthy",
            "statistics": {
                "total_records": total_count,
                "unsynced_records": unsynced_count,
                "synced_records": total_count - unsynced_count
            }
        }
    except Exception as e:
        logger.error(f"Error getting buffer status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emergency/rules")
async def get_emergency_rules(request: Request):
    """Get all emergency control rules"""
    try:
        emergency = request.app.state.emergency_controller
        rules = emergency.get_rules()
        
        return {
            "enabled": emergency.settings.emergency_control_enabled,
            "rules": rules
        }
    except Exception as e:
        logger.error(f"Error getting emergency rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/trigger")
async def trigger_sync(request: Request):
    """Manually trigger cloud synchronization"""
    try:
        sync_service = request.app.state.cloud_sync_service
        result = await sync_service.trigger_manual_sync()
        return result
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mqtt/status")
async def get_mqtt_status(request: Request):
    """Get MQTT ingestion status"""
    try:
        mqtt = request.app.state.mqtt_service
        
        return {
            "connected": mqtt.is_connected(),
            "message_count": mqtt.get_message_count()
        }
    except Exception as e:
        logger.error(f"Error getting MQTT status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud/status")
async def get_cloud_status(request: Request):
    """Get cloud connection status"""
    try:
        sync_service = request.app.state.cloud_sync_service
        
        return {
            "connected": sync_service.is_connected(),
            "api_url": sync_service.settings.cloud_api_url
        }
    except Exception as e:
        logger.error(f"Error getting cloud status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adaptive-sensing/status")
async def get_adaptive_sensing_status(request: Request):
    """
    Thompson Sampling adaptive sensing status.

    Shows the current recommended polling interval for each sensor,
    the Beta(α, β) parameters for every arm, and the expected reward.
    The fog publishes interval-change commands to farms/001/commands
    whenever Thompson Sampling selects a different arm.
    """
    try:
        ts = getattr(request.app.state, "adaptive_ts", None)
        if ts is None:
            return {"enabled": False, "message": "Adaptive sensing not initialised"}
        return {"enabled": True, **ts.get_status()}
    except Exception as e:
        logger.error(f"Error getting adaptive sensing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adaptive-sensing/reset")
async def reset_adaptive_sensing(request: Request):
    """Reset Thompson Sampling state (clears learned Beta distributions)."""
    try:
        ts = getattr(request.app.state, "adaptive_ts", None)
        if ts is None:
            raise HTTPException(status_code=404, detail="Adaptive sensing not initialised")
        from src.adaptive_sensing.thompson_sampler import AdaptiveSamplingTS
        # Re-initialise in place (wipes learned state)
        request.app.state.adaptive_ts = AdaptiveSamplingTS()
        return {"message": "Thompson Sampling state reset — starting fresh"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting adaptive sensing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
