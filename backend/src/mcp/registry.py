"""
MCP Tool Registry - Central registry for all MCP tools
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..types.mcp import MCPTool, ToolResult, ToolError, ValidationResult, ToolResultMetadata, ValidationError

import logging

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Abstract base class for MCP tool registry"""
    
    async def registerTool(self, tool: MCPTool) -> None:
        """Register a new MCP tool"""
        raise NotImplementedError
    
    async def unregisterTool(self, name: str) -> None:
        """Unregister an MCP tool"""
        raise NotImplementedError
    
    def getTool(self, name: str) -> Optional[MCPTool]:
        """Get tool by name"""
        raise NotImplementedError
    
    def listTools(self, category: Optional[str] = None) -> List[MCPTool]:
        """List all tools, optionally filtered by category"""
        raise NotImplementedError
    
    async def executeTool(self, name: str, params: Any) -> ToolResult:
        """Execute a tool with given parameters"""
        raise NotImplementedError


class MCPToolRegistryImpl(MCPToolRegistry):
    """Implementation of MCP tool registry"""
    
    def __init__(self):
        """Initialize the registry"""
        self._tools: Dict[str, MCPTool] = {}
        self._execution_history: List[Dict[str, Any]] = []
    
    async def registerTool(self, tool: MCPTool) -> None:
        """Register a new MCP tool"""
        self._tools[tool.name] = tool
        print(f"✅ Registered MCP tool: {tool.name}")
    
    async def unregisterTool(self, name: str) -> None:
        """Unregister an MCP tool"""
        if name in self._tools:
            del self._tools[name]
            print(f"❌ Unregistered MCP tool: {name}")
    
    def getTool(self, name: str) -> Optional[MCPTool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def listTools(self, category: Optional[str] = None) -> List[MCPTool]:
        """List all tools, optionally filtered by category"""
        tools = list(self._tools.values())
        if category:
            tools = [tool for tool in tools if tool.category == category]
        return tools
    
    async def executeTool(self, name: str, params: Any) -> ToolResult:
        """Execute a tool with given parameters"""
        tool = self.getTool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=ToolError(
                    code="TOOL_NOT_FOUND",
                    message=f"Tool '{name}' not found",
                    recoverable=False
                ),
                metadata=ToolResultMetadata(
                    executionTime=0,
                    timestamp=datetime.now(),
                    toolVersion="unknown"
                )
            )
        
        # Validate parameters
        validation = tool.validate(params)
        if not validation.isValid:
            return ToolResult(
                success=False,
                error=ToolError(
                    code="VALIDATION_ERROR",
                    message=f"Parameter validation failed: {validation.errors}",
                    recoverable=True
                ),
                metadata=ToolResultMetadata(
                    executionTime=0,
                    timestamp=datetime.now(),
                    toolVersion=tool.version
                )
            )
        
        # Execute tool
        start_time = datetime.now()
        try:
            result = await tool.execute(params)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log execution
            self._execution_history.append({
                "tool_name": name,
                "params": params,
                "success": result.success,
                "timestamp": start_time.isoformat(),
                "execution_time": execution_time
            })
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                success=False,
                error=ToolError(
                    code="EXECUTION_ERROR",
                    message=str(e),
                    recoverable=False
                ),
                metadata=ToolResultMetadata(
                    executionTime=execution_time,
                    timestamp=start_time,
                    toolVersion=tool.version
                )
            )
    
    def validateToolParams(self, name: str, params: Any) -> ValidationResult:
        """Validate tool parameters"""
        tool = self.getTool(name)
        if not tool:
            return ValidationResult(
                isValid=False,
                errors=[ValidationError(field="tool", message=f"Tool '{name}' not found", code="NOT_FOUND")],
                warnings=[]
            )
        
        return tool.validate(params)
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export registry configuration"""
        return {
            "tools": {name: tool.name for name, tool in self._tools.items()},
            "tool_count": len(self._tools),
            "exported_at": datetime.now().isoformat()
        }


# Global registry instance
mcp_registry = MCPToolRegistryImpl()