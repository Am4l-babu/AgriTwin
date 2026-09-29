"""
Task Agent - Executes and coordinates farming tasks

Responsibilities:
- Receive task requests from Decision Agent
- Schedule and prioritize tasks
- Execute tasks (or coordinate with actuators)
- Monitor task progress
- Report task completion/failure
- Maintain task history

Based on Paper 9: Task execution in multi-agent systems
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

from .base_agent import BaseAgent, AgentState, MessagePriority

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """Task data structure"""
    task_id: str
    task_type: str  # irrigation, fertilization, inspection, etc.
    priority: TaskPriority
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority.value,
            "parameters": self.parameters,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
        }


class TaskAgent(BaseAgent):
    """
    Task Agent executes and coordinates farming tasks
    
    Beliefs:
    - pending_tasks
    - active_tasks
    - completed_tasks
    - actuator_status
    - task_queue_length
    
    Desires:
    - execute_pending_tasks
    - maintain_task_schedule
    - optimize_task_order
    
    Actions:
    - schedule_task
    - execute_task
    - monitor_progress
    - report_completion
    """
    
    def __init__(self, agent_id: str = "task_agent_001"):
        super().__init__(agent_id, "TaskAgent")
        
        # Task management
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.max_concurrent_tasks = 3
        self.max_history = 1000
        
        # Task execution handlers
        self.task_handlers = {
            "irrigation": self._execute_irrigation,
            "fertilization": self._execute_fertilization,
            "inspection": self._execute_inspection,
            "pruning": self._execute_pruning,
            "harvesting": self._execute_harvesting,
        }
        
        # Initialize beliefs
        self.add_belief("pending_tasks_count", 0)
        self.add_belief("active_tasks_count", 0)
        self.add_belief("completed_tasks_count", 0)
        self.add_belief("tasks_completed_today", 0)
        
        # Initialize desires
        self.add_desire("execute_pending_tasks", priority=10)
        self.add_desire("monitor_active_tasks", priority=9)
        
        logger.info(f"TaskAgent initialized with {len(self.task_handlers)} task types")
    
    async def perceive(self):
        """Perceive task queue and system state"""
        # Update beliefs about task counts
        self.update_belief("pending_tasks_count", len(self.task_queue))
        self.update_belief("active_tasks_count", len(self.active_tasks))
        self.update_belief("completed_tasks_count", len(self.completed_tasks))
    
    async def deliberate(self):
        """Deliberate on task execution strategy"""
        # Check if we can execute more tasks
        if len(self.active_tasks) < self.max_concurrent_tasks and self.task_queue:
            self.add_desire("execute_next_task", priority=10)
        
        # Monitor active tasks
        if self.active_tasks:
            self.add_desire("monitor_active_tasks", priority=9)
    
    async def act(self):
        """Execute tasks"""
        if not self.desires:
            return
        
        top_desire = self.desires[0]
        
        if top_desire.goal == "execute_next_task":
            await self._execute_next_task()
            self.remove_desire("execute_next_task")
        
        elif top_desire.goal == "monitor_active_tasks":
            await self._monitor_active_tasks()
            self.remove_desire("monitor_active_tasks")
    
    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.message_type == "create_task":
            await self._create_task(message.content)
        
        elif message.message_type == "cancel_task":
            task_id = message.content.get("task_id")
            await self._cancel_task(task_id)
        
        elif message.message_type == "get_task_status":
            task_id = message.content.get("task_id")
            await self._send_task_status(task_id, message.sender)
        
        elif message.message_type == "list_tasks":
            await self._send_task_list(message.sender)
    
    async def _create_task(self, task_data: Dict[str, Any]):
        """Create a new task"""
        task_type = task_data.get("task_type")
        priority_str = task_data.get("priority", "medium")
        parameters = task_data.get("parameters", {})
        
        # Map priority string to enum
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT,
        }
        priority = priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)
        
        # Create task
        task = Task(
            task_id=f"task_{datetime.now().timestamp()}",
            task_type=task_type,
            priority=priority,
            parameters=parameters
        )
        
        # Add to queue (sorted by priority)
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        logger.info(f"{self.agent_id}: Created task {task.task_id} ({task_type}, priority={priority.name})")
        
        # Acknowledge task creation
        await self.send_message(
            receiver="decision_agent_001",
            message_type="task_created",
            content={"task_id": task.task_id, "task_type": task_type},
            priority=MessagePriority.NORMAL
        )
    
    async def _execute_next_task(self):
        """Execute the next task from queue"""
        if not self.task_queue:
            return
        
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            return
        
        # Get highest priority task
        task = self.task_queue.pop(0)
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        # Add to active tasks
        self.active_tasks[task.task_id] = task
        
        logger.info(f"{self.agent_id}: Starting task {task.task_id} ({task.task_type})")
        
        # Execute task asynchronously
        asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: Task):
        """Execute a task"""
        try:
            # Get task handler
            handler = self.task_handlers.get(task.task_type)
            
            if handler:
                result = await handler(task)
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                
                logger.info(f"{self.agent_id}: Completed task {task.task_id} ({task.task_type})")
                
                # Notify Decision Agent
                await self.send_message(
                    receiver="decision_agent_001",
                    message_type="task_completed",
                    content={
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "result": result
                    },
                    priority=MessagePriority.NORMAL
                )
                
                self.tasks_completed += 1
                count = self.get_belief("tasks_completed_today").value
                self.update_belief("tasks_completed_today", count + 1)
                
            else:
                raise ValueError(f"No handler for task type: {task.task_type}")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"{self.agent_id}: Task {task.task_id} failed: {e}")
            
            # Notify Decision Agent
            await self.send_message(
                receiver="decision_agent_001",
                message_type="task_failed",
                content={
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "reason": str(e)
                },
                priority=MessagePriority.HIGH
            )
            
            self.tasks_failed += 1
        
        finally:
            # Move to completed tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            
            self.completed_tasks.append(task)
            
            # Keep history size manageable
            if len(self.completed_tasks) > self.max_history:
                self.completed_tasks = self.completed_tasks[-self.max_history:]
    
    # ==================== Task Execution Handlers ====================
    
    async def _execute_irrigation(self, task: Task) -> Dict[str, Any]:
        """Execute irrigation task"""
        duration = task.parameters.get("duration_minutes", 15)
        reason = task.parameters.get("reason", "Scheduled irrigation")
        
        logger.info(f"{self.agent_id}: Irrigating for {duration} minutes - {reason}")
        
        # Simulate irrigation (in real system, control actuators)
        await asyncio.sleep(2)  # Simulate task duration
        
        return {
            "duration_minutes": duration,
            "water_used_liters": duration * 10,  # Estimate
            "reason": reason,
            "success": True
        }
    
    async def _execute_fertilization(self, task: Task) -> Dict[str, Any]:
        """Execute fertilization task"""
        fertilizer_type = task.parameters.get("fertilizer_type", "balanced")
        amount = task.parameters.get("amount", "medium")
        reason = task.parameters.get("reason", "Scheduled fertilization")
        
        logger.info(f"{self.agent_id}: Applying {amount} {fertilizer_type} fertilizer - {reason}")
        
        # Simulate fertilization
        await asyncio.sleep(1.5)
        
        return {
            "fertilizer_type": fertilizer_type,
            "amount": amount,
            "reason": reason,
            "success": True
        }
    
    async def _execute_inspection(self, task: Task) -> Dict[str, Any]:
        """Execute field inspection task"""
        reason = task.parameters.get("reason", "Routine inspection")
        
        logger.info(f"{self.agent_id}: Performing field inspection - {reason}")
        
        # Simulate inspection
        await asyncio.sleep(1)
        
        return {
            "inspection_type": "visual",
            "findings": "No issues detected",
            "reason": reason,
            "success": True
        }
    
    async def _execute_pruning(self, task: Task) -> Dict[str, Any]:
        """Execute pruning task"""
        logger.info(f"{self.agent_id}: Performing pruning")
        
        await asyncio.sleep(2)
        
        return {
            "pruning_type": "maintenance",
            "success": True
        }
    
    async def _execute_harvesting(self, task: Task) -> Dict[str, Any]:
        """Execute harvesting task"""
        logger.info(f"{self.agent_id}: Performing harvest")
        
        await asyncio.sleep(3)
        
        return {
            "harvest_amount_kg": 50,  # Estimate
            "success": True
        }
    
    # ==================== Task Monitoring ====================
    
    async def _monitor_active_tasks(self):
        """Monitor active tasks for timeouts or issues"""
        current_time = datetime.now()
        timeout_minutes = 30
        
        for task_id, task in list(self.active_tasks.items()):
            if task.started_at:
                elapsed = (current_time - task.started_at).total_seconds() / 60
                if elapsed > timeout_minutes:
                    logger.warning(f"{self.agent_id}: Task {task_id} timeout ({elapsed:.1f} min)")
                    task.status = TaskStatus.FAILED
                    task.error = "Task timeout"
                    task.completed_at = current_time
                    
                    del self.active_tasks[task_id]
                    self.completed_tasks.append(task)
    
    async def _cancel_task(self, task_id: str):
        """Cancel a task"""
        # Check pending tasks
        for i, task in enumerate(self.task_queue):
            if task.task_id == task_id:
                task.status = TaskStatus.CANCELLED
                self.task_queue.pop(i)
                self.completed_tasks.append(task)
                logger.info(f"{self.agent_id}: Cancelled pending task {task_id}")
                return
        
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            del self.active_tasks[task_id]
            self.completed_tasks.append(task)
            logger.info(f"{self.agent_id}: Cancelled active task {task_id}")
            return
        
        logger.warning(f"{self.agent_id}: Task {task_id} not found for cancellation")
    
    async def _send_task_status(self, task_id: str, requester: str):
        """Send task status to requester"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            await self.send_message(
                receiver=requester,
                message_type="task_status",
                content=task.to_dict(),
                priority=MessagePriority.NORMAL
            )
            return
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                await self.send_message(
                    receiver=requester,
                    message_type="task_status",
                    content=task.to_dict(),
                    priority=MessagePriority.NORMAL
                )
                return
        
        # Task not found
        await self.send_message(
            receiver=requester,
            message_type="task_not_found",
            content={"task_id": task_id},
            priority=MessagePriority.NORMAL
        )
    
    async def _send_task_list(self, requester: str):
        """Send list of all tasks to requester"""
        task_list = {
            "pending": [t.to_dict() for t in self.task_queue],
            "active": [t.to_dict() for t in self.active_tasks.values()],
            "completed_recent": [t.to_dict() for t in self.completed_tasks[-10:]]
        }
        
        await self.send_message(
            receiver=requester,
            message_type="task_list",
            content=task_list,
            priority=MessagePriority.NORMAL
        )
