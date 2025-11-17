"""
Base Function Executor for Tools Specification System.

This module provides the base class for all function tool executors. It handles
common function execution patterns including validation, authorization, function
wrapping, error handling, and metrics collection.

Classes:
========
- BaseFunctionExecutor: Abstract base class for all function executors

Inheritance Hierarchy:
======================
BaseToolExecutor (from base_executor.py)
└── BaseFunctionExecutor (this file)
    ├── FunctionToolExecutor (standard)
    ├── CachedFunctionExecutor (future)
    ├── StreamingFunctionExecutor (future)
    └── [Your Custom Executors]

Responsibilities:
=================
- Function-specific logging setup
- Common validation/auth flow for functions
- Function invocation with error handling
- Result formatting and wrapping
- Metrics and tracing integration
- Delegates actual function execution to subclasses

Usage:
    class MyFunctionExecutor(BaseFunctionExecutor):
        def __init__(self, spec: ToolSpec, func: Callable):
            super().__init__(spec)
            self.func = func
        
        async def _execute_function(self, args, ctx, timeout):
            # Your specific function execution logic
            result = await asyncio.wait_for(
                self.func(args, ctx),
                timeout=timeout
            )
            return result

Note:
    Subclasses must implement _execute_function() method.
"""

# Standard library
import time
import asyncio
from abc import abstractmethod
from typing import Any, Dict, Callable, Awaitable

# Local imports
from ..base_executor import BaseToolExecutor
from ....spec.tool_types import ToolSpec
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult


class BaseFunctionExecutor(BaseToolExecutor):
    """
    Base executor for function-based tools.
    
    Provides common functionality for executing user-provided functions
    with observability, error handling, and metrics collection.
    
    Attributes:
        spec: Tool specification
        func: The async function to execute
    """
    
    def __init__(self, spec: ToolSpec, func: Callable[[Dict[str, Any], ToolContext], Awaitable[Any]]):
        """
        Initialize the base function executor.
        
        Args:
            spec: Tool specification
            func: Async function to execute. Must accept (args: Dict, ctx: ToolContext)
                 and return Any
        
        Raises:
            TypeError: If func is not callable
        """
        super().__init__(spec)
        
        if not callable(func):
            raise TypeError(f"Function must be callable, got {type(func)}")
        
        self.func = func
    
    async def _execute_impl(
        self,
        args: Dict[str, Any],
        ctx: ToolContext
    ) -> ToolResult:
        """
        Execute the function-based tool.
        
        This is the main execution flow that:
        1. Logs execution start
        2. Executes the function with timeout
        3. Handles errors and formats results
        4. Collects metrics
        
        Args:
            args: Input arguments (already validated)
            ctx: Tool execution context
            
        Returns:
            ToolResult with function execution results
            
        Raises:
            ToolError: If function execution fails
        """
        start_time = time.time()
        
        # Get timeout
        timeout = self.spec.timeout_s or 30
        
        try:
            # Execute the function (delegates to subclass)
            result = await self._execute_function(args, ctx, timeout)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Collect metrics
            if ctx.metrics:
                await ctx.metrics.timing_ms(
                    "function_execution_duration",
                    int(duration * 1000),
                    tags={
                        "tool_name": self.spec.tool_name,
                        "status": "success"
                    }
                )
                await ctx.metrics.incr(
                    "function_executions",
                    tags={"tool_name": self.spec.tool_name, "status": "success"}
                )
            
            # Format and return result
            return await self._format_result(result, ctx)
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            
            # Collect timeout metrics
            if ctx.metrics:
                await ctx.metrics.incr(
                    "function_executions",
                    tags={"tool_name": self.spec.tool_name, "status": "timeout"}
                )
            
            from ....spec.tool_types import ToolError
            raise ToolError(
                f"Function execution timed out after {duration:.2f}s (limit: {timeout}s)",
                retryable=False,
                code="FUNCTION_TIMEOUT"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Collect error metrics
            if ctx.metrics:
                await ctx.metrics.incr(
                    "function_executions",
                    tags={
                        "tool_name": self.spec.tool_name,
                        "status": "error",
                        "error_type": type(e).__name__
                    }
                )
            
            # Re-raise ToolError as-is, wrap others
            from ....spec.tool_types import ToolError
            if isinstance(e, ToolError):
                raise
            
            raise ToolError(
                f"Function execution failed: {str(e)}",
                retryable=self._is_retryable_error(e),
                code="FUNCTION_EXECUTION_ERROR"
            ) from e
    
    @abstractmethod
    async def _execute_function(
        self,
        args: Dict[str, Any],
        ctx: ToolContext,
        timeout: float
    ) -> Any:
        """
        Execute the actual function.
        
        This method must be implemented by subclasses to define
        how the function is invoked.
        
        Args:
            args: Input arguments
            ctx: Tool context
            timeout: Timeout in seconds
            
        Returns:
            Function execution result
            
        Raises:
            Exception: Any error from function execution
        """
        pass
    
    async def _format_result(
        self,
        result: Any,
        ctx: ToolContext
    ) -> ToolResult:
        """
        Format the function result into a ToolResult.
        
        Args:
            result: Raw function result
            ctx: Tool context
            
        Returns:
            Formatted ToolResult
        """
        # If result is already a dict, use it as content
        if isinstance(result, dict):
            content = result
        else:
            # Wrap non-dict results
            content = {"result": result}
        
        return ToolResult(
            return_type=self.spec.return_type,
            return_target=self.spec.return_target,
            content=content,
            metadata={
                "tool_name": self.spec.tool_name,
                "executor": "BaseFunctionExecutor"
            }
        )
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the error should be retried
        """
        # Network errors, timeouts, and temporary failures are retryable
        retryable_types = (
            asyncio.TimeoutError,
            ConnectionError,
            TimeoutError,
        )
        
        return isinstance(error, retryable_types)

