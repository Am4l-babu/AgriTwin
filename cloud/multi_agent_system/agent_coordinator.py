"""
Agent Coordinator - Manages and coordinates all agents

Responsibilities:
- Initialize and start all agents
- Route messages between agents
- Monitor agent health and performance
- Provide unified API for external systems
- Handle agent failures and recovery
- Collect system-wide metrics

Based on Paper 9: Multi-agent coordination
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from .base_agent import BaseAgent, AgentMessage, AgentState
from .field_agent import FieldAgent
from .sensor_harvester_agent import SensorHarvesterAgent
from .decision_agent import DecisionAgent
from .task_agent import TaskAgent

# Try to import ML Decision Agent (optional)
try:
    from .ml_decision_agent import MLDecisionAgent
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    MLDecisionAgent = None

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Coordinates all agents in the Multi-Agent System
    
    Manages:
    - Agent lifecycle (start/stop)
    - Message routing
    - Health monitoring
    - Performance metrics
    - System-wide coordination
    """
    
    def __init__(self, farm_id: str = "farm_001", use_ml: bool = True):
        self.farm_id = farm_id
        self.use_ml = use_ml and ML_AVAILABLE
        self.agents: Dict[str, BaseAgent] = {}
        self.running = False
        self.message_router_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.total_messages_routed = 0
        self.start_time: Optional[datetime] = None
        
        logger.info(f"AgentCoordinator initialized for farm {farm_id} (ML: {self.use_ml})")
    
    def initialize_agents(self):
        """Initialize all agents"""
        logger.info("Initializing agents...")
        
        # Choose decision agent based on ML availability
        if self.use_ml and ML_AVAILABLE:
            logger.info("Using ML-Enhanced Decision Agent")
            decision_agent = MLDecisionAgent("decision_agent_001", self.farm_id)
        else:
            logger.info("Using Rule-Based Decision Agent")
            decision_agent = DecisionAgent("decision_agent_001")
        
        # Create agents
        self.agents = {
            "field_agent_001": FieldAgent("field_agent_001", self.farm_id),
            "sensor_harvester_001": SensorHarvesterAgent("sensor_harvester_001"),
            "decision_agent_001": decision_agent,
            "task_agent_001": TaskAgent("task_agent_001"),
        }
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    async def start(self):
        """Start all agents and message router"""
        if self.running:
            logger.warning("AgentCoordinator already running")
            return
        
        logger.info("Starting Multi-Agent System...")
        self.running = True
        self.start_time = datetime.now()
        
        # Start message router
        self.message_router_task = asyncio.create_task(self._message_router())
        
        # Start all agents
        agent_tasks = []
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(agent.run())
            agent_tasks.append(task)
            logger.info(f"Started agent: {agent_id}")
        
        logger.info("Multi-Agent System started successfully")
        
        # Wait for all agents (they run indefinitely)
        try:
            await asyncio.gather(*agent_tasks, self.message_router_task)
        except Exception as e:
            logger.error(f"Error in agent execution: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop all agents"""
        if not self.running:
            return
        
        logger.info("Stopping Multi-Agent System...")
        self.running = False
        
        # Stop all agents
        for agent_id, agent in self.agents.items():
            agent.stop()
            logger.info(f"Stopped agent: {agent_id}")
        
        # Cancel message router
        if self.message_router_task:
            self.message_router_task.cancel()
            try:
                await self.message_router_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Multi-Agent System stopped")
    
    async def _message_router(self):
        """Route messages between agents"""
        logger.info("Message router started")
        
        while self.running:
            try:
                # Check outbox of each agent
                for sender_id, sender_agent in self.agents.items():
                    try:
                        # Get message from outbox (non-blocking)
                        message = await asyncio.wait_for(
                            sender_agent.outbox.get(),
                            timeout=0.01
                        )
                        
                        # Route to receiver
                        receiver_id = message.receiver
                        if receiver_id in self.agents:
                            receiver_agent = self.agents[receiver_id]
                            await receiver_agent.inbox.put(message)
                            self.total_messages_routed += 1
                            
                            logger.debug(f"Routed message: {sender_id} -> {receiver_id} ({message.message_type})")
                        else:
                            logger.warning(f"Unknown receiver: {receiver_id}")
                    
                    except asyncio.TimeoutError:
                        # No message in outbox, continue
                        continue
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in message router: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Message router stopped")
    
    # ==================== External API ====================
    
    async def send_sensor_data(self, sensor_data: Dict[str, Any]):
        """
        Send sensor data to the system
        
        Args:
            sensor_data: Dict with temperature, humidity, light, soil_moisture
        """
        harvester = self.agents.get("sensor_harvester_001")
        if harvester:
            message = AgentMessage(
                sender="external",
                receiver="sensor_harvester_001",
                message_type="raw_sensor_data",
                content=sensor_data
            )
            await harvester.inbox.put(message)
            logger.debug(f"Sent sensor data to system: {sensor_data}")
    
    async def get_field_status(self) -> Optional[Dict[str, Any]]:
        """Get current field status"""
        field_agent = self.agents.get("field_agent_001")
        if field_agent:
            field_status = field_agent.get_belief("field_status")
            if field_status:
                return field_status.value
        return None
    
    async def get_crop_health(self) -> Optional[float]:
        """Get current crop health score"""
        field_agent = self.agents.get("field_agent_001")
        if field_agent:
            health = field_agent.get_belief("crop_health_score")
            if health:
                return health.value
        return None
    
    async def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get list of pending tasks"""
        task_agent = self.agents.get("task_agent_001")
        if task_agent:
            return [task.to_dict() for task in task_agent.task_queue]
        return []
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of active tasks"""
        task_agent = self.agents.get("task_agent_001")
        if task_agent:
            return [task.to_dict() for task in task_agent.active_tasks.values()]
        return []
    
    async def get_decision_history(self, decision_type: Optional[str] = None, 
                                   days: int = 7) -> List[Dict[str, Any]]:
        """Get decision history"""
        decision_agent = self.agents.get("decision_agent_001")
        if decision_agent:
            return decision_agent.get_decision_history(decision_type, days)
        return []
    
    async def create_manual_task(self, task_type: str, priority: str = "medium",
                                parameters: Dict[str, Any] = None):
        """Manually create a task"""
        decision_agent = self.agents.get("decision_agent_001")
        if decision_agent:
            message = AgentMessage(
                sender="external",
                receiver="task_agent_001",
                message_type="create_task",
                content={
                    "task_type": task_type,
                    "priority": priority,
                    "parameters": parameters or {}
                }
            )
            task_agent = self.agents.get("task_agent_001")
            if task_agent:
                await task_agent.inbox.put(message)
                logger.info(f"Created manual task: {task_type}")
    
    # ==================== Monitoring ====================
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        agent_metrics = {}
        for agent_id, agent in self.agents.items():
            metrics = agent.get_metrics()
            
            # Add ML-specific metrics if available
            if agent_id == "decision_agent_001" and hasattr(agent, 'get_performance_stats'):
                metrics['ml_stats'] = agent.get_performance_stats()
            
            agent_metrics[agent_id] = metrics
        
        return {
            "system_status": "running" if self.running else "stopped",
            "farm_id": self.farm_id,
            "ml_enabled": self.use_ml,
            "uptime_seconds": uptime,
            "total_agents": len(self.agents),
            "total_messages_routed": self.total_messages_routed,
            "messages_per_second": self.total_messages_routed / max(1, uptime),
            "agents": agent_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent"""
        agent = self.agents.get(agent_id)
        if agent:
            return agent.get_metrics()
        return None
    
    def get_all_agent_states(self) -> Dict[str, str]:
        """Get states of all agents"""
        return {
            agent_id: agent.state.value
            for agent_id, agent in self.agents.items()
        }
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        if not self.running:
            return False
        
        # Check if all agents are active or idle (not error/offline)
        for agent in self.agents.values():
            if agent.state in [AgentState.ERROR, AgentState.OFFLINE]:
                return False
        
        return True
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get detailed health report"""
        agent_health = {}
        for agent_id, agent in self.agents.items():
            metrics = agent.get_metrics()
            agent_health[agent_id] = {
                "state": agent.state.value,
                "healthy": agent.state not in [AgentState.ERROR, AgentState.OFFLINE],
                "success_rate": metrics["success_rate"],
                "tasks_completed": metrics["tasks_completed"],
                "tasks_failed": metrics["tasks_failed"],
            }
        
        return {
            "system_healthy": self.is_healthy(),
            "agents": agent_health,
            "timestamp": datetime.now().isoformat()
        }


# ==================== Singleton Instance ====================

_coordinator_instance: Optional[AgentCoordinator] = None


def get_coordinator(farm_id: str = "farm_001", use_ml: bool = True) -> AgentCoordinator:
    """Get or create coordinator singleton"""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = AgentCoordinator(farm_id, use_ml)
        _coordinator_instance.initialize_agents()
    return _coordinator_instance


async def start_multi_agent_system(farm_id: str = "farm_001", use_ml: bool = True):
    """Start the Multi-Agent System"""
    coordinator = get_coordinator(farm_id, use_ml)
    await coordinator.start()


async def stop_multi_agent_system():
    """Stop the Multi-Agent System"""
    global _coordinator_instance
    if _coordinator_instance:
        await _coordinator_instance.stop()
        _coordinator_instance = None
