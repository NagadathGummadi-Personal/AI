"""
Core Data Types for Tools Specification System (v1.2.0)

This module defines the core data types, enumerations, and model classes
that form the foundation of the tools specification system.
"""

from __future__ import annotations
import asyncio
import time
import json
import re
import uuid
import hashlib
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable, Callable, Awaitable, AsyncContextManager, Union
from typing_extensions import TypedDict
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator


# 1) Enumerations
class ToolReturnType(str, Enum):
    """Enumeration for tool return formats"""
    JSON = "json"
    TEXT = "text"


class ToolReturnTarget(str, Enum):
    """Enumeration for tool return routing targets"""
    HUMAN = "human"
    LLM = "llm"
    AGENT = "agent"
    STEP = "step"


class ToolType(str, Enum):
    """Enumeration for tool types"""
    FUNCTION = "function"
    HTTP = "http"
    DB = "db"


class ParameterType(str, Enum):
    """Enumeration for parameter types"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


# 2) Result, Error, and Metrics Types
class ToolUsage(TypedDict, total=False):
    """Usage statistics for tool execution"""
    input_bytes: int
    output_bytes: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    attempts: int
    retries: int
    cached_hit: bool
    idempotency_reused: bool
    circuit_opened: bool


class ToolResult(BaseModel):
    """Standardized result format for tool execution"""
    return_type: ToolReturnType
    return_target: ToolReturnTarget
    content: Any
    artifacts: Optional[Dict[str, bytes]] = None
    usage: Optional[ToolUsage] = None
    latency_ms: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)


class ToolError(Exception):
    """Exception class for tool errors with retry information"""
    def __init__(self, message: str, retryable: bool = False, code: str = "TOOL_ERROR"):
        super().__init__(message)
        self.retryable = retryable
        self.code = code


# 3) Parameter Schema and Tool Spec
class ToolParameter(BaseModel):
    """Base class for tool parameters with common fields"""
    name: str
    description: str
    required: bool = False
    default: Any | None = None
    deprecated: bool = False
    examples: List[Any] = Field(default_factory=list)


class StringParameter(ToolParameter):
    """Parameter for string values with string-specific constraints"""
    param_type: ParameterType = Field(default=ParameterType.STRING)
    enum: List[str] | None = None
    format: Optional[str] = None  # e.g., "email", "uri", "date-time"
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # regex for string
    coerce: bool = False  # optional coercion (string->number, etc.)


class NumericParameter(ToolParameter):
    """Parameter for numeric values (number/integer) with numeric constraints"""
    param_type: ParameterType = Field(default=ParameterType.NUMBER)
    min: Optional[float] = None
    max: Optional[float] = None


class IntegerParameter(NumericParameter):
    """Parameter for integer values"""
    param_type: ParameterType = Field(default=ParameterType.INTEGER)


class BooleanParameter(ToolParameter):
    """Parameter for boolean values"""
    param_type: ParameterType = Field(default=ParameterType.BOOLEAN)


class ArrayParameter(ToolParameter):
    """Parameter for array values with array-specific constraints"""
    param_type: ParameterType = Field(default=ParameterType.ARRAY)
    items: Optional[ToolParameter] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    unique_items: bool = False


class ObjectParameter(ToolParameter):
    """Parameter for object values with object-specific constraints"""
    param_type: ParameterType = Field(default=ParameterType.OBJECT)
    properties: Optional[Dict[str, ToolParameter]] = None
    oneOf: Optional[List[ToolParameter]] = None


class RetryConfig(BaseModel):
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay_s: float = 0.2
    max_delay_s: float = 2.0
    jitter_s: float = 0.1


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern"""
    enabled: bool = True
    failure_threshold: int = 5  # consecutive failures to open
    recovery_timeout_s: int = 30  # OPEN -> HALF_OPEN after timeout
    half_open_max_calls: int = 1  # allowed test calls in HALF_OPEN
    error_codes_to_trip: List[str] = Field(default_factory=lambda: ["TIMEOUT", "UNAVAILABLE", "TOOL_ERROR"])


class IdempotencyConfig(BaseModel):
    """Configuration for idempotency behavior"""
    enabled: bool = True
    key_fields: Optional[List[str]] = None  # if None, use all args
    ttl_s: Optional[int] = 3600
    persist_result: bool = True  # store result for reuse
    bypass_on_missing_key: bool = False  # if key_fields missing, bypass idempotency


