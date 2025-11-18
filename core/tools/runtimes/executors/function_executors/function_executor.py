"""
Function Tool Executor for Tools Specification System.

This module provides the executor for function-based tools that execute
user-provided async functions with full observability and control.

Classes:
========
- FunctionToolExecutor: Executor for function-based tools

Inheritance:
============
BaseToolExecutor
└── FunctionToolExecutor (this class)

Responsibilities:
=================
- Execute user-provided async functions
- Validation, authorization, and egress checks
- Idempotency handling
- Timeout and rate limiting
- Distributed tracing
- Metrics collection
- Error handling and result formatting

Usage:
    from core.tools.executors import FunctionToolExecutor
    from core.tools.spec.tool_types import FunctionToolSpec
    
    # Define your async function
    async def my_function(args):
        result = args['x'] + args['y']
        return {'result': result}
    
    # Create tool spec
    spec = FunctionToolSpec(
        id="add-numbers-v1",
        tool_name="add",
        description="Add two numbers",
        tool_type=ToolType.FUNCTION,
        parameters=[...]
    )
    
    # Create executor
    executor = FunctionToolExecutor(spec, my_function)
    
    # Execute
    result = await executor.execute({'x': 10, 'y': 20}, ctx)

Note:
    - Function must be async and accept a Dict[str, Any] argument
    - Function should return serializable data (dict, list, str, int, etc.)
    - Exceptions raised by function are caught and returned as ToolError
"""

# Standard library
import time
import asyncio
from typing import Any, Awaitable, Callable, Dict

# Local imports
from .base_function_executor import BaseFunctionExecutor
from ....spec.tool_types import ToolSpec
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult
from ....constants import (
    LOG_STARTING_EXECUTION,
    LOG_PARAMETERS,
    LOG_VALIDATING,
    LOG_VALIDATION_PASSED,
    LOG_VALIDATION_SKIPPED,
    LOG_AUTH_CHECK,
    LOG_AUTH_PASSED,
    LOG_AUTH_SKIPPED,
    LOG_EGRESS_CHECK,
    LOG_EGRESS_PASSED,
    LOG_EGRESS_SKIPPED,
    LOG_IDEMPOTENCY_CACHE_HIT,
    LOG_EXECUTION_COMPLETED,
    LOG_EXECUTION_FAILED,
    IDEMPOTENCY_CACHE_PREFIX,
    TOOL_EXECUTION_TIME,
    TOOL_EXECUTIONS,
    STATUS,
    SUCCESS,
    TOOL,
    ERROR,
    EXECUTION_FAILED,
)
from ....defaults import DEFAULT_TOOL_CONTEXT_DATA
from utils.logging.LoggerAdaptor import LoggerAdaptor


class FunctionToolExecutor(BaseFunctionExecutor):
    """
    Executor for function-based tools.
    
    Executes user-provided async functions using the Template Method pattern.
    The base class handles validation, security, idempotency, and metrics.
    This class only implements the actual function execution logic.
    
    Attributes:
        spec: Tool specification
        func: Async function to execute
        logger: Logger instance (inherited from base)
    
    Function Requirements:
        - Must be async: async def my_func(args)
        - Must accept Dict[str, Any] as argument
        - Should return serializable data
        - Exceptions are caught and handled by base class
    
    Example:
        async def division(args):
            numerator = args['numerator']
            denominator = args['denominator']
            if denominator == 0:
                raise ValueError("Division by zero")
            return {'result': numerator / denominator}
        
        spec = FunctionToolSpec(...)
        executor = FunctionToolExecutor(spec, division)
        result = await executor.execute({'numerator': 10, 'denominator': 2}, ctx)
    """
    
    async def _execute_function(
        self,
        args: Dict[str, Any],
        ctx: ToolContext,
        timeout: float
    ) -> Any:
        """
        Execute the actual user function with timeout and optional rate limiting/tracing.
        
        This is the only method that concrete function executors need to implement.
        The base class handles all validation, security, idempotency, and metrics.
        
        Args:
            args: Function arguments (already validated)
            ctx: Tool execution context
            timeout: Maximum execution time in seconds
            
        Returns:
            Function result (will be wrapped in ToolResult by base class)
            
        Raises:
            Any exception from the user function (will be handled by base class)
        """
        # Helper to invoke function with optional tracing
        async def _invoke() -> Any:
            if ctx.tracer:
                async with ctx.tracer.span(f"{self.spec.tool_name}.execute", {"tool": self.spec.tool_name}):
                    return await self.func(args)
            return await self.func(args)
        
        # Execute with optional rate limiting and timeout
        if ctx.limiter:
            async with ctx.limiter.acquire(self.spec.tool_name):
                if timeout:
                    return await asyncio.wait_for(_invoke(), timeout=timeout)
                return await _invoke()
        else:
            if timeout:
                return await asyncio.wait_for(_invoke(), timeout=timeout)
            return await _invoke()

