"""
Base Executor Implementations for Tools Specification System

This module provides base classes and utilities for implementing
tool executors with common patterns and boilerplate.
"""

# Standard library
import json
import time
import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from urllib.request import Request, urlopen

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
    UTF_8,
    IDEMPOTENCY_CACHE_PREFIX,
    TOOL_EXECUTION_TIME,
    TOOL_EXECUTIONS,
    STATUS,
    SUCCESS,
    TOOL,
    ERROR,
    EXECUTION_FAILED,
    HTTP,
)
from ..defaults import (
    DEFAULT_TOOL_CONTEXT_DATA,
    DEFAULT_HTTP_CONTEXT_DATA,
    HTTP_DEFAULT_ERROR_STATUS_WARNING,
)
from ..spec.tool_context import ToolContext
from ..spec.tool_result import ToolResult
from ..spec.tool_types import DbToolSpec, HttpToolSpec, ToolSpec
from utils.logging.LoggerAdaptor import LoggerAdaptor
# Import the ONE true BaseToolExecutor
from .base_executor import BaseToolExecutor


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

            # Idempotency handling
            bypass_idempotency = False
            if self.spec.idempotency.enabled and ctx.memory:
                if self.spec.idempotency.key_fields and self.spec.idempotency.bypass_on_missing_key:
                    missing = [k for k in self.spec.idempotency.key_fields if k not in args]
                    if missing:
                        bypass_idempotency = True
                if not bypass_idempotency:
                    idempotency_key = self._generate_idempotency_key(args, ctx)
                    ctx.idempotency_key = idempotency_key
                    if self.spec.idempotency.persist_result:
                        cached_result = await ctx.memory.get(f"{IDEMPOTENCY_CACHE_PREFIX}:{idempotency_key}")
                        if cached_result:
                            self.logger.info(LOG_IDEMPOTENCY_CACHE_HIT, idempotency_key=idempotency_key, **context_data)
                            return ToolResult(**cached_result)

            # Merge HTTP params: prefer args overrides
            base_url = args.get("url", self.spec.url)
            method = (args.get("method") or self.spec.method or "GET").upper()
            headers: Dict[str, str] = {}
            if self.spec.headers:
                headers.update(self.spec.headers)
            if args.get("headers"):
                headers.update(args.get("headers"))

            # Build query string
            combined_qs: Dict[str, str] = {}
            if self.spec.query_params:
                combined_qs.update(self.spec.query_params)
            if args.get("query_params"):
                combined_qs.update(args.get("query_params"))

            parsed = urlparse(base_url)
            existing_qs = dict(parse_qsl(parsed.query))
            existing_qs.update(combined_qs)
            final_query = urlencode(existing_qs, doseq=True)
            final_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, final_query, parsed.fragment))

            # Prepare body
            body = args.get("body", self.spec.body)
            data_bytes: Optional[bytes] = None
            if method != "GET" and body is not None:
                if isinstance(body, (dict, list)):
                    if "Content-Type" not in {k.title(): v for k, v in headers.items()}:
                        headers["Content-Type"] = "application/json"
                    data_bytes = json.dumps(body).encode(UTF_8)
                elif isinstance(body, (str, bytes)):
                    data_bytes = body.encode(UTF_8) if isinstance(body, str) else body
                else:
                    data_bytes = json.dumps(body).encode(UTF_8)

            # Accept header default
            if "Accept" not in {k.title(): v for k, v in headers.items()}:
                headers.setdefault("Accept", "application/json, */*;q=0.8")

            timeout = float(self.spec.timeout_s) if self.spec.timeout_s else None

            def _do_request() -> Dict[str, Any]:
                req = Request(final_url, data=data_bytes, headers=headers, method=method)
                with urlopen(req, timeout=timeout) as resp:
                    status_code = getattr(resp, "status", None) or resp.getcode()
                    raw = resp.read()
                    content_type = resp.headers.get("Content-Type", "")
                    # Try JSON parse
                    parsed_body: Any
                    if "json" in content_type.lower():
                        try:
                            parsed_body = json.loads(raw.decode(UTF_8))
                        except Exception:
                            parsed_body = raw.decode(UTF_8, errors="ignore")
                    else:
                        # attempt json anyway, else fallback to text
                        try:
                            parsed_body = json.loads(raw.decode(UTF_8))
                        except Exception:
                            parsed_body = raw.decode(UTF_8, errors="ignore")
                    return {
                        "status_code": status_code,
                        "response": parsed_body,
                    }

            async def _invoke_http() -> Dict[str, Any]:
                if ctx.tracer:
                    async with ctx.tracer.span(f"{self.spec.tool_name}.http", {"method": method, "url": final_url}):
                        return await asyncio.to_thread(_do_request)
                return await asyncio.to_thread(_do_request)

            if ctx.limiter:
                async with ctx.limiter.acquire(self.spec.tool_name):
                    if timeout:
                        http_result = await asyncio.wait_for(_invoke_http(), timeout=timeout)
                    else:
                        http_result = await _invoke_http()
            else:
                if timeout:
                    http_result = await asyncio.wait_for(_invoke_http(), timeout=timeout)
                else:
                    http_result = await _invoke_http()

            result_content = {
                "status_code": http_result["status_code"],
                "response": http_result["response"],
                "args": args,
            }

            execution_time = time.time() - start_time

            # Log successful completion
            self.logger.info(
                LOG_HTTP_COMPLETED,
                status_code=http_result["status_code"],
                execution_time_ms=round(execution_time * 1000, 2),
                **context_data,
            )

            # Metrics
            if ctx.metrics:
                TAGS = {TOOL: self.spec.tool_name, STATUS: SUCCESS}
                await ctx.metrics.timing_ms(TOOL_EXECUTION_TIME, int(execution_time * 1000), tags=TAGS)
                await ctx.metrics.incr(TOOL_EXECUTIONS, tags=TAGS)

            usage = self._calculate_usage(start_time, args, result_content)
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
                    ttl_s=self.spec.idempotency.ttl_s,
                )

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
    """
    Database tool executor factory.
    
    This executor acts as a factory that delegates to the appropriate
    database-specific executor based on the driver type.
    
    Supported drivers:
        - dynamodb: DynamoDBExecutor
        - postgresql/postgres: PostgreSQLExecutor (future)
        - mysql: MySQLExecutor (future)
        - sqlite: SQLiteExecutor (future)
    
    The specific executor is selected at initialization time based on
    spec.driver value.
    """
    
    def __init__(self, spec: DbToolSpec):
        """
        Initialize database executor by selecting appropriate driver-specific executor.
        
        Args:
            spec: Database tool specification
            
        Raises:
            ValueError: If driver is not supported
        """
        super().__init__(spec)
        self.spec: DbToolSpec = spec
        
        # Import specific DB executors
        from .db import DynamoDBExecutor
        
        # Map drivers to executor classes
        driver_executors = {
            'dynamodb': DynamoDBExecutor,
            # Future executors
            # 'postgresql': PostgreSQLExecutor,
            # 'postgres': PostgreSQLExecutor,
            # 'mysql': MySQLExecutor,
            # 'sqlite': SQLiteExecutor,
        }
        
        # Get the appropriate executor class
        driver_lower = spec.driver.lower()
        executor_class = driver_executors.get(driver_lower)
        
        if not executor_class:
            raise ValueError(
                f"Unsupported database driver: {spec.driver}. "
                f"Supported drivers: {', '.join(driver_executors.keys())}"
            )
        
        # Create the specific executor instance
        self._executor = executor_class(spec)
    
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """
        Execute the database operation using the driver-specific executor.
        
        Args:
            args: Tool execution arguments
            ctx: Tool execution context
            
        Returns:
            ToolResult from the driver-specific executor
        """
        return await self._executor.execute(args, ctx)
