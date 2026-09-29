"""
Field Agent - Monitors field conditions and crop health

Responsibilities:
- Monitor environmental conditions (temperature, humidity, light, soil moisture)
- Track crop growth stages
- Detect anomalies in field conditions
- Report field status to Decision Agent
- Predict crop health trends

Based on Paper 7: Horticulture Digital Twin
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from .base_agent import BaseAgent, AgentState, MessagePriority

logger = logging.getLogger(__name__)


class FieldAgent(BaseAgent):
    """
    Field Agent monitors field conditions and crop health
    
    Beliefs:
    - current_temperature
    - current_humidity
    - current_light
    - current_soil_moisture
    - crop_growth_stage
    - crop_health_score
    - anomaly_detected
    
    Desires:
    - maintain_optimal_conditions
    - detect_anomalies_early
    - track_crop_growth
    
    Actions:
    - monitor_sensors
    - calculate_health_score
    - detect_anomalies
    - report_status
    """
    
    def __init__(self, agent_id: str = "field_agent_001", farm_id: str = "farm_001"):
        super().__init__(agent_id, "FieldAgent")
        self.farm_id = farm_id
        
        # Optimal ranges calibrated from plant_health_data.csv (1,200 observations)
        # Healthy plants averages: 34.9% moisture, 24°C temp, 55.4% humidity, 603 lux
        self.optimal_ranges = {
            "temperature": (18, 30),  # Celsius (healthy range from dataset)
            "humidity": (45, 65),  # Percentage (healthy range from dataset)
            "light": (400, 800),  # Lux (healthy range from dataset)
            "soil_moisture": (30, 40),  # Percentage (healthy range: 30-40%, optimal: 34.9%)
        }
        
        # Crop growth stages
        self.growth_stages = [
            "germination",
            "seedling",
            "vegetative",
            "flowering",
            "fruiting",
            "ripening",
            "harvest_ready"
        ]
        
        # Initialize beliefs
        self.add_belief("farm_id", farm_id)
        self.add_belief("crop_growth_stage", "vegetative")
        self.add_belief("crop_health_score", 100.0)
        self.add_belief("anomaly_detected", False)
        self.add_belief("last_sensor_reading", None)
        
        # Initialize desires
        self.add_desire("maintain_optimal_conditions", priority=9)
        self.add_desire("detect_anomalies_early", priority=10)
        self.add_desire("track_crop_growth", priority=7)
        
        logger.info(f"FieldAgent initialized for farm {farm_id}")
    
    async def perceive(self):
        """Perceive field conditions from sensors"""
        # In real implementation, this would fetch from sensor database
        # For now, we'll simulate or wait for sensor data messages
        pass
    
    async def deliberate(self):
        """Deliberate on field conditions and form intentions"""
        # Check if we need to report status
        last_report = self.get_belief("last_status_report")
        if last_report is None or \
           (datetime.now() - last_report.value).total_seconds() > 60:
            # Report status every minute
            self.add_desire("report_field_status", priority=8)
        
        # Check for anomalies
        if self.get_belief("anomaly_detected") and \
           self.get_belief("anomaly_detected").value:
            self.add_desire("alert_anomaly", priority=10)
        
        # Check crop health
        health_score = self.get_belief("crop_health_score")
        if health_score and health_score.value < 70:
            self.add_desire("alert_poor_health", priority=9)
    
    async def act(self):
        """Execute intentions"""
        # Process desires in priority order
        if not self.desires:
            return
        
        top_desire = self.desires[0]
        
        if top_desire.goal == "report_field_status":
            await self._report_field_status()
            self.remove_desire("report_field_status")
        
        elif top_desire.goal == "alert_anomaly":
            await self._alert_anomaly()
            self.remove_desire("alert_anomaly")
        
        elif top_desire.goal == "alert_poor_health":
            await self._alert_poor_health()
            self.remove_desire("alert_poor_health")
    
    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.message_type == "sensor_data":
            await self._process_sensor_data(message.content)
        
        elif message.message_type == "request_status":
            await self._report_field_status()
        
        elif message.message_type == "update_growth_stage":
            new_stage = message.content.get("stage")
            if new_stage in self.growth_stages:
                self.update_belief("crop_growth_stage", new_stage)
                logger.info(f"{self.agent_id}: Crop growth stage updated to {new_stage}")
    
    async def _process_sensor_data(self, data: Dict[str, Any]):
        """Process incoming sensor data and update beliefs"""
        # Update sensor beliefs
        if "temperature" in data:
            self.update_belief("current_temperature", data["temperature"])
        if "humidity" in data:
            self.update_belief("current_humidity", data["humidity"])
        if "light" in data:
            self.update_belief("current_light", data["light"])
        if "soil_moisture" in data:
            self.update_belief("current_soil_moisture", data["soil_moisture"])
        
        self.update_belief("last_sensor_reading", datetime.now())
        
        # Calculate health score
        health_score = self._calculate_health_score()
        self.update_belief("crop_health_score", health_score)
        
        # Detect anomalies
        anomaly = self._detect_anomaly(data)
        self.update_belief("anomaly_detected", anomaly)
        
        # Update field status immediately after processing sensor data
        await self._report_field_status()
        
        logger.debug(f"{self.agent_id}: Processed sensor data, health={health_score:.1f}%")
    
    def _calculate_health_score(self) -> float:
        """
        Calculate crop health score (0-100) based on environmental conditions
        
        Score factors:
        - Temperature in optimal range: 25%
        - Humidity in optimal range: 25%
        - Light in optimal range: 25%
        - Soil moisture in optimal range: 25%
        """
        score = 0.0
        factors = 0
        
        # Temperature score
        temp = self.get_belief("current_temperature")
        if temp:
            temp_min, temp_max = self.optimal_ranges["temperature"]
            if temp_min <= temp.value <= temp_max:
                score += 25.0
            elif temp.value < temp_min:
                score += max(0, 25.0 * (1 - (temp_min - temp.value) / 10))
            else:
                score += max(0, 25.0 * (1 - (temp.value - temp_max) / 10))
            factors += 1
        
        # Humidity score
        humidity = self.get_belief("current_humidity")
        if humidity:
            hum_min, hum_max = self.optimal_ranges["humidity"]
            if hum_min <= humidity.value <= hum_max:
                score += 25.0
            elif humidity.value < hum_min:
                score += max(0, 25.0 * (1 - (hum_min - humidity.value) / 20))
            else:
                score += max(0, 25.0 * (1 - (humidity.value - hum_max) / 20))
            factors += 1
        
        # Light score
        light = self.get_belief("current_light")
        if light:
            light_min, light_max = self.optimal_ranges["light"]
            if light_min <= light.value <= light_max:
                score += 25.0
            elif light.value < light_min:
                score += max(0, 25.0 * (light.value / light_min))
            else:
                score += max(0, 25.0 * (light_max / light.value))
            factors += 1
        
        # Soil moisture score
        moisture = self.get_belief("current_soil_moisture")
        if moisture:
            moist_min, moist_max = self.optimal_ranges["soil_moisture"]
            if moist_min <= moisture.value <= moist_max:
                score += 25.0
            elif moisture.value < moist_min:
                score += max(0, 25.0 * (moisture.value / moist_min))
            else:
                score += max(0, 25.0 * (moist_max / moisture.value))
            factors += 1
        
        return score if factors > 0 else 100.0
    
    def _detect_anomaly(self, data: Dict[str, Any]) -> bool:
        """
        Detect anomalies in sensor data
        
        Anomaly conditions:
        - Temperature outside safe range (10-40°C)
        - Humidity outside safe range (30-95%)
        - Soil moisture critically low (<20%) or high (>90%)
        - Sudden large changes in readings
        """
        # Check temperature
        if "temperature" in data:
            if data["temperature"] < 10 or data["temperature"] > 40:
                logger.warning(f"{self.agent_id}: Temperature anomaly: {data['temperature']}°C")
                return True
        
        # Check humidity
        if "humidity" in data:
            if data["humidity"] < 30 or data["humidity"] > 95:
                logger.warning(f"{self.agent_id}: Humidity anomaly: {data['humidity']}%")
                return True
        
        # Check soil moisture
        if "soil_moisture" in data:
            if data["soil_moisture"] < 20:
                logger.warning(f"{self.agent_id}: Critical low soil moisture: {data['soil_moisture']}%")
                return True
            if data["soil_moisture"] > 90:
                logger.warning(f"{self.agent_id}: Critical high soil moisture: {data['soil_moisture']}%")
                return True
        
        return False
    
    async def _report_field_status(self):
            """Report field status to Decision Agent"""
            status = {
                "farm_id": self.farm_id,
                "timestamp": datetime.now().isoformat(),
                "crop_health_score": self.get_belief("crop_health_score").value if self.get_belief("crop_health_score") else 100.0,
                "crop_growth_stage": self.get_belief("crop_growth_stage").value if self.get_belief("crop_growth_stage") else "unknown",
                "anomaly_detected": self.get_belief("anomaly_detected").value if self.get_belief("anomaly_detected") else False,
                "conditions": {
                    "temperature": self.get_belief("current_temperature").value if self.get_belief("current_temperature") else None,
                    "humidity": self.get_belief("current_humidity").value if self.get_belief("current_humidity") else None,
                    "light": self.get_belief("current_light").value if self.get_belief("current_light") else None,
                    "soil_moisture": self.get_belief("current_soil_moisture").value if self.get_belief("current_soil_moisture") else None,
                }
            }

            # Store status as a belief so it can be retrieved by the API
            self.update_belief("field_status", status)

            await self.send_message(
                receiver="decision_agent_001",
                message_type="field_status",
                content=status,
                priority=MessagePriority.NORMAL
            )

            self.update_belief("last_status_report", datetime.now())
            logger.info(f"{self.agent_id}: Reported field status (health={status['crop_health_score']:.1f}%)")

    
    async def _alert_anomaly(self):
        """Alert Decision Agent about detected anomaly"""
        await self.send_message(
            receiver="decision_agent_001",
            message_type="anomaly_alert",
            content={
                "farm_id": self.farm_id,
                "timestamp": datetime.now().isoformat(),
                "severity": "high",
                "message": "Anomaly detected in field conditions"
            },
            priority=MessagePriority.URGENT
        )
        logger.warning(f"{self.agent_id}: Sent anomaly alert")
    
    async def _alert_poor_health(self):
        """Alert Decision Agent about poor crop health"""
        health_score = self.get_belief("crop_health_score").value
        await self.send_message(
            receiver="decision_agent_001",
            message_type="health_alert",
            content={
                "farm_id": self.farm_id,
                "timestamp": datetime.now().isoformat(),
                "health_score": health_score,
                "severity": "high" if health_score < 50 else "medium",
                "message": f"Crop health score is low: {health_score:.1f}%"
            },
            priority=MessagePriority.HIGH
        )
        logger.warning(f"{self.agent_id}: Sent poor health alert (score={health_score:.1f}%)")
