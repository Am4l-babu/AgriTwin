"""
WebSocket Manager for Real-Time Updates

Provides real-time sensor data streaming to frontend dashboards.
"""

from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json
import asyncio


class ConnectionManager:
    """
    Manages WebSocket connections for real-time data streaming
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.farm_subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, farm_id: str = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if farm_id:
            if farm_id not in self.farm_subscriptions:
                self.farm_subscriptions[farm_id] = []
            self.farm_subscriptions[farm_id].append(websocket)
        
        logger.info(f"WebSocket connected (total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        
        # Remove from farm subscriptions
        for farm_id in list(self.farm_subscriptions.keys()):
            if websocket in self.farm_subscriptions[farm_id]:
                self.farm_subscriptions[farm_id].remove(websocket)
                if not self.farm_subscriptions[farm_id]:
                    del self.farm_subscriptions[farm_id]
        
        logger.info(f"WebSocket disconnected (total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_json = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
    
    async def broadcast_to_farm(self, farm_id: str, message: dict):
        """Broadcast message to clients subscribed to specific farm"""
        if farm_id not in self.farm_subscriptions:
            return
        
        message_json = json.dumps(message)
        for connection in self.farm_subscriptions[farm_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to farm {farm_id}: {e}")
    
    async def send_sensor_update(self, farm_id: str, sensor_data: dict):
        """Send real-time sensor update to subscribed clients"""
        message = {
            "type": "sensor_update",
            "farm_id": farm_id,
            "data": sensor_data,
            "timestamp": sensor_data.get("timestamp")
        }
        subscribers = self.farm_subscriptions.get(farm_id, [])
        logger.info(f"📤 Sending sensor update to {len(subscribers)} clients for {farm_id}: {sensor_data}")
        if not subscribers:
            logger.warning(f"⚠️  No WebSocket clients subscribed to {farm_id}. Active subscriptions: {list(self.farm_subscriptions.keys())}")
        await self.broadcast_to_farm(farm_id, message)
    
    async def send_alert(self, farm_id: str, alert: dict):
        """Send alert to subscribed clients"""
        message = {
            "type": "alert",
            "farm_id": farm_id,
            "alert": alert
        }
        await self.broadcast_to_farm(farm_id, message)
    
    async def send_twin_update(self, farm_id: str, twin_state: dict):
        """Send digital twin state update"""
        message = {
            "type": "twin_update",
            "farm_id": farm_id,
            "state": twin_state
        }
        await self.broadcast_to_farm(farm_id, message)


# Global instance
manager = ConnectionManager()
