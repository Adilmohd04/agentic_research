"""
Tests for Executor Agent
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.executor import ExecutorAgent
from src.core.memory import TaskRecord


class TestExecutorAgent:
    """Test Executor Agent functionality"""
    
    @pytest.fixture
    def executor_agent(self):
        return ExecutorAgent()
    
    @pytest.fixture
    def code_generation_task(self):
        return TaskRecord(
            task_id="test-code-gen-001",
            type="code_generation",
            description="Generate a Python FastAPI application with authentication",
            priority="medium",
            status="pending",
            created_at=datetime.now(),
            agent_id="executor-001"
        )
    
    @pytest.fixture
    def diff_generation_task(self):
        return TaskRecord(
            task_id="test-diff-gen-001",
            type="diff_generation",
            description="Generate diff for code changes in main.py",
            priority="medium",
            status="pending",
            created_at=datetime.now(),
            agent_id="executor-001"
        )
    
    @pytest.fixture
    def report_generation_task(self):
        return TaskRecord(
            task_id="test-report-gen-001",
            type="report_generation",
            description="Compile research report with analysis and citations",
            priority="high",
            status="pending",
            created_at=datetime.now(),
            agent_id="executor-001"
        )
    
    def test_agent_initialization(self, executor_agent):
        """Test agent initialization"""
        assert executor_agent.agent_id == "executor-001"
        assert executor_agent.role == "executor"
        assert "output_formatting" in executor_agent.capabilities
        assert "code_generation" in executor_agent.capabilities
        assert "diff_generation" in executor_agent.capabilities
        assert "report_compilation" in executor_agent.capabilities
    
    @pytest.mark.asyncio
    async def test_code_generation(self, executor_agent, code_generation_task):
        """Test code generation functionality"""
        result = await executor_agent.process_task(code_generation_task)
        
        assert "code_generation" in result
        assert "generated_code" in result["code_generation"]
        assert "documentation" in result["code_generation"]
        assert result["code_generation"]["language"] == "python"
        
        # Check that main file was generated
        generated_code = result["code_generation"]["generated_code"]
        assert "main.py" in generated_code
        assert "fastapi" in generated_code["main.py"].lower()
    
    @pytest.mark.asyncio
    async def test_diff_generation(self, executor_agent, diff_generation_task):
        """Test diff generation functionality"""
        result = await executor_agent.process_task(diff_generation_task)
        
        assert "diff_generation" in result
        assert "unified_diff" in result["diff_generation"]
        assert "side_by_side_diff" in result["diff_generation"]
        assert "change_analysis" in result["diff_generation"]
        assert "change_explanation" in result["diff_generation"]
    
    @pytest.mark.asyncio
    async def test_report_compilation(self, executor_agent, report_generation_task):
        """Test report compilation functionality"""
        result = await executor_agent.process_task(report_generation_task)
        
        assert "report_compilation" in result
        assert "compiled_report" in result["report_compilation"]
        assert "export_formats" in result["report_compilation"]
        assert "report_metadata" in result["report_compilation"]
        
        # Check report structure
        compiled_report = result["report_compilation"]["compiled_report"]
        assert "# Research Report" in compiled_report
        assert "## Executive Summary" in compiled_report
    
    def test_parse_code_requirements(self, executor_agent):
        """Test parsing code requirements from description"""
        description = "Generate a Python FastAPI application with database and authentication features"
        requirements = executor_agent._parse_code_requirements(description)
        
        assert requirements["language"] == "python"
        assert requirements["framework"] == "fastapi"
        assert "api" in requirements["features"]
        assert "database" in requirements["features"]
        assert "authentication" in requirements["features"]
    
    def test_create_code_structure(self, executor_agent):
        """Test creating code structure"""
        requirements = {
            "language": "python",
            "framework": "fastapi",
            "features": ["api", "database"],
            "include_tests": True
        }
        
        structure = executor_agent._create_code_structure(requirements)
        
        assert structure["main_file"] == "main.py"
        assert "api.py" in structure["modules"]
        assert "database.py" in structure["modules"]
        assert len(structure["tests"]) > 0
    
    def test_analyze_code_changes(self, executor_agent):
        """Test analyzing code changes"""
        original = "print('Hello')\n"
        modified = "print('Hello World')\nprint('Updated!')\n"
        
        analysis = executor_agent._analyze_code_changes(original, modified)
        
        assert analysis["lines_added"] == 1
        assert analysis["change_type"] == "modification"
        assert analysis["complexity"] == "low"
    
    def test_generate_change_explanation(self, executor_agent):
        """Test generating change explanations"""
        change_analysis = {
            "change_type": "modification",
            "lines_added": 2,
            "lines_removed": 0,
            "complexity": "low"
        }
        
        explanation = executor_agent._generate_change_explanation(change_analysis)
        
        assert "modification" in explanation
        assert "2 line(s) added" in explanation
        assert "0 line(s) removed" in explanation
    
    def test_parse_report_requirements(self, executor_agent):
        """Test parsing report requirements"""
        description = "Generate a research report in PDF format with analysis and citations"
        requirements = executor_agent._parse_report_requirements(description)
        
        assert requirements["type"] == "research"
        assert requirements["format"] == "pdf"
        assert requirements["include_citations"] is True
    
    def test_convert_markdown_to_html(self, executor_agent):
        """Test markdown to HTML conversion"""
        markdown = "# Title\n\n## Section\n\n**Bold text**"
        html = executor_agent._convert_markdown_to_html(markdown)
        
        assert "<h1>Title</h1>" in html
        assert "<h2>Section</h2>" in html
        assert "<strong>Bold text</strong>" in html
    
    def test_convert_report_to_json(self, executor_agent):
        """Test report to JSON conversion"""
        report = "# Test Report\n\n## Summary\n\nThis is a test."
        json_str = executor_agent._convert_report_to_json(report)
        
        import json
        data = json.loads(json_str)
        
        assert data["title"] == "Test Report"
        assert "summary" in data
    
    def test_apply_formatting(self, executor_agent):
        """Test applying formatting to data"""
        data = '{"test": "value"}'
        requirements = {"format": "json"}
        
        formatted = executor_agent._apply_formatting(data, requirements)
        
        # Should be properly formatted JSON
        import json
        parsed = json.loads(formatted)
        assert parsed["test"] == "value"
    
    def test_validate_formatting(self, executor_agent):
        """Test formatting validation"""
        valid_json = '{"test": "value"}'
        invalid_json = '{"test": value}'
        
        # Test valid JSON
        validation = executor_agent._validate_formatting(valid_json, {"format": "json"})
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        
        # Test invalid JSON
        validation = executor_agent._validate_formatting(invalid_json, {"format": "json"})
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
    
    def test_determine_execution_type(self, executor_agent):
        """Test determining execution type from description"""
        assert executor_agent._determine_execution_type("generate code for API") == "code"
        assert executor_agent._determine_execution_type("create diff for changes") == "diff"
        assert executor_agent._determine_execution_type("compile research report") == "report"
        assert executor_agent._determine_execution_type("format output data") == "format"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])