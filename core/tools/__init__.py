"""
Tools Specification System (v1.2.0)

This module provides a modular, asynchronous tool execution system with SOLID separation,
strict validation, security, idempotency, tracing, metrics, and circuit breaker-aware retries.

Core components:
- ToolType: Enumeration for tool types (Function, Http, DB)
- ToolReturnType: Enumeration for return formats (JSON, Text)
- ToolReturnTarget: Enumeration for return routing (Human, LLM, Agent, Step)
- ToolParameter: Schema definition for tool parameters
- ToolSpec: Main tool specification with metadata and configuration
- ToolContext: Execution context with tracing, auth, and dependencies
- ToolResult: Standardized result format with usage metrics
- ToolError: Exception class for tool errors
- Protocol interfaces for pluggable components (validators, security, policies, etc.)
- Base executor classes for common tool types
- Example implementations and usage patterns
"""

from .enum import ToolType, ToolReturnType, ToolReturnTarget

# Core spec models (re-export from subpackage)
from .spec import (
    ToolContext,
    ToolUsage,
    ToolResult,
    ToolError,
    ToolParameter,
    ToolSpec,
    FunctionToolSpec,
    HttpToolSpec,
    DbToolSpec,
    RetryConfig,
    CircuitBreakerConfig,
    IdempotencyConfig,
)

# Interfaces (re-export from subpackage)
from .interfaces import (
    IToolExecutor,
    IToolValidator,
    IToolSecurity,
    IToolPolicy,
    IToolEmitter,
    IToolMemory,
    IToolMetrics,
    IToolTracer,
    IToolLimiter,
)

# Implementations / executors / validators
from .validators import BasicValidator
from .executors import (
    BaseToolExecutor,
    FunctionToolExecutor,
    HttpToolExecutor,
    DbToolExecutor,
)

__all__ = [
    # Types
    "ToolType",
    "ToolReturnType",
    "ToolReturnTarget",
    "ToolUsage",
    "ToolResult",
    "ToolError",
    "ToolParameter",
    "ToolSpec",
    "FunctionToolSpec",
    "HttpToolSpec",
    "DbToolSpec",
    "ToolContext",
    "RetryConfig",
    "CircuitBreakerConfig",
    "IdempotencyConfig",
    # Interfaces
    "IToolExecutor",
    "IToolValidator",
    "IToolSecurity",
    "IToolPolicy",
    "IToolEmitter",
    "IToolMemory",
    "IToolMetrics",
    "IToolTracer",
    "IToolLimiter",
    # Implementations
    "BasicValidator",
    "BaseToolExecutor",
    "FunctionToolExecutor",
    "HttpToolExecutor",
    "DbToolExecutor"
]
