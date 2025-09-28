"""
Basic Implementations for Tools Specification System

This module provides basic, no-op implementations of the various
interfaces that can be used as defaults or for testing purposes.
"""

import time
import asyncio
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
    IToolLimiter,
    ToolError
)


class NoOpExecutor:
    """No-op implementation of IToolExecutor"""

    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the tool (no-op implementation)"""
        raise NotImplementedError("NoOpExecutor should be replaced with actual implementation")


class NoOpValidator:
    """No-op implementation of IToolValidator"""

    async def validate(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        """Validate parameters (no-op implementation)"""
        pass


class NoOpSecurity:
    """No-op implementation of IToolSecurity"""

    async def authorize(self, ctx: ToolContext, spec: ToolSpec) -> None:
        """Authorize execution (no-op implementation)"""
        pass

    async def check_egress(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        """Check egress permissions (no-op implementation)"""
        pass


class BasicSecurity:
    """Basic implementation of IToolSecurity with authorization"""

    def __init__(self, authorized_users: List[str] = None, authorized_roles: List[str] = None):
        self.authorized_users = authorized_users or []
        self.authorized_roles = authorized_roles or []

    async def authorize(self, ctx: ToolContext, spec: ToolSpec) -> None:
        """Authorize execution based on user and permissions"""
        # Check if user is authorized
        if self.authorized_users and ctx.user_id not in self.authorized_users:
            raise ToolError(f"User {ctx.user_id} is not authorized to execute tool {spec.tool_name}",
                          retryable=False, code="UNAUTHORIZED")

        # Check if user has required permissions
        if spec.permissions:
            user_permissions = ctx.auth.get("permissions", [])
            if not all(perm in user_permissions for perm in spec.permissions):
                missing_perms = [perm for perm in spec.permissions if perm not in user_permissions]
                raise ToolError(f"User {ctx.user_id} missing required permissions: {missing_perms}",
                              retryable=False, code="INSUFFICIENT_PERMISSIONS")

        # Check role-based authorization
        if self.authorized_roles:
            user_role = ctx.auth.get("user_role")
            if user_role not in self.authorized_roles:
                raise ToolError(f"User role {user_role} is not authorized to execute tool {spec.tool_name}",
                              retryable=False, code="UNAUTHORIZED_ROLE")

    async def check_egress(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        """Check egress permissions (basic implementation)"""
        # For now, just pass - in a real implementation, this would check
        # if the tool is allowed to access external resources
        pass


class NoOpPolicy:
    """No-op implementation of IToolPolicy"""

    async def with_policy(
        self,
        attempt_coro_factory: Callable[[], Awaitable[ToolResult]],
        *,
        idempotent: bool,
        spec: ToolSpec,
        ctx: ToolContext
    ) -> ToolResult:
        """Execute with policy controls (no-op implementation)"""
        return await attempt_coro_factory()


class NoOpEmitter:
    """No-op implementation of IToolEmitter"""

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit event (no-op implementation)"""
        pass


class NoOpMemory:
    """No-op implementation of IToolMemory"""

    async def get(self, key: str) -> Any:
        """Get value from memory (no-op implementation)"""
        return None

    async def set(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        """Set value in memory (no-op implementation)"""
        pass

    async def set_if_absent(self, key: str, value: Any, ttl_s: Optional[int] = None) -> bool:
        """Set value if absent (no-op implementation)"""
        return False

    async def delete(self, key: str) -> None:
        """Delete value from memory (no-op implementation)"""
        pass

    @asynccontextmanager
    async def lock(self, key: str, ttl_s: int = 10) -> AsyncContextManager[None]:
        """Acquire lock (no-op implementation)"""
        yield


class NoOpMetrics:
    """No-op implementation of IToolMetrics"""

    async def incr(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment metric (no-op implementation)"""
        pass

    async def observe(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Observe metric value (no-op implementation)"""
        pass

    async def timing_ms(self, name: str, value_ms: int, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing metric (no-op implementation)"""
        pass


class NoOpTracer:
    """No-op implementation of IToolTracer"""

    @asynccontextmanager
    async def span(self, name: str, attrs: Optional[Dict[str, Any]] = None) -> AsyncContextManager[str]:
        """Create tracing span (no-op implementation)"""
        yield ""


class NoOpLimiter:
    """No-op implementation of IToolLimiter"""

    @asynccontextmanager
    async def acquire(self, key: str, limit: Optional[int] = None) -> AsyncContextManager[None]:
        """Acquire rate limit (no-op implementation)"""
        yield
