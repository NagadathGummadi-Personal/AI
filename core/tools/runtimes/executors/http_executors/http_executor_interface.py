"""
HTTP Executor Interface for Tools Specification System.

This module defines the interface for HTTP-based tool executors that make
HTTP requests with full observability and control.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult


class IHttpExecutor(ABC):
    """
    Interface for HTTP-based tool executors.
    
    HTTP executors handle HTTP requests (GET, POST, PUT, DELETE, etc.) with
    validation, authorization, retries, and metrics collection.
    
    Methods:
        execute: Execute an HTTP request
    
    Implementing Classes:
        HttpToolExecutor: Standard HTTP executor
        CustomHttpExecutor: Custom implementations
    
    Example Implementation:
        class CustomHttpExecutor(IHttpExecutor):
            async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
                # Custom HTTP request logic
                response = await self._make_request(args)
                return ToolResult(content=response, tool_name=self.spec.tool_name)
    """
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        """
        Execute an HTTP request.
        
        Args:
            args: HTTP request arguments including:
                - method: HTTP method (GET, POST, PUT, DELETE, etc.)
                - url: Request URL (optional if spec has base_url)
                - headers: Additional headers
                - body: Request body for POST/PUT
                - query_params: URL query parameters
            ctx: Tool execution context containing:
                - user_id: User identifier
                - session_id: Session identifier
                - trace_id: Trace identifier
                - memory: Memory interface
                - metrics: Metrics interface
                
        Returns:
            ToolResult containing:
                - content: HTTP response data
                - tool_name: Name of the tool
                - error: Error information if request failed
                - usage: Resource usage information
                
        Raises:
            ValidationError: If arguments are invalid
            PermissionError: If authorization fails
            TimeoutError: If request times out
            HTTPError: HTTP-specific errors
        
        Example:
            executor = HttpToolExecutor(spec)
            result = await executor.execute({
                'method': 'GET',
                'url': '/users/123',
                'headers': {'Authorization': 'Bearer token'}
            }, ctx)
            
            if result.error:
                print(f"Error: {result.error}")
            else:
                print(f"Response: {result.content}")
        """
        pass

