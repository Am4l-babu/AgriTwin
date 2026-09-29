# Actuation controller - Virtual → Physical control

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class ActuationType(Enum):
    """Types of physical actuations"""
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PESTICIDE = "pesticide"
    VENTILATION = "ventilation"
    HEATING = "heating"
    COOLING = "cooling"


class ActuationController:
    """
    Control physical devices from digital twin
    Virtual → Physical direction
    
    Features:
    - Send commands to physical devices
    - Safety validation
    - Cooldown management
    - Action logging
    """
    
    def __init__(self, mqtt_client, farm_id: str):
        self.mqtt_client = mqtt_client
        self.farm_id = farm_id
        self.action_history: Dict[str, datetime] = {}
        
        # Safety limits
        self.safety_limits = {
            ActuationType.IRRIGATION: {
                "min_duration": 60,  # 1 minute
                "max_duration": 3600,  # 1 hour
                "cooldown": 600  # 10 minutes
            },
            ActuationType.FERTILIZATION: {
                "min_duration": 30,
                "max_duration": 300,  # 5 minutes
                "cooldown": 86400  # 24 hours
            },
            ActuationType.VENTILATION: {
                "min_duration": 60,
                "max_duration": 7200,  # 2 hours
                "cooldown": 300  # 5 minutes
            }
        }
    
    def irrigate(self, device_id: str, duration_seconds: int, 
                 flow_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Send irrigation command to physical device
        
        Args:
            device_id: Target device ID
            duration_seconds: How long to irrigate (seconds)
            flow_rate: Optional flow rate (L/min)
        
        Returns:
            Result dictionary with success status
        """
        action_type = ActuationType.IRRIGATION
        
        # Safety validation
        validation = self._validate_command(
            device_id, action_type, duration_seconds
        )
        
        if not validation["safe"]:
            return {
                "success": False,
                "error": validation["reason"],
                "device_id": device_id
            }
        
        # Build command
        command = {
            "action": "irrigate",
            "duration": duration_seconds,
            "timestamp": datetime.now().isoformat(),
            "source": "digital_twin"
        }
        
        if flow_rate:
            command["flow_rate"] = flow_rate
        
        # Send via MQTT
        topic = f"farm/{self.farm_id}/device/{device_id}/command"
        self.mqtt_client.publish(topic, json.dumps(command))
        
        # Log action
        self._log_action(device_id, action_type, duration_seconds)
        
        return {
            "success": True,
            "device_id": device_id,
            "action": "irrigate",
            "duration": duration_seconds,
            "flow_rate": flow_rate,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }
    
    def fertilize(self, device_id: str, duration_seconds: int,
                 fertilizer_type: str = "N") -> Dict[str, Any]:
        """
        Send fertilization command
        
        Args:
            device_id: Target device ID
            duration_seconds: Application duration
            fertilizer_type: Type of fertilizer (N, P, K, NPK)
        """
        action_type = ActuationType.FERTILIZATION
        
        validation = self._validate_command(
            device_id, action_type, duration_seconds
        )
        
        if not validation["safe"]:
            return {
                "success": False,
                "error": validation["reason"]
            }
        
        command = {
            "action": "fertilize",
            "duration": duration_seconds,
            "fertilizer_type": fertilizer_type,
            "timestamp": datetime.now().isoformat(),
            "source": "digital_twin"
        }
        
        topic = f"farm/{self.farm_id}/device/{device_id}/command"
        self.mqtt_client.publish(topic, json.dumps(command))
        
        self._log_action(device_id, action_type, duration_seconds)
        
        return {
            "success": True,
            "device_id": device_id,
            "action": "fertilize",
            "duration": duration_seconds,
            "fertilizer_type": fertilizer_type
        }
    
    def control_ventilation(self, device_id: str, state: str,
                           duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Control ventilation (fan, vents)
        
        Args:
            device_id: Target device ID
            state: "on" or "off"
            duration_seconds: Optional auto-off duration
        """
        command = {
            "action": "ventilation",
            "state": state,
            "timestamp": datetime.now().isoformat(),
            "source": "digital_twin"
        }
        
        if duration_seconds:
            command["duration"] = duration_seconds
        
        topic = f"farm/{self.farm_id}/device/{device_id}/command"
        self.mqtt_client.publish(topic, json.dumps(command))
        
        return {
            "success": True,
            "device_id": device_id,
            "action": "ventilation",
            "state": state,
            "duration": duration_seconds
        }
    
    def _validate_command(self, device_id: str, action_type: ActuationType,
                         duration: int) -> Dict[str, Any]:
        """
        Validate command safety
        
        Checks:
        - Duration within limits
        - Cooldown period respected
        - Device availability
        """
        if action_type not in self.safety_limits:
            return {"safe": True}  # No limits defined
        
        limits = self.safety_limits[action_type]
        
        # Check duration limits
        if duration < limits["min_duration"]:
            return {
                "safe": False,
                "reason": f"Duration too short (min: {limits['min_duration']}s)"
            }
        
        if duration > limits["max_duration"]:
            return {
                "safe": False,
                "reason": f"Duration too long (max: {limits['max_duration']}s)"
            }
        
        # Check cooldown
        action_key = f"{device_id}_{action_type.value}"
        if action_key in self.action_history:
            last_action = self.action_history[action_key]
            time_since = (datetime.now() - last_action).total_seconds()
            
            if time_since < limits["cooldown"]:
                remaining = limits["cooldown"] - time_since
                return {
                    "safe": False,
                    "reason": f"Cooldown active ({remaining:.0f}s remaining)"
                }
        
        return {"safe": True}
    
    def _log_action(self, device_id: str, action_type: ActuationType,
                   duration: int):
        """Log action for cooldown tracking"""
        action_key = f"{device_id}_{action_type.value}"
        self.action_history[action_key] = datetime.now()
        
        # TODO: Store in database for audit trail
        print(f"[ACTUATION] {action_type.value} on {device_id} for {duration}s")
    
    def get_action_history(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get action history for device or all devices"""
        if device_id:
            return {
                k: v.isoformat() 
                for k, v in self.action_history.items() 
                if k.startswith(device_id)
            }
        
        return {k: v.isoformat() for k, v in self.action_history.items()}
    
    def check_cooldown_status(self, device_id: str, 
                             action_type: ActuationType) -> Dict[str, Any]:
        """Check if action is in cooldown"""
        action_key = f"{device_id}_{action_type.value}"
        
        if action_key not in self.action_history:
            return {
                "in_cooldown": False,
                "can_execute": True
            }
        
        last_action = self.action_history[action_key]
        limits = self.safety_limits.get(action_type, {})
        cooldown = limits.get("cooldown", 0)
        
        time_since = (datetime.now() - last_action).total_seconds()
        in_cooldown = time_since < cooldown
        
        return {
            "in_cooldown": in_cooldown,
            "can_execute": not in_cooldown,
            "last_action": last_action.isoformat(),
            "time_since_last": time_since,
            "cooldown_remaining": max(0, cooldown - time_since)
        }
