"""
No-Op Executor Implementation.

Placeholder executor for development/testing.
"""

from typing import Any, Dict

from ..spec.tool_types import ToolSpec
from ..spec.tool_context import ToolContext
from ..spec.tool_result import ToolResult


class NoOpExecutor:
    """
    No-op implementation of IExecutor.
    
    This is a placeholder executor that raises NotImplementedError.
    Useful for:
    - Testing tool specifications without implementation
    - Placeholder during development
    - API mocking
    
    Usage:
        executor = NoOpExecutor(spec)
        # Will raise NotImplementedError when executed
    """
    
    def __init__(self, spec: ToolSpec):
        """
        Initialize no-op executor.
        
        Args:
            spec: Tool specification
        """
        self.spec = spec
    
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the tool (no-op implementation that raises error)."""
        raise NotImplementedError(
            f"NoOpExecutor should be replaced with actual implementation for tool: {self.spec.tool_name}"
        )

