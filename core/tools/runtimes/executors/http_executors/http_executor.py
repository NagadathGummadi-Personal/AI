"""
HTTP Tool Executor for Tools Specification System.

This module provides the executor for HTTP-based tools that make HTTP requests
with full observability and control.
"""

# Standard library
import json
import time
import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from urllib.request import Request, urlopen

# Local imports
from ..base_executor import BaseToolExecutor
from .base_http_executor import BaseHttpExecutor
from ....spec.tool_types import HttpToolSpec
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult
from ....constants import (
    LOG_HTTP_STARTING,
    LOG_HTTP_COMPLETED,
    LOG_HTTP_FAILED,
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
    UTF_8,
    IDEMPOTENCY_CACHE_PREFIX,
    TOOL_EXECUTION_TIME,
    TOOL_EXECUTIONS,
    STATUS,
    SUCCESS,
    TOOL,
    ERROR,
    HTTP,
)
from ....defaults import DEFAULT_HTTP_CONTEXT_DATA, HTTP_DEFAULT_ERROR_STATUS_WARNING
from utils.logging.LoggerAdaptor import LoggerAdaptor


class HttpToolExecutor(BaseHttpExecutor):
    """
    Executor for HTTP-based tools.
    
    Makes HTTP requests with full lifecycle management including validation,
    authorization, idempotency, metrics, and error handling.
    
    Attributes:
        spec: HTTP tool specification
        logger: Logger instance
    
    Methods:
        execute: Main execution method with full lifecycle management
    """
    
    def __init__(self, spec: HttpToolSpec):
        """
        Initialize HTTP tool executor.
        
        Args:
            spec: HTTP tool specification
        """
        super().__init__(spec)
        self.spec: HttpToolSpec = spec
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

