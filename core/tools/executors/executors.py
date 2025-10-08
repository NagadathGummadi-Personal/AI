"""
Base Executor Implementations for Tools Specification System

This module provides base classes and utilities for implementing
tool executors with common patterns and boilerplate.
"""

# Standard library
import hashlib
import json
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

# Local imports
from ..interfaces.tool_interfaces import IToolExecutor
from ..constants import (
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
    LOG_HTTP_STARTING,
    LOG_HTTP_COMPLETED,
    LOG_HTTP_FAILED,
    LOG_DB_STARTING,
    LOG_DB_COMPLETED,
    LOG_DB_FAILED,
    # HTTP_EXECUTION_STATUS_COMPLETED,
    # HTTP_EXECUTION_STATUS_FAILED,
    # DB_EXECUTION_STATUS_FAILED,
    # TOOL_EXECUTION_STATUS_FAILED,
    # TOOL_EXECUTION_STATUS_COMPLETED,
    # DB_EXECUTION_STATUS_COMPLETED,

    UTF_8,
    EXC_HTTP_EXECUTION_NOT_IMPLEMENTED,
    IDEMPOTENCY_CACHE_PREFIX,
    EXC_DB_EXECUTION_NOT_IMPLEMENTED,
    TOOL_EXECUTION_TIME,
    TOOL_EXECUTIONS,
    STATUS,
    SUCCESS,
    TOOL,
    ERROR,
    EXECUTION_FAILED,
    HTTP,
    DB,
    EMPTY_STRING,
)
from ..defaults import (
    DEFAULT_TOOL_CONTEXT_DATA,
    DEFAULT_HTTP_CONTEXT_DATA,
    DEFAULT_DB_CONTEXT_DATA,
    HTTP_DEFAULT_SUCCESS_STATUS_RESPONSE,
    HTTP_DEFAULT_ERROR_STATUS_WARNING,
    DB_DEFAULT_SUCCESS_RESULT_CONTENT,
    DB_DEFAULT_ERROR_STATUS_WARNING,
    calculate_tokens_in,
    calculate_tokens_out,
    calculate_cost_usd,
    calculate_attempts,
    calculate_retries,
    check_cached_hit,
    check_idempotency_reused,
    check_circuit_opened,
)
from ..spec.tool_context import ToolContext, ToolUsage
from ..spec.tool_result import ToolResult
from ..spec.tool_types import DbToolSpec, HttpToolSpec, ToolSpec
#LoggerAdaptor
from utils.logging.LoggerAdaptor import LoggerAdaptor
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
            str(ctx.user_id or EMPTY_STRING),
            str(ctx.session_id or EMPTY_STRING),
            json.dumps(key_data, sort_keys=True)
        ]

        return hashlib.sha256("|".join(key_components).encode()).hexdigest()

    def _calculate_usage(self, start_time: float, input_args: Dict[str, Any], output_content: Any) -> ToolUsage:
        """Calculate usage statistics for the tool execution"""
        # end_time retained for potential future use; presently not needed
        # Basic calculations - in real implementation, you'd have more sophisticated metrics
        input_bytes = len(json.dumps(input_args).encode(UTF_8))
        output_bytes = len(json.dumps(output_content).encode(UTF_8)) if output_content else 0

        return ToolUsage(
            input_bytes=input_bytes,
            output_bytes=output_bytes,
            tokens_in=calculate_tokens_in(),
            tokens_out=calculate_tokens_out(),
            cost_usd=calculate_cost_usd(),
            attempts=calculate_attempts(),
            retries=calculate_retries(),
            cached_hit=check_cached_hit(),
            idempotency_reused=check_idempotency_reused(),
            circuit_opened=check_circuit_opened(),
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
        self.logger = LoggerAdaptor.get_logger(f"{TOOL}.{spec.tool_name}")

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the function tool"""
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
            if self.spec.idempotency.enabled and ctx.memory:
                idempotency_key = self._generate_idempotency_key(args, ctx)
                ctx.idempotency_key = idempotency_key

                # Try to get cached result
                if self.spec.idempotency.persist_result:
                    cached_result = await ctx.memory.get(f"{IDEMPOTENCY_CACHE_PREFIX}:{idempotency_key}")
                    if cached_result:
                        self.logger.info(LOG_IDEMPOTENCY_CACHE_HIT, idempotency_key=idempotency_key, **context_data)
                        # Reconstruct ToolResult from cached data
                        return ToolResult(**cached_result)

            # Execute the actual function (without passing context)
            result_content = await self.func(args)

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

            # Cache result if idempotency is enabled
            if self.spec.idempotency.enabled and ctx.memory and self.spec.idempotency.persist_result:
                await ctx.memory.set(
                    f"{IDEMPOTENCY_CACHE_PREFIX}:{ctx.idempotency_key}",
                    result.dict(),
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


class HttpToolExecutor(BaseToolExecutor, IToolExecutor):
    """Executor for HTTP-based tools"""

    def __init__(self, spec: HttpToolSpec):
        super().__init__(spec)
        self.spec: HttpToolSpec = spec
        # Initialize logger for HTTP tool execution
        self.logger = LoggerAdaptor.get_logger(f"{HTTP}.{spec.tool_name}") if LoggerAdaptor else None

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the HTTP tool"""
        start_time = time.time()

        # Set up logging context
        context_data = DEFAULT_HTTP_CONTEXT_DATA(self.spec, ctx)

        # Log execution start
        self.logger.info(LOG_HTTP_STARTING, **context_data)

        try:
            # In a real implementation, this would make HTTP requests
            # Dev-only mock; raise if not dev
            from ..config import is_dev
            if not is_dev():
                raise NotImplementedError(EXC_HTTP_EXECUTION_NOT_IMPLEMENTED)
            result_content = HTTP_DEFAULT_SUCCESS_STATUS_RESPONSE(self.spec, args)

            execution_time = time.time() - start_time

            # Log successful completion
            self.logger.info(LOG_HTTP_COMPLETED,
                status_code=200,
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, result_content)
            result = self._create_result(result_content, usage)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(LOG_HTTP_FAILED,
                error=str(e),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, None)
            error_result = self._create_result(
                content={ERROR: str(e)},
                usage=usage,
                warnings=[HTTP_DEFAULT_ERROR_STATUS_WARNING(self.spec, str(e))]
            )
            return error_result


class DbToolExecutor(BaseToolExecutor, IToolExecutor):
    """Executor for database-based tools"""

    def __init__(self, spec: DbToolSpec):
        super().__init__(spec)
        self.spec: DbToolSpec = spec
        # Initialize logger for DB tool execution
        self.logger = LoggerAdaptor.get_logger(f"{DB}.{spec.tool_name}") if LoggerAdaptor else None

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the database tool"""
        start_time = time.time()

        # Set up logging context
        context_data = DEFAULT_DB_CONTEXT_DATA(self.spec, ctx)

        # Log execution start
        self.logger.info(LOG_DB_STARTING, **context_data)

        try:
            # In a real implementation, this would execute SQL queries
            from ..config import is_dev
            if not is_dev():
                raise NotImplementedError(EXC_DB_EXECUTION_NOT_IMPLEMENTED)
            result_content = DB_DEFAULT_SUCCESS_RESULT_CONTENT(self.spec, args)

            execution_time = time.time() - start_time

            # Log successful completion
            self.logger.info(LOG_DB_COMPLETED,
                rows_affected=1,
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, result_content)
            result = self._create_result(result_content, usage)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(LOG_DB_FAILED,
                error=str(e),
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data)

            usage = self._calculate_usage(start_time, args, None)
            error_result = self._create_result(
                content={ERROR: str(e)},
                usage=usage,
                warnings=[DB_DEFAULT_ERROR_STATUS_WARNING(self.spec, str(e))]
            )
            return error_result
