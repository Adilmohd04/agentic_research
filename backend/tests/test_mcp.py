"""
Tests for MCP integration layer
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime

from src.mcp.registry import MCPToolRegistryImpl
from src.mcp.base_tool import BaseMCPTool
from shared.types.mcp import JSONSchema, ToolResult


class TestTool(BaseMCPTool):
    """Simple test tool for testing"""
    
    def __init__(self):
        super().__init__(
            name="test_tool",
            description="A simple test tool",
            category="test"
        )
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Test message"},
                "number": {"type": "number", "description": "Test number"}
            },
            "required": ["message"]
        }
    
    async def _execute_impl(self, params):
        return {
            "echo": params.get("message", ""),
            "number": params.get("number", 0),
            "timestamp": datetime.now().isoformat()
        }


class TestMCPRegistry:
    """Test MCP Registry functionality"""
    
    @pytest.fixture
    def registry(self):
        return MCPToolRegistryImpl()
    
    @pytest.fixture
    def test_tool(self):
        return TestTool()
    
    @pytest.mark.asyncio
    async def test_register_tool(self, registry, test_tool):
        """Test tool registration"""
        await registry.registerTool(test_tool)
        
        retrieved = registry.getTool("test_tool")
        assert retrieved is not None
        assert retrieved.name == "test_tool"
        assert retrieved.category == "test"
    
    @pytest.mark.asyncio
    async def test_list_tools(self, registry, test_tool):
        """Test listing tools"""
        await registry.registerTool(test_tool)
        
        all_tools = registry.listTools()
        assert len(all_tools) == 1
        assert all_tools[0].name == "test_tool"
        
        test_tools = registry.listTools(category="test")
        assert len(test_tools) == 1
        
        other_tools = registry.listTools(category="other")
        assert len(other_tools) == 0
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, registry, test_tool):
        """Test tool execution"""
        await registry.registerTool(test_tool)
        
        result = await registry.executeTool("test_tool", {"message": "hello"})
        
        assert result.success is True
        assert result.data["echo"] == "hello"
        assert "timestamp" in result.data
    
    @pytest.mark.asyncio
    async def test_validation_error(self, registry, test_tool):
        """Test parameter validation"""
        await registry.registerTool(test_tool)
        
        # Missing required parameter
        result = await registry.executeTool("test_tool", {})
        
        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self, registry):
        """Test executing non-existent tool"""
        result = await registry.executeTool("nonexistent", {})
        
        assert result.success is False
        assert result.error.code == "TOOL_NOT_FOUND"


class TestBaseTool:
    """Test base tool functionality"""
    
    @pytest.fixture
    def test_tool(self):
        return TestTool()
    
    def test_schema_definition(self, test_tool):
        """Test schema is properly defined"""
        schema = test_tool.schema
        
        assert schema["type"] == "object"
        assert "message" in schema["properties"]
        assert "message" in schema["required"]
    
    def test_validation_success(self, test_tool):
        """Test successful validation"""
        result = test_tool.validate({"message": "test", "number": 42})
        
        assert result.isValid is True
        assert len(result.errors) == 0
    
    def test_validation_missing_required(self, test_tool):
        """Test validation with missing required field"""
        result = test_tool.validate({"number": 42})
        
        assert result.isValid is False
        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "MISSING_REQUIRED"
    
    def test_validation_wrong_type(self, test_tool):
        """Test validation with wrong parameter type"""
        result = test_tool.validate({"message": 123})  # Should be string
        
        assert result.isValid is False
        assert any(error["code"] == "INVALID_TYPE" for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_execute_success(self, test_tool):
        """Test successful execution"""
        result = await test_tool.execute({"message": "test"})
        
        assert result.success is True
        assert result.data["echo"] == "test"
        assert result.metadata["toolVersion"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])