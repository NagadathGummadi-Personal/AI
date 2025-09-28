"""
Base Executor Implementations for Tools Specification System

This module provides base classes and utilities for implementing
tool executors with common patterns and boilerplate.
"""

import asyncio
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable, Awaitable
from .tool_types import (
    ToolResult,
    ToolSpec,
    HttpToolSpec,
    DbToolSpec,
    ToolContext,
    ToolUsage,
    ToolReturnType,
    ToolReturnTarget,
    IToolExecutor,
    ToolError
)
from .implementations import NoOpMetrics

# Import LoggerAdaptor for proper logging
try:
    from utils.logging.LoggerAdaptor import LoggerAdaptor
except ImportError:
    # Fallback if logging system is not available
    LoggerAdaptor = None


class BaseToolExecutor:
    """Base class for tool executors with common functionality"""

    def __init__(self, spec: ToolSpec):
        self.spec = spec

    def _generate_idempotency_key(self, args: Dict[str, Any], ctx: ToolContext) -> str:
        """Generate idempotency key from arguments and context"""
        if self.spec.idempotency.key_fields:
            key_data = {k: args.get(k) for k in self.spec.idempotency.key_fields if k in args}
        else:
            key_data = args

        key_components = [
            self.spec.id,
            str(ctx.user_id or ""),
            str(ctx.session_id or ""),
            json.dumps(key_data, sort_keys=True)
        ]

        return hashlib.sha256("|".join(key_components).encode()).hexdigest()

    def _calculate_usage(self, start_time: float, input_args: Dict[str, Any], output_content: Any) -> ToolUsage:
        """Calculate usage statistics for the tool execution"""
        end_time = time.time()

        # Basic calculations - in real implementation, you'd have more sophisticated metrics
        input_bytes = len(json.dumps(input_args).encode('utf-8'))
        output_bytes = len(json.dumps(output_content).encode('utf-8')) if output_content else 0

        return ToolUsage(
            input_bytes=input_bytes,
            output_bytes=output_bytes,
            tokens_in=0,  # Would need tokenizer
            tokens_out=0,  # Would need tokenizer
            cost_usd=0.0,  # Would need pricing model
            attempts=1,
            retries=0,
            cached_hit=False,
            idempotency_reused=False,
            circuit_opened=False
        )

    def _create_result(
        self,
        content: Any,
        usage: Optional[ToolUsage] = None,
        warnings: Optional[List[str]] = None,
        logs: Optional[List[str]] = None,
        artifacts: Optional[Dict[str, bytes]] = None
    ) -> ToolResult:
        """Create a standardized ToolResult"""
        return ToolResult(
            return_type=self.spec.return_type,
            return_target=self.spec.return_target,
            content=content,
            artifacts=artifacts,
            usage=usage,
            warnings=warnings or [],
            logs=logs or []
        )


