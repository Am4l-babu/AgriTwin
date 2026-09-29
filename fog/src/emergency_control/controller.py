"""
Emergency Controller

Autonomous decision-making when cloud connectivity is lost.
Executes predefined rules for critical situations (e.g., auto-irrigation).
"""

import asyncio
from typing import Dict, List, Any
from loguru import logger
import yaml


class EmergencyRule:
    """Represents an emergency control rule"""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = config["name"]
        self.enabled = config.get("enabled", True)
        self.sensor_type = config["sensor_type"]
        self.condition = config["condition"]
        self.threshold = config["threshold"]
        self.action = config["action"]
        self.cooldown_seconds = config.get("cooldown_seconds", 300)
        self.last_triggered = 0
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if rule condition is met"""
        if not self.enabled:
            return False
        
        if self.condition == "less_than":
            return value < self.threshold
        elif self.condition == "greater_than":
            return value > self.threshold
        elif self.condition == "equals":
            return value == self.threshold
        
        return False
    
    def can_trigger(self, current_time: float) -> bool:
        """Check if enough time has passed since last trigger"""
        return (current_time - self.last_triggered) >= self.cooldown_seconds


class EmergencyController:
    """
    Autonomous emergency control system
    """
    
    def __init__(self, settings, buffer_manager):
        self.settings = settings
        self.buffer = buffer_manager
        self.rules: List[EmergencyRule] = []
        self.running = False
        self._load_rules()
    
    def _load_rules(self):
        """Load emergency rules from configuration"""
        try:
            # Default rules
            default_rules = [
                {
                    "name": "auto_irrigation_low",
                    "enabled": True,
                    "sensor_type": "soil_moisture",
                    "condition": "less_than",
                    "threshold": 30.0,
                    "action": "activate_irrigation",
                    "duration_seconds": 30,
                    "cooldown_seconds": 600
                },
                {
                    "name": "temperature_alert_high",
                    "enabled": True,
                    "sensor_type": "temperature",
                    "condition": "greater_than",
                    "threshold": 35.0,
                    "action": "send_alert",
                    "cooldown_seconds": 300
                }
            ]
            
            for rule_config in default_rules:
                rule = EmergencyRule(rule_config)
                self.rules.append(rule)
                logger.info(f"Loaded emergency rule: {rule.name}")
            
        except Exception as e:
            logger.error(f"Error loading emergency rules: {e}")
    
    async def start(self):
        """Start the emergency controller"""
        self.running = True
        logger.info("Emergency Controller started")
    
    async def stop(self):
        """Stop the emergency controller"""
        self.running = False
        logger.info("Emergency Controller stopped")
    
    async def evaluate_conditions(self, farm_id: str, sensor_type: str, data: Dict[str, Any]):
        """Evaluate emergency conditions for incoming sensor data"""
        if not self.settings.emergency_control_enabled:
            return
        
        try:
            value = data.get("value")
            if value is None:
                return
            
            import time
            current_time = time.time()
            
            # Check all rules for this sensor type
            for rule in self.rules:
                if rule.sensor_type == sensor_type:
                    if rule.evaluate(value) and rule.can_trigger(current_time):
                        await self._execute_action(farm_id, rule, value)
                        rule.last_triggered = current_time
        
        except Exception as e:
            logger.error(f"Error evaluating emergency conditions: {e}")
    
    async def _execute_action(self, farm_id: str, rule: EmergencyRule, value: float):
        """Execute emergency action"""
        logger.warning(
            f"🚨 Emergency rule triggered: {rule.name} | "
            f"Farm: {farm_id} | Value: {value} | Threshold: {rule.threshold}"
        )
        
        try:
            if rule.action == "activate_irrigation":
                await self._activate_irrigation(farm_id)
            elif rule.action == "send_alert":
                await self._send_alert(farm_id, rule, value)
            else:
                logger.warning(f"Unknown action: {rule.action}")
        
        except Exception as e:
            logger.error(f"Error executing emergency action: {e}")
    
    async def _activate_irrigation(self, farm_id: str):
        """Activate irrigation system"""
        logger.info(f"Activating irrigation for farm: {farm_id}")
        
        # In a real system, this would:
        # 1. Publish MQTT command to edge device
        # 2. Activate relay/valve
        # 3. Log action to buffer
        
        # For now, just log the action
        await self.buffer.store_alert(farm_id, {
            "alert_type": "emergency_action",
            "severity": "warning",
            "message": f"Auto-irrigation activated",
            "timestamp": int(asyncio.get_event_loop().time())
        })
    
    async def _send_alert(self, farm_id: str, rule: EmergencyRule, value: float):
        """Send alert"""
        logger.warning(f"Alert: {rule.name} triggered for farm {farm_id}")
        
        await self.buffer.store_alert(farm_id, {
            "alert_type": rule.name,
            "severity": "warning",
            "message": f"{rule.sensor_type} = {value} (threshold: {rule.threshold})",
            "timestamp": int(asyncio.get_event_loop().time())
        })
    
    def is_running(self) -> bool:
        """Check if controller is running"""
        return self.running
    
    def get_rules(self) -> List[Dict]:
        """Get all rules"""
        return [
            {
                "name": rule.name,
                "enabled": rule.enabled,
                "sensor_type": rule.sensor_type,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "action": rule.action
            }
            for rule in self.rules
        ]
