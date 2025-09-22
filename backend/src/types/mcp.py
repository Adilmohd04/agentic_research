"""
MCP (Model Context Protocol) related types and interfaces
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class ToolCategory(str, Enum):
    """Tool categories"""
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    WEB = "web"
    CODE_ANALYSIS = "code_analysis"
    SEARCH = "search"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"


@dataclass
class JSONSchema:
    """JSON Schema definition"""
    type: str
    properties: Dict[str, Any]
    required: Optional[List[str]] = None
    additionalProperties: Optional[bool] = None


@dataclass
class ValidationError:
    """Validation error"""
    field: str
    message: str
    code: str


@dataclass
class ValidationWarning:
    """Validation warning"""
    field: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Validation result"""
    isValid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]


@dataclass
class ResourceUsage:
    """Resource usage information"""
    cpuTime: float
    memoryUsed: int
    networkRequests: int
    diskOperations: int


@dataclass
class ToolError:
    """Tool execution error"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = False
    suggestedAction: Optional[str] = None


@dataclass
class ToolResultMetadata:
    """Tool result metadata"""
    executionTime: float
    timestamp: datetime
    toolVersion: str
    resourcesUsed: Optional[ResourceUsage] = None


@dataclass
class ToolResult:
    """Tool execution result"""
    success: bool
    data: Optional[Any] = None
    error: Optional[ToolError] = None
    metadata: Optional[ToolResultMetadata] = None


class MCPTool(ABC):
    """Abstract base class for MCP tools"""
    
    def __init__(self, name: str, description: str, category: ToolCategory, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.category = category
        self.version = version
        self._schema = self._define_schema()
    
    @property
    def schema(self) -> JSONSchema:
        """Get tool schema"""
        return self._schema
    
    @abstractmethod
    def _define_schema(self) -> JSONSchema:
        """Define the tool's parameter schema"""
        pass
    
    @abstractmethod
    async def execute(self, params: Any) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def validate(self, params: Any) -> ValidationResult:
        """Validate tool parameters"""
        errors = []
        warnings = []
        
        if not isinstance(params, dict):
            errors.append(ValidationError(
                field="params",
                message="Parameters must be a dictionary",
                code="INVALID_TYPE"
            ))
            return ValidationResult(isValid=False, errors=errors, warnings=warnings)
        
        # Check required fields
        if self._schema.required:
            for field in self._schema.required:
                if field not in params:
                    errors.append(ValidationError(
                        field=field,
                        message=f"Required field '{field}' is missing",
                        code="MISSING_REQUIRED"
                    ))
        
        # Check field types
        for field, value in params.items():
            if field in self._schema.properties:
                expected_type = self._schema.properties[field].get("type")
                if expected_type and not self._validate_type(value, expected_type):
                    errors.append(ValidationError(
                        field=field,
                        message=f"Field '{field}' should be of type '{expected_type}'",
                        code="INVALID_TYPE"
                    ))
        
        return ValidationResult(
            isValid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid


class MCPToolRegistry(ABC):
    """Abstract base class for MCP tool registry"""
    
    @abstractmethod
    async def registerTool(self, tool: MCPTool) -> None:
        """Register a new MCP tool"""
        pass
    
    @abstractmethod
    async def unregisterTool(self, name: str) -> None:
        """Unregister an MCP tool"""
        pass
    
    @abstractmethod
    def getTool(self, name: str) -> Optional[MCPTool]:
        """Get tool by name"""
        pass
    
    @abstractmethod
    def listTools(self, category: Optional[ToolCategory] = None) -> List[MCPTool]:
        """List all tools, optionally filtered by category"""
        pass
    
    @abstractmethod
    async def executeTool(self, name: str, params: Any) -> ToolResult:
        """Execute a tool with given parameters"""
        pass


@dataclass
class ServerCapability:
    """Server capability"""
    name: str
    version: str
    description: str


@dataclass
class AuthConfig:
    """Authentication configuration"""
    type: str  # 'none', 'api_key', 'oauth', 'jwt'
    config: Dict[str, Any]


@dataclass
class MCPServerConfig:
    """MCP Server configuration"""
    name: str
    version: str
    description: str
    tools: List[MCPTool]
    capabilities: List[ServerCapability]
    authentication: Optional[AuthConfig] = None


@dataclass
class MCPEvent:
    """MCP Event"""
    type: str  # 'tool_registered', 'tool_unregistered', 'tool_executed', 'error'
    data: Any
    timestamp: datetime


class MCPClient(ABC):
    """Abstract MCP Client interface"""
    
    @abstractmethod
    async def connect(self, server_config: MCPServerConfig) -> None:
        """Connect to MCP server"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        pass
    
    @abstractmethod
    async def listTools(self) -> List[MCPTool]:
        """List available tools"""
        pass
    
    @abstractmethod
    async def executeTool(self, name: str, params: Any) -> ToolResult:
        """Execute a tool"""
        pass
    
    @abstractmethod
    def subscribeToEvents(self, callback) -> None:
        """Subscribe to MCP events"""
        pass