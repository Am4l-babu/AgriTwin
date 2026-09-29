"""
Base Agent Class for Multi-Agent System

Provides common functionality for all agents:
- Message passing
- State management
- Belief-Desire-Intention (BDI) architecture
- Communication protocols
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent operational states"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
        }


@dataclass
class Belief:
    """Agent's belief about the world state"""
    key: str
    value: Any
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "self"


@dataclass
class Desire:
    """Agent's goal or desired state"""
    goal: str
    priority: int  # 1-10
    deadline: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intention:
    """Agent's committed plan to achieve a desire"""
    desire: Desire
    plan: List[str]  # List of action names
    status: str = "pending"  # pending, in_progress, completed, failed
    started_at: Optional[datetime] = None


class BaseAgent(ABC):
    """
    Base class for all agents in the Multi-Agent System
    
    Implements BDI (Belief-Desire-Intention) architecture:
    - Beliefs: What the agent knows about the world
    - Desires: What the agent wants to achieve
    - Intentions: What the agent has committed to do
    """
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState.IDLE
        
        # BDI components
        self.beliefs: Dict[str, Belief] = {}
        self.desires: List[Desire] = []
        self.intentions: List[Intention] = []
        
        # Communication
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.outbox: asyncio.Queue = asyncio.Queue()
        
        # Performance metrics
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.uptime_start = datetime.now()
        
        logger.info(f"Agent {self.agent_id} ({self.agent_type}) initialized")
    
    # ==================== Belief Management ====================
    
    def add_belief(self, key: str, value: Any, confidence: float = 1.0, source: str = "self"):
        """Add or update a belief"""
        self.beliefs[key] = Belief(
            key=key,
            value=value,
            confidence=confidence,
            timestamp=datetime.now(),
            source=source
        )
        logger.debug(f"{self.agent_id}: Added belief {key}={value} (confidence={confidence})")
    
    def get_belief(self, key: str) -> Optional[Belief]:
        """Get a belief by key"""
        return self.beliefs.get(key)
    
    def remove_belief(self, key: str):
        """Remove a belief"""
        if key in self.beliefs:
            del self.beliefs[key]
            logger.debug(f"{self.agent_id}: Removed belief {key}")
    
    def update_belief(self, key: str, value: Any, confidence: float = None):
        """Update an existing belief"""
        if key in self.beliefs:
            self.beliefs[key].value = value
            self.beliefs[key].timestamp = datetime.now()
            if confidence is not None:
                self.beliefs[key].confidence = confidence
    
    # ==================== Desire Management ====================
    
    def add_desire(self, goal: str, priority: int = 5, deadline: datetime = None, 
                   conditions: Dict[str, Any] = None):
        """Add a new desire (goal)"""
        desire = Desire(
            goal=goal,
            priority=priority,
            deadline=deadline,
            conditions=conditions or {}
        )
        self.desires.append(desire)
        self.desires.sort(key=lambda d: d.priority, reverse=True)
        logger.info(f"{self.agent_id}: Added desire '{goal}' (priority={priority})")
    
    def remove_desire(self, goal: str):
        """Remove a desire"""
        self.desires = [d for d in self.desires if d.goal != goal]
    
    # ==================== Intention Management ====================
    
    def commit_to_intention(self, desire: Desire, plan: List[str]):
        """Commit to an intention (plan to achieve desire)"""
        intention = Intention(
            desire=desire,
            plan=plan,
            status="pending"
        )
        self.intentions.append(intention)
        logger.info(f"{self.agent_id}: Committed to intention for '{desire.goal}'")
    
    def execute_intention(self, intention: Intention):
        """Execute an intention's plan"""
        intention.status = "in_progress"
        intention.started_at = datetime.now()
        logger.info(f"{self.agent_id}: Executing intention for '{intention.desire.goal}'")
    
    def complete_intention(self, intention: Intention, success: bool = True):
        """Mark intention as completed or failed"""
        intention.status = "completed" if success else "failed"
        if success:
            self.tasks_completed += 1
            self.remove_desire(intention.desire.goal)
        else:
            self.tasks_failed += 1
        logger.info(f"{self.agent_id}: Intention {'completed' if success else 'failed'}")
    
    # ==================== Communication ====================
    
    async def send_message(self, receiver: str, message_type: str, content: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL):
        """Send a message to another agent"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority
        )
        await self.outbox.put(message)
        self.messages_sent += 1
        logger.debug(f"{self.agent_id} -> {receiver}: {message_type}")
    
    async def receive_message(self) -> Optional[AgentMessage]:
        """Receive a message from inbox"""
        try:
            message = await asyncio.wait_for(self.inbox.get(), timeout=0.1)
            self.messages_received += 1
            logger.debug(f"{self.agent_id} <- {message.sender}: {message.message_type}")
            return message
        except asyncio.TimeoutError:
            return None
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming message - to be implemented by subclasses"""
        logger.warning(f"{self.agent_id}: Unhandled message type '{message.message_type}'")
    
    # ==================== Agent Lifecycle ====================
    
    @abstractmethod
    async def perceive(self):
        """
        Perceive the environment and update beliefs
        To be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def deliberate(self):
        """
        Deliberate on beliefs and desires to form intentions
        To be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def act(self):
        """
        Execute intentions and perform actions
        To be implemented by subclasses
        """
        pass
    
    async def run(self):
        """Main agent loop: perceive -> deliberate -> act"""
        logger.info(f"{self.agent_id}: Starting agent loop")
        self.state = AgentState.ACTIVE
        
        try:
            while self.state != AgentState.OFFLINE:
                # Process incoming messages
                message = await self.receive_message()
                if message:
                    await self.handle_message(message)
                
                # BDI cycle
                await self.perceive()
                await self.deliberate()
                await self.act()
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"{self.agent_id}: Error in agent loop: {e}")
            self.state = AgentState.ERROR
            raise
    
    def stop(self):
        """Stop the agent"""
        logger.info(f"{self.agent_id}: Stopping agent")
        self.state = AgentState.OFFLINE
    
    # ==================== Metrics ====================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        uptime = (datetime.now() - self.uptime_start).total_seconds()
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": self.tasks_completed / max(1, self.tasks_completed + self.tasks_failed),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "beliefs_count": len(self.beliefs),
            "desires_count": len(self.desires),
            "intentions_count": len(self.intentions),
            "uptime_seconds": uptime,
        }
    
    def __repr__(self):
        return f"<{self.agent_type} id={self.agent_id} state={self.state.value}>"
