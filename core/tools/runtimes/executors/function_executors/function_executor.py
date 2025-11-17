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
from ..base_executor import BaseToolExecutor
from ....interfaces.tool_interfaces import IToolExecutor
from .function_executor_interface import IFunctionExecutor
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


class FunctionToolExecutor(BaseToolExecutor, IFunctionExecutor, IToolExecutor):
    """
    Executor for function-based tools.
    
    Executes user-provided async functions with full observability, control,
    and integration with the tools specification system.
    
    Attributes:
        spec: Tool specification
        func: Async function to execute
        logger: Logger instance
    
    Methods:
        execute: Main execution method with full lifecycle management
    
    Function Requirements:
        - Must be async: async def my_func(args)
        - Must accept Dict[str, Any] as argument
        - Should return serializable data
        - Exceptions are caught and handled gracefully
    
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
    
    def __init__(self, spec: ToolSpec, func: Callable[[Dict[str, Any]], Awaitable[Any]]):
        """
        Initialize function tool executor.
        
        Args:
            spec: Tool specification
            func: Async function to execute (must accept Dict[str, Any])
        """
        super().__init__(spec)
        self.func = func
        self.logger = LoggerAdaptor.get_logger(f"{TOOL}.{spec.tool_name}")
    
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """
        Execute the function tool with full lifecycle management.
        
        Execution Flow:
        1. Log execution start
        2. Validate parameters (if validator available)
        3. Authorize execution (if security available)
        4. Check egress permissions (if security available)
        5. Check idempotency cache (if enabled)
        6. Execute user function with timeout/rate limiting
        7. Record metrics and logs
        8. Cache result (if idempotency enabled)
        9. Handle errors gracefully
        
        Args:
            args: Function arguments
            ctx: Tool execution context
            
        Returns:
            ToolResult containing function output and metadata
        """
        start_time = time.time()
        
        # Set up logging context
        context_data = DEFAULT_TOOL_CONTEXT_DATA(self.spec, ctx)
        
        # Log execution start with context
        self.logger.info(LOG_STARTING_EXECUTION, **context_data)
        
        # Log parameter details
        self.logger.debug(LOG_PARAMETERS, parameters=args, **context_data)
        
        try:
            # Validate parameters if validator is available
            if ctx.validator:
                self.logger.info(LOG_VALIDATING, **context_data)
                await ctx.validator.validate(args, self.spec)
                self.logger.info(LOG_VALIDATION_PASSED, **context_data)
            else:
                self.logger.warning(LOG_VALIDATION_SKIPPED, **context_data)
            
            # Authorize execution if security is available
            if ctx.security:
                self.logger.info(LOG_AUTH_CHECK, **context_data)
                await ctx.security.authorize(ctx, self.spec)
                self.logger.info(LOG_AUTH_PASSED, **context_data)
            else:
                self.logger.warning(LOG_AUTH_SKIPPED, **context_data)
            
            # Check egress permissions if security is available
            if ctx.security:
                self.logger.info(LOG_EGRESS_CHECK, **context_data)
                await ctx.security.check_egress(args, self.spec)
                self.logger.info(LOG_EGRESS_PASSED, **context_data)
            else:
                self.logger.warning(LOG_EGRESS_SKIPPED, **context_data)
            
            # Check idempotency if enabled
            bypass_idempotency = False
            if self.spec.idempotency.enabled and ctx.memory:
                # If key_fields are defined and bypass_on_missing_key is True, and any key is missing, bypass idempotency
                if self.spec.idempotency.key_fields and self.spec.idempotency.bypass_on_missing_key:
                    missing = [k for k in self.spec.idempotency.key_fields if k not in args]
                    if missing:
                        bypass_idempotency = True
                if not bypass_idempotency:
                    idempotency_key = self._generate_idempotency_key(args, ctx)
                    ctx.idempotency_key = idempotency_key
                    # Try to get cached result
                    if self.spec.idempotency.persist_result:
                        cached_result = await ctx.memory.get(f"{IDEMPOTENCY_CACHE_PREFIX}:{idempotency_key}")
                        if cached_result:
                            self.logger.info(
                                LOG_IDEMPOTENCY_CACHE_HIT,
                                idempotency_key=idempotency_key,
                                **context_data
                            )
                            return ToolResult(**cached_result)
            
            # Execute the actual function with optional limiter, tracing, and timeout
            async def _invoke() -> Any:
                if ctx.tracer:
                    async with ctx.tracer.span(f"{self.spec.tool_name}.execute", {"tool": self.spec.tool_name}):
                        return await self.func(args)
                return await self.func(args)
            
            if ctx.limiter:
                async with ctx.limiter.acquire(self.spec.tool_name):
                    if self.spec.timeout_s:
                        result_content = await asyncio.wait_for(_invoke(), timeout=self.spec.timeout_s)
                    else:
                        result_content = await _invoke()
            else:
                if self.spec.timeout_s:
                    result_content = await asyncio.wait_for(_invoke(), timeout=self.spec.timeout_s)
                else:
                    result_content = await _invoke()
            
            execution_time = time.time() - start_time
            
            # Log successful completion
            self.logger.info(LOG_EXECUTION_COMPLETED,
                result=str(result_content),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)
            
            # Log metrics if available
            if ctx.metrics:
                TAGS = {TOOL: self.spec.tool_name, STATUS: SUCCESS}
                await ctx.metrics.timing_ms(TOOL_EXECUTION_TIME, int(execution_time * 1000), tags=TAGS)
                await ctx.metrics.incr(TOOL_EXECUTIONS, tags=TAGS)
            
            # Calculate usage metrics
            usage = self._calculate_usage(start_time, args, result_content)
            
            # Create result
            result = self._create_result(result_content, usage)
            
            # Cache result if idempotency is enabled and not bypassed
            if (
                self.spec.idempotency.enabled
                and ctx.memory
                and self.spec.idempotency.persist_result
                and not bypass_idempotency
                and getattr(ctx, "idempotency_key", None)
            ):
                await ctx.memory.set(
                    f"{IDEMPOTENCY_CACHE_PREFIX}:{ctx.idempotency_key}",
                    result.model_dump(),
                    ttl_s=self.spec.idempotency.ttl_s
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(LOG_EXECUTION_FAILED,
                error=str(e),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)
            
            # Log error metrics if available
            if ctx.metrics:
                await ctx.metrics.incr(TOOL_EXECUTIONS, tags={TOOL: self.spec.tool_name, STATUS: ERROR})
            
            # Create error result
            usage = self._calculate_usage(start_time, args, None)
            error_result = self._create_result(
                content={ERROR: str(e)},
                usage=usage,
                warnings=[f"{EXECUTION_FAILED}: {str(e)}"]
            )
            return error_result

