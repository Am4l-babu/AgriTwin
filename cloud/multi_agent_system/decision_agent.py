"""
Decision Agent - Makes autonomous farming decisions

Responsibilities:
- Analyze field status and sensor data
- Make irrigation decisions
- Plan fertilization schedules
- Detect disease risks
- Coordinate with Task Agent for execution
- Learn from outcomes to improve decisions

Based on Papers 7 and 9: Autonomous decision-making in agriculture
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .base_agent import BaseAgent, AgentState, MessagePriority

logger = logging.getLogger(__name__)


class DecisionAgent(BaseAgent):
    """
    Decision Agent makes autonomous farming decisions
    
    Beliefs:
    - field_status
    - crop_health
    - weather_forecast
    - irrigation_schedule
    - fertilization_schedule
    - pending_decisions
    
    Desires:
    - optimize_irrigation
    - maintain_crop_health
    - prevent_diseases
    - maximize_yield
    
    Actions:
    - decide_irrigation
    - decide_fertilization
    - assess_disease_risk
    - create_task_plan
    """
    
    def __init__(self, agent_id: str = "decision_agent_001"):
        super().__init__(agent_id, "DecisionAgent")
        
        # Decision thresholds calibrated from plant_health_data.csv analysis
        # Based on 1,200 observations from 10 plants over 30 days
        # Healthy plants: 34.9% moisture avg, Stressed: 18.1% moisture avg
        self.irrigation_threshold = 32.2  # Soil moisture % (25th percentile of healthy plants)
        self.fertilization_threshold = 26.7  # Nitrogen level (25th percentile of healthy plants)
        self.health_alert_threshold = 70  # Health score
        self.disease_risk_threshold = 0.3  # 30% risk
        
        # Decision history for learning
        self.decision_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        # Initialize beliefs
        self.add_belief("last_irrigation_decision", None)
        self.add_belief("last_fertilization_decision", None)
        self.add_belief("decisions_made_today", 0)
        self.add_belief("autonomous_mode", True)
        
        # Initialize desires
        self.add_desire("monitor_field_conditions", priority=10)
        self.add_desire("optimize_irrigation", priority=9)
        self.add_desire("maintain_crop_health", priority=8)
        
        logger.info(f"DecisionAgent initialized with calibrated thresholds (irrigation: {self.irrigation_threshold}%, fertilization: {self.fertilization_threshold})")
    
    async def perceive(self):
        """Perceive field conditions and system state"""
        # Check if we have recent field status
        field_status = self.get_belief("field_status")
        if field_status:
            age = (datetime.now() - field_status.timestamp).total_seconds()
            if age > 120:  # Status older than 2 minutes
                # Request fresh status
                await self.send_message(
                    receiver="field_agent_001",
                    message_type="request_status",
                    content={},
                    priority=MessagePriority.NORMAL
                )
    
    async def deliberate(self):
        """Deliberate on farming decisions"""
        field_status = self.get_belief("field_status")
        if not field_status:
            return
        
        status_data = field_status.value
        
        # Check irrigation needs
        soil_moisture = status_data.get("conditions", {}).get("soil_moisture")
        if soil_moisture and soil_moisture < self.irrigation_threshold:
            self.add_desire("decide_irrigation", priority=10)
        
        # Check crop health
        health_score = status_data.get("crop_health_score", 100)
        if health_score < self.health_alert_threshold:
            self.add_desire("investigate_health_issue", priority=9)
        
        # Check for anomalies
        if status_data.get("anomaly_detected"):
            self.add_desire("handle_anomaly", priority=10)
        
        # Periodic fertilization check
        last_fert = self.get_belief("last_fertilization_decision")
        if last_fert is None or \
           (datetime.now() - last_fert.value).days >= 7:
            self.add_desire("decide_fertilization", priority=7)
    
    async def act(self):
        """Execute decisions"""
        if not self.desires:
            return
        
        top_desire = self.desires[0]
        
        if top_desire.goal == "decide_irrigation":
            await self._decide_irrigation()
            self.remove_desire("decide_irrigation")
        
        elif top_desire.goal == "decide_fertilization":
            await self._decide_fertilization()
            self.remove_desire("decide_fertilization")
        
        elif top_desire.goal == "investigate_health_issue":
            await self._investigate_health_issue()
            self.remove_desire("investigate_health_issue")
        
        elif top_desire.goal == "handle_anomaly":
            await self._handle_anomaly()
            self.remove_desire("handle_anomaly")
    
    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.message_type == "field_status":
            self.update_belief("field_status", message.content)
            logger.debug(f"{self.agent_id}: Received field status update")
        
        elif message.message_type == "anomaly_alert":
            self.add_desire("handle_anomaly", priority=10)
            logger.warning(f"{self.agent_id}: Anomaly alert received")
        
        elif message.message_type == "health_alert":
            self.add_desire("investigate_health_issue", priority=9)
            logger.warning(f"{self.agent_id}: Health alert received")
        
        elif message.message_type == "task_completed":
            await self._handle_task_completion(message.content)
        
        elif message.message_type == "task_failed":
            await self._handle_task_failure(message.content)
        
        elif message.message_type == "data_quality_alert":
            logger.warning(f"{self.agent_id}: Data quality alert: {message.content}")
        
        elif message.message_type == "sensor_failure_alert":
            logger.error(f"{self.agent_id}: Sensor failure: {message.content}")
            # May need to adjust decision-making based on available sensors
    
    async def _decide_irrigation(self):
        """
        Decide on irrigation action
        
        Decision factors:
        - Current soil moisture
        - Crop growth stage
        - Weather forecast (if available)
        - Time of day
        - Recent irrigation history
        """
        field_status = self.get_belief("field_status").value
        soil_moisture = field_status.get("conditions", {}).get("soil_moisture", 50)
        crop_stage = field_status.get("crop_growth_stage", "vegetative")
        
        # Decision logic
        should_irrigate = False
        duration_minutes = 0
        reason = ""
        
        if soil_moisture < 30:
            should_irrigate = True
            duration_minutes = 20
            reason = f"Critical low soil moisture ({soil_moisture}%)"
        elif soil_moisture < 40:
            should_irrigate = True
            duration_minutes = 15
            reason = f"Low soil moisture ({soil_moisture}%)"
        elif soil_moisture < 50 and crop_stage in ["flowering", "fruiting"]:
            should_irrigate = True
            duration_minutes = 10
            reason = f"Moderate moisture during critical growth stage"
        else:
            reason = f"Soil moisture adequate ({soil_moisture}%)"
        
        # Record decision
        decision = {
            "type": "irrigation",
            "timestamp": datetime.now().isoformat(),
            "should_irrigate": should_irrigate,
            "duration_minutes": duration_minutes,
            "soil_moisture": soil_moisture,
            "crop_stage": crop_stage,
            "reason": reason
        }
        
        self._record_decision(decision)
        self.update_belief("last_irrigation_decision", datetime.now())
        
        if should_irrigate:
            # Send task to Task Agent
            await self.send_message(
                receiver="task_agent_001",
                message_type="create_task",
                content={
                    "task_type": "irrigation",
                    "priority": "high" if soil_moisture < 30 else "medium",
                    "parameters": {
                        "duration_minutes": duration_minutes,
                        "reason": reason
                    }
                },
                priority=MessagePriority.HIGH if soil_moisture < 30 else MessagePriority.NORMAL
            )
            logger.info(f"{self.agent_id}: Irrigation decision: YES ({duration_minutes} min) - {reason}")
        else:
            logger.info(f"{self.agent_id}: Irrigation decision: NO - {reason}")
    
    async def _decide_fertilization(self):
        """
        Decide on fertilization action
        
        Decision factors:
        - Crop growth stage
        - Days since last fertilization
        - Crop health score
        - Nutrient requirements by stage
        """
        field_status = self.get_belief("field_status").value
        crop_stage = field_status.get("crop_growth_stage", "vegetative")
        health_score = field_status.get("crop_health_score", 100)
        
        # Fertilization schedule by growth stage
        fertilization_schedule = {
            "germination": {"apply": False, "type": None},
            "seedling": {"apply": True, "type": "balanced", "amount": "light"},
            "vegetative": {"apply": True, "type": "nitrogen-rich", "amount": "medium"},
            "flowering": {"apply": True, "type": "phosphorus-rich", "amount": "medium"},
            "fruiting": {"apply": True, "type": "potassium-rich", "amount": "heavy"},
            "ripening": {"apply": False, "type": None},
            "harvest_ready": {"apply": False, "type": None}
        }
        
        schedule = fertilization_schedule.get(crop_stage, {"apply": False})
        
        should_fertilize = schedule.get("apply", False)
        fertilizer_type = schedule.get("type", "balanced")
        amount = schedule.get("amount", "medium")
        
        # Adjust based on health score
        if health_score < 70:
            should_fertilize = True
            amount = "heavy"
            reason = f"Low health score ({health_score:.1f}%) requires fertilization"
        else:
            reason = f"Scheduled fertilization for {crop_stage} stage"
        
        # Record decision
        decision = {
            "type": "fertilization",
            "timestamp": datetime.now().isoformat(),
            "should_fertilize": should_fertilize,
            "fertilizer_type": fertilizer_type,
            "amount": amount,
            "crop_stage": crop_stage,
            "health_score": health_score,
            "reason": reason
        }
        
        self._record_decision(decision)
        self.update_belief("last_fertilization_decision", datetime.now())
        
        if should_fertilize:
            # Send task to Task Agent
            await self.send_message(
                receiver="task_agent_001",
                message_type="create_task",
                content={
                    "task_type": "fertilization",
                    "priority": "high" if health_score < 70 else "medium",
                    "parameters": {
                        "fertilizer_type": fertilizer_type,
                        "amount": amount,
                        "reason": reason
                    }
                },
                priority=MessagePriority.HIGH if health_score < 70 else MessagePriority.NORMAL
            )
            logger.info(f"{self.agent_id}: Fertilization decision: YES ({fertilizer_type}, {amount}) - {reason}")
        else:
            logger.info(f"{self.agent_id}: Fertilization decision: NO - {reason}")
    
    async def _investigate_health_issue(self):
        """Investigate poor crop health"""
        field_status = self.get_belief("field_status").value
        health_score = field_status.get("crop_health_score", 100)
        conditions = field_status.get("conditions", {})
        
        issues = []
        
        # Check each condition
        if conditions.get("temperature", 25) > 35:
            issues.append("High temperature stress")
        elif conditions.get("temperature", 25) < 15:
            issues.append("Low temperature stress")
        
        if conditions.get("humidity", 70) < 40:
            issues.append("Low humidity")
        elif conditions.get("humidity", 70) > 90:
            issues.append("High humidity (disease risk)")
        
        if conditions.get("soil_moisture", 50) < 30:
            issues.append("Water stress")
        
        if conditions.get("light", 30000) < 10000:
            issues.append("Insufficient light")
        
        logger.warning(f"{self.agent_id}: Health investigation - Score: {health_score:.1f}%, Issues: {', '.join(issues) if issues else 'None identified'}")
        
        # Send investigation report
        await self.send_message(
            receiver="task_agent_001",
            message_type="health_investigation_report",
            content={
                "health_score": health_score,
                "identified_issues": issues,
                "timestamp": datetime.now().isoformat()
            },
            priority=MessagePriority.HIGH
        )
    
    async def _handle_anomaly(self):
        """Handle detected anomaly"""
        logger.warning(f"{self.agent_id}: Handling anomaly - requesting immediate field assessment")
        
        # Request immediate status update
        await self.send_message(
            receiver="field_agent_001",
            message_type="request_status",
            content={"urgent": True},
            priority=MessagePriority.URGENT
        )
        
        # Create inspection task
        await self.send_message(
            receiver="task_agent_001",
            message_type="create_task",
            content={
                "task_type": "inspection",
                "priority": "urgent",
                "parameters": {
                    "reason": "Anomaly detected in field conditions"
                }
            },
            priority=MessagePriority.URGENT
        )
    
    async def _handle_task_completion(self, task_info: Dict[str, Any]):
        """Handle task completion notification"""
        task_type = task_info.get("task_type")
        logger.info(f"{self.agent_id}: Task completed - {task_type}")
        
        # Update decision count
        count = self.get_belief("decisions_made_today").value
        self.update_belief("decisions_made_today", count + 1)
        
        # Learn from outcome (simplified)
        # In full implementation, this would update decision models
    
    async def _handle_task_failure(self, task_info: Dict[str, Any]):
        """Handle task failure notification"""
        task_type = task_info.get("task_type")
        reason = task_info.get("reason", "Unknown")
        logger.error(f"{self.agent_id}: Task failed - {task_type}: {reason}")
        
        # May need to create alternative task or alert human operator
    
    def _record_decision(self, decision: Dict[str, Any]):
        """Record decision for learning and audit"""
        self.decision_history.append(decision)
        
        # Keep history size manageable
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history:]
        
        logger.debug(f"{self.agent_id}: Recorded decision: {decision['type']}")
    
    def get_decision_history(self, decision_type: Optional[str] = None, 
                            days: int = 7) -> List[Dict[str, Any]]:
        """Get decision history"""
        cutoff = datetime.now() - timedelta(days=days)
        
        history = [
            d for d in self.decision_history
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]
        
        if decision_type:
            history = [d for d in history if d["type"] == decision_type]
        
        return history
