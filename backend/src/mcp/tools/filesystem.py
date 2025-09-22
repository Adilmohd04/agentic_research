"""File system MCP tools"""
import os
import aiofiles
from typing import Any, Dict
from ..base_tool import BaseMCPTool
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from shared.schemas.mcp import JSONSchema

class ReadFileTool(BaseMCPTool):
    def __init__(self):
        super().__init__("read_file", "Read contents of a file", "filesystem")
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
            },
            "required": ["path"]
        }
    
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params["path"]
        encoding = params.get("encoding", "utf-8")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
            content = await f.read()
        
        return {"content": content, "path": file_path, "size": len(content), "encoding": encoding}

class WriteFileTool(BaseMCPTool):
    def __init__(self):
        super().__init__("write_file", "Write content to a file", "filesystem")
    
    def _define_schema(self) -> JSONSchema:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to write"},
                "content": {"type": "string", "description": "Content to write"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
            },
            "required": ["path", "content"]
        }
    
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params["path"]
        content = params["content"]
        encoding = params.get("encoding", "utf-8")
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
            await f.write(content)
        
        return {"path": file_path, "bytes_written": len(content.encode(encoding)), "encoding": encoding}