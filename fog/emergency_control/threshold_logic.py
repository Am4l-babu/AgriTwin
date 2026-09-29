"""
Emergency Control System - Autonomous Threshold-Based Control

Enables the fog layer to operate independently when cloud is down.
Implements rule-based control logic for critical farm operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class EmergencyRule:
    """Single emergency control rule"""
    
    def __init__(self, name: str, condition, action: str, 
                 duration_sec: int = 0, cooldown_sec: int = 600):
        """
        Args:
            name: Rule name
            condition: Lambda function that takes sensor_data and returns bool
            action: Action to execute (e.g., "activate_valve_01")
            duration_sec: Duration for action execution
            cooldown_sec: Minimum time between rule activations
        """
        self.name = name
        self.condition = condition
        self.action = action
        self.duration_sec = duration_sec
        self.cooldown_sec = cooldown_sec
        
        self.last_activation = None
        self.activation_count = 0
    
    def can_activate(self) -> bool:
        """Check if rule can be activated (not in cooldown)"""
        if self.last_activation is None:
            return True
        
        cooldown_end = self.last_activation + timedelta(seconds=self.cooldown_sec)
        return datetime.now() >= cooldown_end
    
    def should_activate(self, sensor_data: Dict[str, Any]) -> bool:
        """Evaluate if rule condition is met"""
        try:
            return self.condition(sensor_data)
        except Exception as e:
            logger.error(f"Error evaluating rule {self.name}: {e}")
            return False


class ThresholdLogic:
    """
    Threshold-based emergency control system
    
    Implements autonomous decision-making based on sensor thresholds.
    Works independently of cloud backend.
    """
    
    def __init__(self, mqtt_client=None):
        """
        Args:
            mqtt_client: MQTT client for publishing commands
        """
        self.mqtt_client = mqtt_client
        self.rules: List[EmergencyRule] = []
        self.rule_history = []
        
        # Initialize default rules
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default emergency control rules"""
        
        # Auto-irrigation when soil moisture is low
        self.add_rule(EmergencyRule(
            name="Auto-irrigation (low moisture)",
            condition=lambda data: data.get('soil_moisture', 100) < 30,
            action="activate_valve_01",
            duration_sec=30,
            cooldown_sec=600  # 10 minutes
        ))
        
        # Heat protection - activate ventilation
        self.add_rule(EmergencyRule(
            name="Heat protection",
            condition=lambda data: data.get('temperature', 0) > 35,
            action="activate_fan_01",
            duration_sec=1800,  # 30 minutes
            cooldown_sec=300    # 5 minutes
        ))
        
        # Critical low moisture alert
        self.add_rule(EmergencyRule(
            name="Critical low moisture alert",
            condition=lambda data: data.get('soil_moisture', 100) < 20,
            action="send_alert_critical",
            duration_sec=0,
            cooldown_sec=3600  # 1 hour
        ))
        
        # pH out of range alert
        self.add_rule(EmergencyRule(
            name="pH out of range",
            condition=lambda data: (
                data.get('ph', 7.0) < 5.5 or data.get('ph', 7.0) > 8.5
            ),
            action="send_alert_ph",
            duration_sec=0,
            cooldown_sec=1800  # 30 minutes
        ))
        
        logger.info(f"✓ Initialized {len(self.rules)} emergency control rules")
    
    def add_rule(self, rule: EmergencyRule):
        """Add custom emergency rule"""
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.name}")
    
    async def evaluate(self, sensor_data: Dict[str, Any]):
        """
        Evaluate all rules against sensor data
        
        Args:
            sensor_data: Current sensor readings
        """
        farm_id = sensor_data.get('farm_id', 'unknown')
        
        for rule in self.rules:
            try:
                # Check if rule should activate
                if rule.should_activate(sensor_data):
                    # Check cooldown
                    if rule.can_activate():
                        logger.warning(
                            f"🚨 Emergency rule triggered: {rule.name} "
                            f"(farm: {farm_id})"
                        )
                        
                        # Execute action
                        await self._execute_action(
                            farm_id, 
                            rule.action, 
                            rule.duration_sec,
                            sensor_data
                        )
                        
                        # Update rule state
                        rule.last_activation = datetime.now()
                        rule.activation_count += 1
                        
                        # Log to history
                        self.rule_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'rule': rule.name,
                            'farm_id': farm_id,
                            'action': rule.action,
                            'sensor_data': sensor_data
                        })
                    else:
                        logger.debug(
                            f"Rule {rule.name} in cooldown "
                            f"(last activation: {rule.last_activation})"
                        )
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
    
    async def _execute_action(self, farm_id: str, action: str, 
                              duration_sec: int, sensor_data: Dict[str, Any]):
        """
        Execute emergency action
        
        Args:
            farm_id: Farm identifier
            action: Action to execute
            duration_sec: Action duration
            sensor_data: Current sensor data (for context)
        """
        if action.startswith("activate_valve"):
            await self._activate_actuator(farm_id, action, duration_sec)
        elif action.startswith("activate_fan"):
            await self._activate_actuator(farm_id, action, duration_sec)
        elif action.startswith("send_alert"):
            await self._send_alert(farm_id, action, sensor_data)
        else:
            logger.warning(f"Unknown action: {action}")
    
    async def _activate_actuator(self, farm_id: str, actuator_id: str, 
                                 duration_sec: int):
        """Send MQTT command to activate actuator"""
        if not self.mqtt_client:
            logger.warning("No MQTT client available for actuator control")
            return
        
        command = {
            "command": "activate",
            "actuator_id": actuator_id,
            "duration_sec": duration_sec,
            "source": "emergency_control",
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"farms/{farm_id}/commands/irrigation"
        
        success = self.mqtt_client.publish(topic, command, qos=1)
        
        if success:
            logger.info(
                f"✓ Activated {actuator_id} for {duration_sec} seconds "
                f"(farm: {farm_id})"
            )
        else:
            logger.error(f"✗ Failed to activate {actuator_id}")
    
    async def _send_alert(self, farm_id: str, alert_type: str, 
                         sensor_data: Dict[str, Any]):
        """Send alert via MQTT"""
        if not self.mqtt_client:
            logger.warning("No MQTT client available for alerts")
            return
        
        alert = {
            "alert_type": alert_type,
            "farm_id": farm_id,
            "severity": "critical" if "critical" in alert_type else "warning",
            "message": self._generate_alert_message(alert_type, sensor_data),
            "sensor_data": sensor_data,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"farms/{farm_id}/alerts"
        
        self.mqtt_client.publish(topic, alert, qos=1)
        logger.warning(f"⚠ Alert sent: {alert_type} (farm: {farm_id})")
    
    def _generate_alert_message(self, alert_type: str, 
                                sensor_data: Dict[str, Any]) -> str:
        """Generate human-readable alert message"""
        if "moisture" in alert_type:
            moisture = sensor_data.get('soil_moisture', 'N/A')
            return f"Soil moisture critically low: {moisture}%"
        elif "ph" in alert_type:
            ph = sensor_data.get('ph', 'N/A')
            return f"pH out of optimal range: {ph}"
        elif "temperature" in alert_type:
            temp = sensor_data.get('temperature', 'N/A')
            return f"High temperature alert: {temp}°C"
        else:
            return f"Alert: {alert_type}"
    
    def get_rule_stats(self) -> Dict[str, Any]:
        """Get statistics on rule activations"""
        return {
            'total_rules': len(self.rules),
            'rules': [
                {
                    'name': rule.name,
                    'activation_count': rule.activation_count,
                    'last_activation': rule.last_activation.isoformat() 
                        if rule.last_activation else None
                }
                for rule in self.rules
            ],
            'total_activations': sum(r.activation_count for r in self.rules)
        }
