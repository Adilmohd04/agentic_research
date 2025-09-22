"""Base MCP Tool implementation"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime
from ..types.mcp import MCPTool, ToolResult, ValidationResult, ToolError, JSONSchema

class BaseMCPTool(MCPTool):
    def __init__(self, name: str, description: str, category: str, version: str = "1.0.0"):
        from ..types.mcp import ToolCategory
        super().__init__(name, description, ToolCategory(category), version)
    
    @abstractmethod
    def _define_schema(self) -> JSONSchema:
        pass
    
    @abstractmethod
    async def _execute_impl(self, params: Any) -> Any:
        pass
    
    async def execute(self, params: Any) -> ToolResult:
        start_time = datetime.now()
        try:
            validation = self.validate(params)
            if not validation.isValid:
                from ..types.mcp import ToolResultMetadata
                return ToolResult(
                    success=False,
                    error=ToolError(code="VALIDATION_ERROR", message=f"Validation failed: {validation.errors}", recoverable=True),
                    metadata=ToolResultMetadata(executionTime=0, timestamp=start_time, toolVersion=self.version)
                )
            
            result_data = await self._execute_impl(params)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            from ..types.mcp import ToolResultMetadata
            return ToolResult(
                success=True,
                data=result_data,
                metadata=ToolResultMetadata(executionTime=execution_time, timestamp=start_time, toolVersion=self.version)
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            from ..types.mcp import ToolResultMetadata
            return ToolResult(
                success=False,
                error=ToolError(code="EXECUTION_ERROR", message=str(e), recoverable=False),
                metadata=ToolResultMetadata(executionTime=execution_time, timestamp=start_time, toolVersion=self.version)
            )
    
    def validate(self, params: Any) -> ValidationResult:
        from ..types.mcp import ValidationError
        errors = []
        if not isinstance(params, dict):
            errors.append(ValidationError(field="params", message="Parameters must be a dictionary", code="INVALID_TYPE"))
            return ValidationResult(isValid=False, errors=errors, warnings=[])
        
        required = self.schema.required or []
        for field in required:
            if field not in params:
                errors.append(ValidationError(field=field, message=f"Required field '{field}' is missing", code="MISSING_REQUIRED"))
        
        return ValidationResult(isValid=len(errors) == 0, errors=errors, warnings=[])