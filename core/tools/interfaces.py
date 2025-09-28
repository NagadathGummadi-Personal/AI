"""
Protocol Interfaces for Tools Specification System

This module defines the protocol interfaces that allow for pluggable
components in the tools system. All interfaces are designed to be
narrow and focused on single responsibilities.
"""

from typing import Any, Dict, List, Optional, Callable, Awaitable, AsyncContextManager
from contextlib import asynccontextmanager
from .tool_types import (
    ToolResult,
    ToolSpec,
    ToolContext,
    IToolExecutor,
    IToolValidator,
    IToolSecurity,
    IToolPolicy,
    IToolEmitter,
    IToolMemory,
    IToolMetrics,
    IToolTracer,
    IToolLimiter
)

# Re-export all interfaces for convenience
__all__ = [
    "IToolExecutor",
    "IToolValidator",
    "IToolSecurity",
    "IToolPolicy",
    "IToolEmitter",
    "IToolMemory",
    "IToolMetrics",
    "IToolTracer",
    "IToolLimiter"
]
