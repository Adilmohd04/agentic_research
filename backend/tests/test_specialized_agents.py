"""
Tests for specialized agents
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.coordinator import CoordinatorAgent
from src.agents.researcher import ResearcherAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.executor import ExecutorAgent
from src.agents.crew_setup import AgentCrew
from src.core.memory import TaskRecord


class TestSpecializedAgents:
    """Test specialized agent functionality"""
    
    @pytest.fixture
    async def coordinator(self):
        agent = CoordinatorAgent()
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.fixture
    async def researcher(self):
        agent = ResearcherAgent()
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.fixture
    async def analyzer(self):
        agent = AnalyzerAgent()
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.fixture
    async def executor(self):
        agent = ExecutorAgent()
        await agent.initialize()
        yield agent
        await agent.shutdown()
    
    @pytest.mark.asyncio
    async def test_coordinator_task_planning(self, coordinator):
        """Test coordinator task planning"""
        task = TaskRecord(
            task_id="coord-test-1",
            type="coordination",
            description="Plan a research project on AI trends",
            status="pending",
            assigned_agent=coordinator.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await coordinator.process_task(task)
        
        assert "coordination_plan" in result
        assert "subtasks" in result["coordination_plan"]
        assert len(result["coordination_plan"]["subtasks"]) > 0
    
    @pytest.mark.asyncio
    async def test_researcher_information_gathering(self, researcher):
        """Test researcher information gathering"""
        task = TaskRecord(
            task_id="research-test-1",
            type="research",
            description="Research AI trends in healthcare",
            status="pending",
            assigned_agent=researcher.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await researcher.process_task(task)
        
        assert "research_results" in result
        assert "sources" in result
        assert "citations" in result
        assert result["research_results"]["confidence_score"] > 0
    
    @pytest.mark.asyncio
    async def test_analyzer_data_analysis(self, analyzer):
        """Test analyzer data analysis"""
        task = TaskRecord(
            task_id="analysis-test-1",
            type="analysis",
            description="Analyze market trends data",
            status="pending",
            assigned_agent=analyzer.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await analyzer.process_task(task)
        
        assert "analysis_results" in result
        assert "statistical_analysis" in result["analysis_results"]
        assert "bias_analysis" in result["analysis_results"]
        assert "confidence_assessment" in result["analysis_results"]
    
    @pytest.mark.asyncio
    async def test_executor_code_generation(self, executor):
        """Test executor code generation"""
        task = TaskRecord(
            task_id="exec-test-1",
            type="code_generation",
            description="Generate a Python function for data processing",
            status="pending",
            assigned_agent=executor.agent_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await executor.process_task(task)
        
        assert "code_generation_results" in result
        assert "generated_code" in result["code_generation_results"]
        assert "test_code" in result["code_generation_results"]
        assert "documentation" in result["code_generation_results"]


class TestAgentCrew:
    """Test agent crew coordination"""
    
    @pytest.fixture
    async def crew(self):
        crew = AgentCrew()
        yield crew
        if crew.initialized:
            await crew.shutdown_crew()
    
    @pytest.mark.asyncio
    async def test_crew_initialization(self, crew):
        """Test crew initialization"""
        result = await crew.initialize_crew()
        
        assert result["status"] == "initialized"
        assert result["total_agents"] == 4
        assert crew.initialized is True
    
    @pytest.mark.asyncio
    async def test_research_workflow(self, crew):
        """Test complete research workflow"""
        await crew.initialize_crew()
        
        result = await crew.execute_research_workflow(
            topic="AI in healthcare",
            session_id="test-session"
        )
        
        assert result["workflow"] == "research"
        assert result["status"] == "completed"
        assert "results" in result
        assert len(result["results"]) == 4  # 4 workflow steps
    
    @pytest.mark.asyncio
    async def test_crew_status(self, crew):
        """Test crew status reporting"""
        await crew.initialize_crew()
        
        status = await crew.get_crew_status()
        
        assert status["crew_status"] == "operational"
        assert "orchestrator_status" in status
        assert "agent_details" in status
        assert len(status["agent_details"]) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])