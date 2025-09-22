"""
Tests for agent system
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.agents.orchestrator import AgentOrchestrator
from src.core.memory import TaskRecord


class TestAgent(BaseAgent):
    """Simple test agent"""
    
    def __init__(self, agent_id: str = "test-agent"):
        super().__init__(
            agent_id=agent_id,
            role="test",
            capabilities=["testing"],
            tools=["read_file", "write_file"]
        )
    
    async def process_task(self, task: TaskRecord):
        """Simple task processing"""
        return {
            "message": f"Processed task: {task.description}",
            "task_id": task.task_id,
            "agent_id": self.agent_id
        }


class TestAgentSystem:
    """Test agent system functionality"""
    
    @pytest.fixture
    async def test_agent(self):
        agent = TestAgent()
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.fixture
    async def orchestrator_with_agent(self):
        orch = AgentOrchestrator()
        agent = TestAgent()
        await orch.register_agent(agent)
        yield orch, agent
        await orch.shutdown_all()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_agent):
        """Test agent initialization"""
        assert test_agent.is_active is True
        assert test_agent.agent_id == "test-agent"
        assert test_agent.role == "test"
    
    @pytest.mark.asyncio
    async def test_task_execution(self, test_agent):
        """Test task execution"""
        task = TaskRecord(
            task_id="test-task-1",
            type="test",
            description="Test task",
            status="pending",
            assigned_agent=test_agent.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await test_agent.execute_task(task)
        
        assert result["message"] == "Processed task: Test task"
        assert result["task_id"] == "test-task-1"
        assert result["agent_id"] == test_agent.agent_id
    
    @pytest.mark.asyncio
    async def test_orchestrator_task_delegation(self, orchestrator_with_agent):
        """Test orchestrator task delegation"""
        orch, agent = orchestrator_with_agent
        
        result = await orch.delegate_task(
            task_type="test",
            description="Test orchestrator task",
            context={"test": True}
        )
        
        assert "message" in result
        assert "Test orchestrator task" in result["message"]
    
    @pytest.mark.asyncio
    async def test_system_status(self, orchestrator_with_agent):
        """Test system status"""
        orch, agent = orchestrator_with_agent
        
        status = await orch.get_system_status()
        
        assert status["total_agents"] == 1
        assert status["active_agents"] == 1
        assert len(status["agents"]) == 1
        assert status["agents"][0]["role"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])