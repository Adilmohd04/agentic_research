"""
Base Agent Class for Multi-Agent System
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, role: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.role = role
        self.capabilities = capabilities
        self.status = "ready"
        self.current_tasks = []
        self.task_history = []
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return results"""
        pass
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with logging and error handling"""
        task_id = task.get("task_id", str(uuid.uuid4()))
        
        try:
            self.status = "busy"
            self.current_tasks.append(task_id)
            self.last_active = datetime.utcnow()
            
            logger.info(f"Agent {self.agent_id} starting task {task_id}")
            
            # Process the task
            result = await self.process_task(task)
            
            # Add metadata
            result.update({
                "agent_id": self.agent_id,
                "task_id": task_id,
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed"
            })
            
            # Update history
            self.task_history.append({
                "task_id": task_id,
                "task": task,
                "result": result,
                "completed_at": datetime.utcnow()
            })
            
            logger.info(f"Agent {self.agent_id} completed task {task_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed task {task_id}: {str(e)}")
            return {
                "agent_id": self.agent_id,
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
        finally:
            self.status = "ready"
            if task_id in self.current_tasks:
                self.current_tasks.remove(task_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "capabilities": self.capabilities,
            "current_tasks": len(self.current_tasks),
            "total_tasks_completed": len(self.task_history),
            "last_active": self.last_active.isoformat(),
            "uptime": (datetime.utcnow() - self.created_at).total_seconds()
        }