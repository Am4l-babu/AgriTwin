"""
Sensor Harvester Agent - Optimizes sensor data collection

Responsibilities:
- Collect sensor data from ESP32 devices
- Optimize sampling rates based on conditions
- Detect sensor failures
- Aggregate and preprocess data
- Forward data to Field Agent and storage

Based on Paper 9: Cloud-Fog-Edge Multi-Agent System
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from .base_agent import BaseAgent, AgentState, MessagePriority

logger = logging.getLogger(__name__)


class SensorHarvesterAgent(BaseAgent):
    """
    Sensor Harvester Agent optimizes data collection
    
    Beliefs:
    - active_sensors
    - sensor_health
    - sampling_rate
    - data_quality
    - last_collection_time
    
    Desires:
    - optimize_sampling_rate
    - ensure_data_quality
    - detect_sensor_failures
    
    Actions:
    - collect_sensor_data
    - adjust_sampling_rate
    - validate_data
    - forward_to_field_agent
    """
    
    def __init__(self, agent_id: str = "sensor_harvester_001"):
        super().__init__(agent_id, "SensorHarvesterAgent")
        
        # Sensor configuration
        self.sensors = {
            "temperature": {"min": -10, "max": 50, "unit": "°C"},
            "humidity": {"min": 0, "max": 100, "unit": "%"},
            "light": {"min": 0, "max": 100000, "unit": "lux"},
            "soil_moisture": {"min": 0, "max": 100, "unit": "%"},
        }
        
        # Sampling configuration
        self.default_sampling_rate = 10  # seconds
        self.min_sampling_rate = 5
        self.max_sampling_rate = 60
        
        # Initialize beliefs
        self.add_belief("active_sensors", list(self.sensors.keys()))
        self.add_belief("sampling_rate", self.default_sampling_rate)
        self.add_belief("data_quality_score", 100.0)
        self.add_belief("total_readings_collected", 0)
        
        # Initialize desires
        self.add_desire("collect_sensor_data", priority=10)
        self.add_desire("optimize_sampling_rate", priority=7)
        self.add_desire("ensure_data_quality", priority=9)
        
        logger.info(f"SensorHarvesterAgent initialized with {len(self.sensors)} sensors")
    
    async def perceive(self):
        """Perceive sensor availability and health"""
        # Check if it's time to collect data
        last_collection = self.get_belief("last_collection_time")
        sampling_rate = self.get_belief("sampling_rate").value
        
        if last_collection is None or \
           (datetime.now() - last_collection.value).total_seconds() >= sampling_rate:
            self.add_desire("collect_sensor_data", priority=10)
    
    async def deliberate(self):
        """Deliberate on data collection strategy"""
        # Check data quality
        quality = self.get_belief("data_quality_score")
        if quality and quality.value < 80:
            self.add_desire("improve_data_quality", priority=8)
        
        # Optimize sampling rate periodically
        last_optimization = self.get_belief("last_optimization_time")
        if last_optimization is None or \
           (datetime.now() - last_optimization.value).total_seconds() > 300:  # Every 5 minutes
            self.add_desire("optimize_sampling_rate", priority=7)
    
    async def act(self):
        """Execute data collection and optimization"""
        if not self.desires:
            return
        
        top_desire = self.desires[0]
        
        if top_desire.goal == "collect_sensor_data":
            await self._collect_sensor_data()
            self.remove_desire("collect_sensor_data")
        
        elif top_desire.goal == "optimize_sampling_rate":
            await self._optimize_sampling_rate()
            self.remove_desire("optimize_sampling_rate")
        
        elif top_desire.goal == "improve_data_quality":
            await self._improve_data_quality()
            self.remove_desire("improve_data_quality")
    
    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.message_type == "raw_sensor_data":
            await self._process_raw_data(message.content)
        
        elif message.message_type == "adjust_sampling_rate":
            new_rate = message.content.get("rate", self.default_sampling_rate)
            self.update_belief("sampling_rate", new_rate)
            logger.info(f"{self.agent_id}: Sampling rate adjusted to {new_rate}s")
        
        elif message.message_type == "sensor_failure":
            sensor_id = message.content.get("sensor_id")
            await self._handle_sensor_failure(sensor_id)
    
    async def _collect_sensor_data(self):
        """Collect data from sensors (simulated or from MQTT)"""
        # In real implementation, this would fetch from MQTT or database
        # For now, we'll wait for raw_sensor_data messages
        self.update_belief("last_collection_time", datetime.now())
        logger.debug(f"{self.agent_id}: Initiated sensor data collection")
    
    async def _process_raw_data(self, raw_data: Dict[str, Any]):
        """Process and validate raw sensor data"""
        validated_data = {}
        quality_scores = []
        
        for sensor_name, value in raw_data.items():
            if sensor_name not in self.sensors:
                continue
            
            sensor_config = self.sensors[sensor_name]
            
            # Validate range
            if sensor_config["min"] <= value <= sensor_config["max"]:
                validated_data[sensor_name] = value
                quality_scores.append(100.0)
            else:
                logger.warning(f"{self.agent_id}: {sensor_name} out of range: {value}")
                quality_scores.append(50.0)
                # Use clamped value
                validated_data[sensor_name] = max(sensor_config["min"], 
                                                  min(sensor_config["max"], value))
        
        # Update data quality score
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            self.update_belief("data_quality_score", avg_quality)
        
        # Update reading count
        total = self.get_belief("total_readings_collected").value
        self.update_belief("total_readings_collected", total + 1)
        
        # Forward to Field Agent
        await self.send_message(
            receiver="field_agent_001",
            message_type="sensor_data",
            content=validated_data,
            priority=MessagePriority.NORMAL
        )
        
        logger.debug(f"{self.agent_id}: Processed and forwarded sensor data (quality={avg_quality:.1f}%)")
    
    async def _optimize_sampling_rate(self):
        """
        Optimize sampling rate based on conditions
        
        Strategy:
        - High variability -> Increase sampling rate (lower interval)
        - Stable conditions -> Decrease sampling rate (higher interval)
        - Anomalies detected -> Increase sampling rate
        """
        # Get current conditions from beliefs
        # In real implementation, analyze recent data variance
        
        current_rate = self.get_belief("sampling_rate").value
        quality = self.get_belief("data_quality_score").value
        
        # Simple optimization logic
        if quality < 80:
            # Poor quality -> sample more frequently
            new_rate = max(self.min_sampling_rate, current_rate - 5)
        elif quality > 95:
            # Excellent quality and stable -> can sample less frequently
            new_rate = min(self.max_sampling_rate, current_rate + 5)
        else:
            new_rate = current_rate
        
        if new_rate != current_rate:
            self.update_belief("sampling_rate", new_rate)
            logger.info(f"{self.agent_id}: Optimized sampling rate: {current_rate}s -> {new_rate}s")
        
        self.update_belief("last_optimization_time", datetime.now())
    
    async def _improve_data_quality(self):
        """Take actions to improve data quality"""
        # Increase sampling rate temporarily
        current_rate = self.get_belief("sampling_rate").value
        new_rate = max(self.min_sampling_rate, current_rate - 5)
        self.update_belief("sampling_rate", new_rate)
        
        # Alert Decision Agent about quality issues
        await self.send_message(
            receiver="decision_agent_001",
            message_type="data_quality_alert",
            content={
                "quality_score": self.get_belief("data_quality_score").value,
                "action_taken": f"Increased sampling rate to {new_rate}s",
                "timestamp": datetime.now().isoformat()
            },
            priority=MessagePriority.HIGH
        )
        
        logger.info(f"{self.agent_id}: Improved data quality measures activated")
    
    async def _handle_sensor_failure(self, sensor_id: str):
        """Handle sensor failure"""
        logger.error(f"{self.agent_id}: Sensor failure detected: {sensor_id}")
        
        # Remove from active sensors
        active = self.get_belief("active_sensors").value
        if sensor_id in active:
            active.remove(sensor_id)
            self.update_belief("active_sensors", active)
        
        # Alert Decision Agent
        await self.send_message(
            receiver="decision_agent_001",
            message_type="sensor_failure_alert",
            content={
                "sensor_id": sensor_id,
                "timestamp": datetime.now().isoformat(),
                "active_sensors_remaining": len(active)
            },
            priority=MessagePriority.URGENT
        )
