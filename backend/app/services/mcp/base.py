"""MCP (Model Context Protocol) base classes and protocol implementation."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPToolParameter:
    """MCP tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


@dataclass
class MCPToolResult:
    """Result from executing an MCP tool."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {"success": self.success}
        if self.data:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


class MCPTool(ABC):
    """Base class for MCP tools."""
    
    def __init__(self):
        """Initialize MCP tool."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[MCPToolParameter]:
        """Tool parameters."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> MCPToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            MCPToolResult: Execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema in MCP format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                    }
                    for param in self.parameters
                },
                "required": [
                    param.name for param in self.parameters if param.required
                ],
            },
        }
    
    async def validate_params(self, **kwargs) -> bool:
        """
        Validate tool parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        return True


class MCPServer:
    """MCP server that manages and executes tools."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.tools: Dict[str, MCPTool] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_tool(self, tool: MCPTool):
        """
        Register a tool with the server.
        
        Args:
            tool: MCPTool instance to register
        """
        self.tools[tool.name] = tool
        self.logger.info(f"Registered MCP tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            MCPTool or None if not found
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.
        
        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, **kwargs) -> MCPToolResult:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            MCPToolResult: Execution result
        """
        tool = self.get_tool(name)
        if not tool:
            return MCPToolResult(
                success=False,
                error=f"Tool not found: {name}"
            )
        
        try:
            # Validate parameters
            await tool.validate_params(**kwargs)
            
            # Execute tool
            self.logger.info(f"Executing tool: {name}")
            result = await tool.execute(**kwargs)
            
            self.logger.info(
                f"Tool execution completed: {name}, "
                f"success={result.success}"
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Tool execution failed: {name}, error={str(e)}")
            return MCPToolResult(
                success=False,
                error=str(e)
            )


# Global MCP server instance
mcp_server = MCPServer()
