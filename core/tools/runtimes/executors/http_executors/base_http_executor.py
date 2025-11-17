"""
Base HTTP Executor for Tools Specification System.

This module provides the base class for all HTTP tool executors. It handles
common HTTP execution patterns including validation, authorization, request
building, response handling, and metrics collection.

Classes:
========
- BaseHttpExecutor: Abstract base class for all HTTP executors

Inheritance Hierarchy:
======================
BaseToolExecutor (from base_executor.py)
└── BaseHttpExecutor (this file)
    ├── HttpToolExecutor (standard REST)
    ├── GraphQLExecutor (future)
    ├── WebSocketExecutor (future)
    └── [Your Custom Executors]

Responsibilities:
=================
- HTTP-specific logging setup
- Common validation/auth flow for HTTP requests
- Request building and execution
- Response parsing and formatting
- Retry logic for transient failures
- Metrics and tracing integration
- Delegates actual HTTP logic to subclasses

Usage:
    class MyHttpExecutor(BaseHttpExecutor):
        async def _execute_http_request(self, args, ctx, timeout):
            # Your specific HTTP logic
            response = await self._make_request(
                method='GET',
                url=f"{self.spec.base_url}/endpoint",
                headers={'Authorization': 'Bearer token'}
            )
            return response

Note:
    Subclasses must implement _execute_http_request() method.
"""

# Standard library
import time
import asyncio
from abc import abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

# Third-party (conditional import)
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    # Create a dummy class for type checking
    if TYPE_CHECKING:
        import aiohttp

# Local imports
from ..base_executor import BaseToolExecutor
from ....spec.tool_types import ToolSpec
from ....spec.tool_context import ToolContext
from ....spec.tool_result import ToolResult


class BaseHttpExecutor(BaseToolExecutor):
    """
    Base executor for HTTP-based tools.
    
    Provides common functionality for making HTTP requests
    with observability, error handling, and metrics collection.
    
    Attributes:
        spec: Tool specification
        session: Shared aiohttp session (optional)
    """
    
    def __init__(self, spec: ToolSpec):
        """
        Initialize the base HTTP executor.
        
        Args:
            spec: Tool specification
            
        Raises:
            ImportError: If aiohttp is not installed
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for HTTP executors. "
                "Install it with: pip install aiohttp"
            )
        
        super().__init__(spec)
        self._session: Optional['aiohttp.ClientSession'] = None
    
    async def _execute_impl(
        self,
        args: Dict[str, Any],
        ctx: ToolContext
    ) -> ToolResult:
        """
        Execute the HTTP-based tool.
        
        This is the main execution flow that:
        1. Logs execution start
        2. Executes the HTTP request with timeout
        3. Handles errors and formats responses
        4. Collects metrics
        
        Args:
            args: Input arguments (already validated)
            ctx: Tool execution context
            
        Returns:
            ToolResult with HTTP response
            
        Raises:
            ToolError: If HTTP request fails
        """
        start_time = time.time()
        
        # Get timeout
        timeout = self.spec.timeout_s or 30
        
        try:
            # Execute the HTTP request (delegates to subclass)
            response = await self._execute_http_request(args, ctx, timeout)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Collect metrics
            if ctx.metrics:
                await ctx.metrics.timing_ms(
                    "http_request_duration",
                    int(duration * 1000),
                    tags={
                        "tool_name": self.spec.tool_name,
                        "status": "success"
                    }
                )
                await ctx.metrics.incr(
                    "http_requests",
                    tags={"tool_name": self.spec.tool_name, "status": "success"}
                )
            
            # Format and return result
            return await self._format_response(response, ctx)
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            
            # Collect timeout metrics
            if ctx.metrics:
                await ctx.metrics.incr(
                    "http_requests",
                    tags={"tool_name": self.spec.tool_name, "status": "timeout"}
                )
            
            from ....spec.tool_types import ToolError
            raise ToolError(
                f"HTTP request timed out after {duration:.2f}s (limit: {timeout}s)",
                retryable=True,
                code="HTTP_TIMEOUT"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Collect error metrics
            if ctx.metrics:
                await ctx.metrics.incr(
                    "http_requests",
                    tags={
                        "tool_name": self.spec.tool_name,
                        "status": "error",
                        "error_type": type(e).__name__
                    }
                )
            
            # Re-raise ToolError as-is, wrap others
            from ....spec.tool_types import ToolError
            if isinstance(e, ToolError):
                raise
            
            # Check if it's an aiohttp error and if it's retryable
            is_retryable = False
            if AIOHTTP_AVAILABLE and e.__class__.__module__.startswith('aiohttp'):
                is_retryable = self._is_retryable_http_error(e)
            
            raise ToolError(
                f"HTTP execution failed: {str(e)}",
                retryable=is_retryable,
                code="HTTP_EXECUTION_ERROR"
            ) from e
    
    @abstractmethod
    async def _execute_http_request(
        self,
        args: Dict[str, Any],
        ctx: ToolContext,
        timeout: float
    ) -> Dict[str, Any]:
        """
        Execute the actual HTTP request.
        
        This method must be implemented by subclasses to define
        how the HTTP request is made.
        
        Args:
            args: Input arguments
            ctx: Tool context
            timeout: Timeout in seconds
            
        Returns:
            HTTP response data (typically dict with status, headers, body)
            
        Raises:
            Exception: Any error from HTTP request
        """
        pass
    
    async def _format_response(
        self,
        response: Dict[str, Any],
        ctx: ToolContext
    ) -> ToolResult:
        """
        Format the HTTP response into a ToolResult.
        
        Args:
            response: Raw HTTP response data
            ctx: Tool context
            
        Returns:
            Formatted ToolResult
        """
        return ToolResult(
            return_type=self.spec.return_type,
            return_target=self.spec.return_target,
            content=response,
            metadata={
                "tool_name": self.spec.tool_name,
                "executor": "BaseHttpExecutor"
            }
        )
    
    def _is_retryable_http_error(self, error: Exception) -> bool:
        """
        Determine if an HTTP error is retryable.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the error should be retried
        """
        if not AIOHTTP_AVAILABLE:
            return False
        
        # Connection errors, timeouts, and 5xx errors are retryable
        retryable_types = (
            asyncio.TimeoutError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorError,
            aiohttp.ServerTimeoutError,
        )
        
        if isinstance(error, retryable_types):
            return True
        
        # Check for 5xx status codes
        if isinstance(error, aiohttp.ClientResponseError):
            return 500 <= error.status < 600
        
        return False
    
    async def _get_session(self) -> 'aiohttp.ClientSession':
        """
        Get or create an aiohttp session.
        
        Returns:
            aiohttp ClientSession
            
        Raises:
            ImportError: If aiohttp is not available
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required but not installed")
        
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the HTTP session if it exists."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