class FunctionToolExecutor(BaseToolExecutor, IToolExecutor):
    """Executor for function-based tools"""

    def __init__(self, spec: ToolSpec, func: Callable[[Dict[str, Any]], Awaitable[Any]]):
        super().__init__(spec)
        self.func = func
        # Initialize logger for tool execution
        self.logger = LoggerAdaptor.get_logger(f"tool.{spec.tool_name}", environment="dev") if LoggerAdaptor else None

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the function tool"""
        start_time = time.time()

        # Set up logging context
        context_data = {
            "user_id": ctx.user_id,
            "session_id": ctx.session_id,
            "tool_name": self.spec.tool_name,
            "trace_id": ctx.trace_id
        }

        # Log execution start with context
        self.logger.info("Starting tool execution", **context_data)

        # Log parameter details
        self.logger.debug("Tool parameters", parameters=args, **context_data)

        try:
            # Validate parameters if validator is available
            if ctx.validator:
                self.logger.info("Validating parameters", **context_data)
                await ctx.validator.validate(args, self.spec)
                self.logger.info("Parameter validation passed", **context_data)
            else:
                self.logger.warning("No validator available - skipping parameter validation", **context_data)

            # Authorize execution if security is available
            if ctx.security:
                self.logger.info("Checking authorization", **context_data)
                await ctx.security.authorize(ctx, self.spec)
                self.logger.info("Authorization passed", **context_data)
            else:
                self.logger.warning("No security component available - skipping authorization", **context_data)

            # Check egress permissions if security is available
            if ctx.security:
                self.logger.info("Checking egress permissions", **context_data)
                await ctx.security.check_egress(args, self.spec)
                self.logger.info("Egress check passed", **context_data)
            else:
                self.logger.warning("No security component available - skipping egress check", **context_data)
            # Check idempotency if enabled
            if self.spec.idempotency.enabled and ctx.memory:
                idempotency_key = self._generate_idempotency_key(args, ctx)
                ctx.idempotency_key = idempotency_key

                # Try to get cached result
                if self.spec.idempotency.persist_result:
                    cached_result = await ctx.memory.get(f"result:{idempotency_key}")
                    if cached_result:
                        self.logger.info("Using cached result for idempotency", idempotency_key=idempotency_key, **context_data)
                        # Reconstruct ToolResult from cached data
                        return ToolResult(**cached_result)

            # Execute the actual function (without passing context)
            result_content = await self.func(args)

            execution_time = time.time() - start_time

            # Log successful completion
            self.logger.info("Tool execution completed",
                result=str(result_content),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            # Log metrics if available
            if ctx.metrics:
                await ctx.metrics.timing_ms("tool.execution_time", int(execution_time * 1000), tags={"tool": self.spec.tool_name})
                await ctx.metrics.incr("tool.executions", tags={"tool": self.spec.tool_name, "status": "success"})

            # Calculate usage metrics
            usage = self._calculate_usage(start_time, args, result_content)

            # Create result
            result = self._create_result(result_content, usage)

            # Cache result if idempotency is enabled
            if self.spec.idempotency.enabled and ctx.memory and self.spec.idempotency.persist_result:
                await ctx.memory.set(
                    f"result:{ctx.idempotency_key}",
                    result.dict(),
                    ttl_s=self.spec.idempotency.ttl_s
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Tool execution failed",
                error=str(e),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            # Log error metrics if available
            if ctx.metrics:
                await ctx.metrics.incr("tool.executions", tags={"tool": self.spec.tool_name, "status": "error"})

            # Create error result
            usage = self._calculate_usage(start_time, args, None)
            error_result = self._create_result(
                content={"error": str(e)},
                usage=usage,
                warnings=[f"Execution failed: {str(e)}"]
            )
            return error_result


class HttpToolExecutor(BaseToolExecutor, IToolExecutor):
    """Executor for HTTP-based tools"""

    def __init__(self, spec: HttpToolSpec):
        super().__init__(spec)
        self.spec: HttpToolSpec = spec
        # Initialize logger for HTTP tool execution
        self.logger = LoggerAdaptor.get_logger(f"http.{spec.tool_name}", environment="dev") if LoggerAdaptor else None

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the HTTP tool"""
        start_time = time.time()

        # Set up logging context
        context_data = {
            "user_id": ctx.user_id,
            "session_id": ctx.session_id,
            "tool_name": self.spec.tool_name,
            "trace_id": ctx.trace_id,
            "http_method": self.spec.method,
            "http_url": self.spec.url
        }

        # Log execution start
        self.logger.info("Starting HTTP tool execution", **context_data)

        try:
            # In a real implementation, this would make HTTP requests
            # For demo purposes, just return a mock response
            result_content = {
                "status_code": 200,
                "response": f"HTTP {self.spec.method} to {self.spec.url} completed",
                "args": args
            }

            execution_time = time.time() - start_time

            # Log successful completion
            self.logger.info("HTTP tool execution completed",
                status_code=200,
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, result_content)
            result = self._create_result(result_content, usage)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("HTTP tool execution failed",
                error=str(e),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, None)
            error_result = self._create_result(
                content={"error": str(e)},
                usage=usage,
                warnings=[f"HTTP execution failed: {str(e)}"]
            )
            return error_result


class DbToolExecutor(BaseToolExecutor, IToolExecutor):
    """Executor for database-based tools"""

    def __init__(self, spec: DbToolSpec):
        super().__init__(spec)
        self.spec: DbToolSpec = spec
        # Initialize logger for DB tool execution
        self.logger = LoggerAdaptor.get_logger(f"db.{spec.tool_name}", environment="dev") if LoggerAdaptor else None

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the database tool"""
        start_time = time.time()

        # Set up logging context
        context_data = {
            "user_id": ctx.user_id,
            "session_id": ctx.session_id,
            "tool_name": self.spec.tool_name,
            "trace_id": ctx.trace_id,
            "db_host": self.spec.host,
            "db_port": self.spec.port,
            "db_database": self.spec.database
        }

        # Log execution start
        self.logger.info("Starting database tool execution", **context_data)

        try:
            # In a real implementation, this would execute SQL queries
            # For demo purposes, just return a mock response
            result_content = {
                "rows_affected": 1,
                "query": args.get("query", "SELECT 1"),
                "connection": {
                    "host": self.spec.host,
                    "port": self.spec.port,
                    "database": self.spec.database
                }
            }

            execution_time = time.time() - start_time

            # Log successful completion
            self.logger.info("Database tool execution completed",
                rows_affected=1,
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, result_content)
            result = self._create_result(result_content, usage)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error("Database tool execution failed",
                error=str(e),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, None)
            error_result = self._create_result(
                content={"error": str(e)},
                usage=usage,
                warnings=[f"Database execution failed: {str(e)}"]
            )
            return error_result
