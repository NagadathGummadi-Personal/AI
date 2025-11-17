"""
HTTP Executor Factory for Tools Specification System.

Provides a centralized factory for creating HTTP executors with
support for custom executor registration.

Classes:
========
- HttpExecutorFactory: Factory for creating HTTP executors

Architecture:
=============
This factory follows the Factory pattern to create HTTP executors
based on tool specifications and user requirements.

Usage:
======
    from core.tools.runtimes.executors.http_executors import HttpExecutorFactory
    from core.tools.spec.tool_types import HttpToolSpec
    
    # Create executor using factory (recommended)
    spec = HttpToolSpec(
        tool_name="github_api",
        base_url="https://api.github.com",
        method="GET",
        endpoint="/repos/{owner}/{repo}",
        ...
    )
    executor = HttpExecutorFactory.create_executor(spec)
    
    # Register custom executor type
    class GraphQLExecutor(BaseHttpExecutor):
        async def _execute_http_request(self, args, ctx, timeout):
            # GraphQL-specific logic
            pass
    
    HttpExecutorFactory.register('graphql', GraphQLExecutor)
    
    # Use custom executor
    executor = HttpExecutorFactory.create_executor(spec, executor_type='graphql')

Extending:
==========
To add custom HTTP executors:

1. Create your executor:
    
    from core.tools.runtimes.executors.http_executors import BaseHttpExecutor
    
    class WebSocketExecutor(BaseHttpExecutor):
        async def _execute_http_request(self, args, ctx, timeout):
            # WebSocket-specific logic
            async with self.session.ws_connect(url) as ws:
                await ws.send_str(message)
                response = await ws.receive_str()
                return {'data': response}

2. Register it:
    
    HttpExecutorFactory.register('websocket', WebSocketExecutor)

3. Use it:
    
    executor = HttpExecutorFactory.create_executor(spec, executor_type='websocket')
"""

from typing import Dict, Type, Optional
from .base_http_executor import BaseHttpExecutor
from .http_executor import HttpToolExecutor
from ....spec.tool_types import ToolSpec


class HttpExecutorFactory:
    """
    Factory for creating HTTP executors.
    
    This factory manages executor creation and supports custom
    executor registration for extensibility.
    """
    
    # Registry of executor types
    _executors: Dict[str, Type[BaseHttpExecutor]] = {
        'standard': HttpToolExecutor,
        'default': HttpToolExecutor,
        'rest': HttpToolExecutor,
    }
    
    @classmethod
    def create_executor(
        cls,
        spec: ToolSpec,
        executor_type: str = 'standard'
    ) -> BaseHttpExecutor:
        """
        Create an HTTP executor based on type.
        
        Args:
            spec: Tool specification
            executor_type: Type of executor ('standard', 'graphql', 'websocket', etc.)
                          Defaults to 'standard'
        
        Returns:
            Configured HTTP executor instance
            
        Raises:
            ValueError: If executor_type is not registered
        
        Example:
            ```python
            spec = HttpToolSpec(
                tool_name="api_call",
                base_url="https://api.example.com",
                method="GET",
                endpoint="/users/{id}"
            )
            executor = HttpExecutorFactory.create_executor(spec)
            result = await executor.execute({'id': '123'}, ctx)
            ```
        """
        executor_type = executor_type.lower()
        
        if executor_type not in cls._executors:
            raise ValueError(
                f"Unknown executor type: '{executor_type}'. "
                f"Available types: {list(cls._executors.keys())}"
            )
        
        executor_class = cls._executors[executor_type]
        return executor_class(spec)
    
    @classmethod
    def register(
        cls,
        executor_type: str,
        executor_class: Type[BaseHttpExecutor]
    ) -> None:
        """
        Register a custom HTTP executor type.
        
        Args:
            executor_type: Name for the executor type (e.g., 'graphql', 'websocket')
            executor_class: Executor class that inherits from BaseHttpExecutor
            
        Raises:
            TypeError: If executor_class doesn't inherit from BaseHttpExecutor
            ValueError: If executor_type is empty
            
        Example:
            ```python
            class GraphQLExecutor(BaseHttpExecutor):
                async def _execute_http_request(self, args, ctx, timeout):
                    query = args.get('query')
                    variables = args.get('variables', {})
                    
                    session = await self._get_session()
                    async with session.post(
                        self.spec.base_url,
                        json={'query': query, 'variables': variables},
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        data = await response.json()
                        return {
                            'status': response.status,
                            'data': data
                        }
            
            HttpExecutorFactory.register('graphql', GraphQLExecutor)
            
            # Now use it
            executor = HttpExecutorFactory.create_executor(
                spec, executor_type='graphql'
            )
            ```
        """
        if not executor_type:
            raise ValueError("Executor type cannot be empty")
        
        if not issubclass(executor_class, BaseHttpExecutor):
            raise TypeError(
                f"Executor class must inherit from BaseHttpExecutor, "
                f"got {executor_class}"
            )
        
        cls._executors[executor_type.lower()] = executor_class
    
    @classmethod
    def unregister(cls, executor_type: str) -> None:
        """
        Unregister an HTTP executor type.
        
        Args:
            executor_type: Name of the executor type to remove
            
        Raises:
            ValueError: If executor_type doesn't exist or is built-in
            
        Note:
            Cannot unregister 'standard', 'default', or 'rest' executor types.
        """
        executor_type = executor_type.lower()
        
        if executor_type in ('standard', 'default', 'rest'):
            raise ValueError(
                f"Cannot unregister built-in executor type: '{executor_type}'"
            )
        
        if executor_type not in cls._executors:
            raise ValueError(
                f"Executor type '{executor_type}' is not registered"
            )
        
        del cls._executors[executor_type]
    
    @classmethod
    def list_executor_types(cls) -> list[str]:
        """
        List all registered executor types.
        
        Returns:
            List of registered executor type names
            
        Example:
            ```python
            types = HttpExecutorFactory.list_executor_types()
            print(types)  # ['standard', 'default', 'rest', 'graphql', 'websocket']
            ```
        """
        return list(cls._executors.keys())
    
    @classmethod
    def get_executor_class(cls, executor_type: str) -> Type[BaseHttpExecutor]:
        """
        Get the executor class for a given type.
        
        Args:
            executor_type: Name of the executor type
            
        Returns:
            Executor class
            
        Raises:
            ValueError: If executor_type is not registered
        """
        executor_type = executor_type.lower()
        
        if executor_type not in cls._executors:
            raise ValueError(
                f"Unknown executor type: '{executor_type}'. "
                f"Available types: {list(cls._executors.keys())}"
            )
        
        return cls._executors[executor_type]

