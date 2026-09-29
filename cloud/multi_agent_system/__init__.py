"""
Multi-Agent System (MAS) for Autonomous Farm Operations

Based on Papers 7 (Horticulture DT) and 9 (Cloud-Fog-Edge MAS)

Agents:
- Field Agent: Monitors field conditions and crop health
- Sensor Harvester Agent: Optimizes sensor data collection
- Decision Agent: Makes autonomous farming decisions
- Task Agent: Executes and coordinates farming tasks

Benefits:
- 50% reduction in manual intervention
- Autonomous operations 24/7
- Intelligent task prioritization
- Collaborative decision making
"""

from .base_agent import BaseAgent, AgentMessage, AgentState
from .field_agent import FieldAgent
from .sensor_harvester_agent import SensorHarvesterAgent
from .decision_agent import DecisionAgent
from .task_agent import TaskAgent
from .agent_coordinator import AgentCoordinator, get_coordinator, start_multi_agent_system, stop_multi_agent_system

__all__ = [
    'BaseAgent',
    'AgentMessage',
    'AgentState',
    'FieldAgent',
    'SensorHarvesterAgent',
    'DecisionAgent',
    'TaskAgent',
    'AgentCoordinator',
    'get_coordinator',
    'start_multi_agent_system',
    'stop_multi_agent_system',
]