class ToolSpec(BaseModel):
    """Base class for tool specifications with common metadata"""
    id: str
    version: str = "1.0.0"
    tool_name: str
    description: str
    tool_type: ToolType
    parameters: List[ToolParameter]
    return_type: ToolReturnType = Field(default=ToolReturnType.JSON, alias="returns")
    return_target: ToolReturnTarget = ToolReturnTarget.STEP
    required: bool = False
    owner: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    timeout_s: int = 30
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    # Advanced config
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    idempotency: IdempotencyConfig = Field(default_factory=IdempotencyConfig)
    metrics_tags: Dict[str, str] = Field(default_factory=dict)  # static tags for metrics

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True
    }


class FunctionToolSpec(ToolSpec):
    """Tool specification for function-based tools"""
    tool_type: ToolType = Field(default=ToolType.FUNCTION)


class HttpToolSpec(ToolSpec):
    """Tool specification for HTTP-based tools"""
    tool_type: ToolType = Field(default=ToolType.HTTP)

    # HTTP-specific fields
    url: str
    method: str = "POST"  # GET, POST, PUT, DELETE, etc.
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None  # Only for non-GET requests


class DbToolSpec(ToolSpec):
    """Tool specification for database-based tools"""
    tool_type: ToolType = Field(default=ToolType.DB)

    # Database-specific fields
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    driver: str = "postgresql"  # postgresql, mysql, sqlite, etc.


# 4) Context, Tracing, Metrics, Memory, Limiting
class ToolContext(BaseModel):
    """Execution context with tracing, auth, and dependencies"""

    model_config = {"arbitrary_types_allowed": True}
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Tracing
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None

    # Execution control
    locale: Optional[str] = None
    timezone: Optional[str] = None
    deadline_ts: Optional[float] = None

    # Auth and arbitrary extensions
    auth: Dict[str, Any] = Field(default_factory=dict)
    extras: Dict[str, Any] = Field(default_factory=dict)

    # Idempotency / run metadata
    run_id: Optional[str] = None
    idempotency_key: Optional[str] = None

    # Injected dependencies (optional but recommended)
    memory: Optional[IToolMemory] = None
    metrics: Optional[IToolMetrics] = None
    tracer: Optional[IToolTracer] = None
    limiter: Optional[IToolLimiter] = None
    validator: Optional[IToolValidator] = None
    security: Optional[IToolSecurity] = None


# 5) Protocol Interfaces
@runtime_checkable
class IToolExecutor(Protocol):
    """Interface for tool execution"""
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        ...


@runtime_checkable
class IToolValidator(Protocol):
    """Interface for parameter validation"""
    async def validate(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        ...


@runtime_checkable
class IToolSecurity(Protocol):
    """Interface for security checks"""
    async def authorize(self, ctx: ToolContext, spec: ToolSpec) -> None:
        ...

    async def check_egress(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        ...


@runtime_checkable
class IToolPolicy(Protocol):
    """Interface for execution policies (retries, circuit breaker, etc.)"""
    async def with_policy(
        self,
        attempt_coro_factory: Callable[[], Awaitable[ToolResult]],
        *,
        idempotent: bool,
        spec: ToolSpec,
        ctx: ToolContext
    ) -> ToolResult:
        ...


@runtime_checkable
class IToolEmitter(Protocol):
    """Interface for event emission"""
    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        ...


@runtime_checkable
class IToolMemory(Protocol):
    """Interface for memory/caching operations"""
    async def get(self, key: str) -> Any:
        ...

    async def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        ...

    async def set_if_absent(self, key: str, value: Any, ttl_s: Optional[int] = None) -> bool:
        ...

    async def delete(self, key: str) -> None:
        ...

    @asynccontextmanager
    async def lock(self, key: str, ttl_s: int = 10) -> AsyncContextManager[None]:
        yield


@runtime_checkable
class IToolMetrics(Protocol):
    """Interface for metrics collection"""
    async def incr(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        ...

    async def observe(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        ...

    async def timing_ms(self, name: str, value_ms: int, tags: Optional[Dict[str, str]] = None) -> None:
        ...


@runtime_checkable
class IToolTracer(Protocol):
    """Interface for distributed tracing"""
    @asynccontextmanager
    async def span(self, name: str, attrs: Optional[Dict[str, Any]] = None) -> AsyncContextManager[str]:
        # yields span_id
        yield ""


@runtime_checkable
class IToolLimiter(Protocol):
    """Interface for rate limiting"""
    @asynccontextmanager
    async def acquire(self, key: str, limit: Optional[int] = None) -> AsyncContextManager[None]:
        yield
