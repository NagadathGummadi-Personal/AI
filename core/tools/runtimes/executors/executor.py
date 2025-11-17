"""
Executor Interface for Tools Specification System.

This module defines the interface for tool execution strategies.
"""

from typing import Protocol, Dict, Any, runtime_checkable, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ...spec.tool_result import ToolResult
    from ...spec.tool_context import ToolContext


@runtime_checkable
class IExecutor(Protocol):
    """
    Interface for tool execution strategies.
    
    All executors must implement this interface to provide tool execution
    functionality.
    
    Methods:
        execute: Execute the tool with given arguments and context
        
    Usage:
        class CustomExecutor:
            async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
                # Your execution logic
                pass
    """
    
    async def execute(self, args: Dict[str, Any], ctx: "ToolContext") -> "ToolResult":
        """
        Execute the tool with given arguments and context.
        
        Args:
            args: Tool arguments
            ctx: Execution context with tracing, auth, and dependencies
            
        Returns:
            ToolResult with execution output and usage statistics
            
        Raises:
            ToolError: If execution fails
        """
        ...

