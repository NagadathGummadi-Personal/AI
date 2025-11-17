"""
Function Executor Interface for Tools Specification System.

This module defines the interface for function-based tool executors that execute
user-provided async functions with full observability and control.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult


class IFunctionExecutor(ABC):
    """
    Interface for function-based tool executors.
    
    Function executors handle execution of user-provided async functions with
    validation, authorization, idempotency, and metrics collection.
    
    Methods:
        execute: Execute a function-based tool
    
    Implementing Classes:
        FunctionToolExecutor: Standard function executor
        CustomFunctionExecutor: Custom implementations
    
    Example Implementation:
        class CustomFunctionExecutor(IFunctionExecutor):
            async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
                # Custom function execution logic
                result = await self.func(args)
                return ToolResult(content=result, tool_name=self.spec.tool_name)
    """
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """
        Execute a function-based tool.
        
        Args:
            args: Function arguments as dictionary
            ctx: Tool execution context containing:
                - user_id: User identifier
                - session_id: Session identifier
                - trace_id: Trace identifier
                - memory: Memory interface
                - metrics: Metrics interface
                
        Returns:
            ToolResult containing:
                - content: Function result data
                - tool_name: Name of the tool
                - error: Error information if function failed
                - usage: Resource usage information
                
        Raises:
            ValidationError: If arguments are invalid
            PermissionError: If authorization fails
            TimeoutError: If function times out
            Exception: Function-specific errors
        
        Example:
            executor = FunctionToolExecutor(spec, my_function)
            result = await executor.execute({'x': 10, 'y': 20}, ctx)
            
            if result.error:
                print(f"Error: {result.error}")
            else:
                print(f"Result: {result.content}")
        """
        pass

