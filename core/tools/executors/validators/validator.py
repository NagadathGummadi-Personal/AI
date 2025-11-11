"""
Validator Interface for Tools Specification System.

This module defines the interface for parameter validation strategies.
"""

from typing import Protocol, Dict, Any, runtime_checkable
from ...spec.tool_types import ToolSpec


@runtime_checkable
class IValidator(Protocol):
    """
    Interface for parameter validation strategies.
    
    All validators must implement this interface to provide parameter validation
    for tool execution.
    
    Methods:
        validate: Validate tool arguments against the specification
        
    Usage:
        class CustomValidator:
            async def validate(self, args: Dict[str, Any], spec: ToolSpec) -> None:
                # Your validation logic
                pass
    """
    
    async def validate(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        """
        Validate tool arguments against the specification.
        
        Args:
            args: Tool arguments to validate
            spec: Tool specification with parameter definitions
            
        Raises:
            ToolError: If validation fails
        """
        ...

