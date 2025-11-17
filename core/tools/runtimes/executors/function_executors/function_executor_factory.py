"""
Function Executor Factory for Tools Specification System.

Provides a centralized factory for creating function executors with
support for custom executor registration.

Classes:
========
- FunctionExecutorFactory: Factory for creating function executors

Architecture:
=============
This factory follows the Factory pattern to create function executors
based on tool specifications and user requirements.

Usage:
======
    from core.tools.runtimes.executors.function_executors import FunctionExecutorFactory
    from core.tools.spec.tool_types import ToolSpec
    
    # Create executor using factory (recommended)
    spec = ToolSpec(tool_name="my_function", ...)
    executor = FunctionExecutorFactory.create_executor(spec, my_async_function)
    
    # Register custom executor type
    class CachedFunctionExecutor(BaseFunctionExecutor):
        pass
    
    FunctionExecutorFactory.register('cached', CachedFunctionExecutor)
    
    # Use custom executor
    executor = FunctionExecutorFactory.create_executor(
        spec, 
        my_function, 
        executor_type='cached'
    )

Extending:
==========
To add custom function executors:

1. Create your executor:
    
    from core.tools.runtimes.executors.function_executors import BaseFunctionExecutor
    
    class StreamingFunctionExecutor(BaseFunctionExecutor):
        async def _execute_function(self, args, ctx, timeout):
            # Your streaming logic
            async for chunk in self.func(args, ctx):
                yield chunk

2. Register it:
    
    FunctionExecutorFactory.register('streaming', StreamingFunctionExecutor)

3. Use it:
    
    executor = FunctionExecutorFactory.create_executor(
        spec, func, executor_type='streaming'
    )
"""

from typing import Dict, Type, Callable, Any, Awaitable, Optional
from .base_function_executor import BaseFunctionExecutor
from .function_executor import FunctionToolExecutor
from ....spec.tool_types import ToolSpec


class FunctionExecutorFactory:
    """
    Factory for creating function executors.
    
    This factory manages executor creation and supports custom
    executor registration for extensibility.
    """
    
    # Registry of executor types
    _executors: Dict[str, Type[BaseFunctionExecutor]] = {
        'standard': FunctionToolExecutor,
        'default': FunctionToolExecutor,
    }
    
    @classmethod
    def create_executor(
        cls,
        spec: ToolSpec,
        func: Callable[[Dict[str, Any], Any], Awaitable[Any]],
        executor_type: str = 'standard'
    ) -> BaseFunctionExecutor:
        """
        Create a function executor based on type.
        
        Args:
            spec: Tool specification
            func: Async function to execute
            executor_type: Type of executor ('standard', 'cached', etc.)
                          Defaults to 'standard'
        
        Returns:
            Configured function executor instance
            
        Raises:
            ValueError: If executor_type is not registered
            TypeError: If func is not callable
        
        Example:
            ```python
            spec = ToolSpec(tool_name="add", ...)
            executor = FunctionExecutorFactory.create_executor(
                spec, 
                my_add_function
            )
            result = await executor.execute(args, ctx)
            ```
        """
        if not callable(func):
            raise TypeError(f"Function must be callable, got {type(func)}")
        
        executor_type = executor_type.lower()
        
        if executor_type not in cls._executors:
            raise ValueError(
                f"Unknown executor type: '{executor_type}'. "
                f"Available types: {list(cls._executors.keys())}"
            )
        
        executor_class = cls._executors[executor_type]
        return executor_class(spec, func)
    
    @classmethod
    def register(
        cls,
        executor_type: str,
        executor_class: Type[BaseFunctionExecutor]
    ) -> None:
        """
        Register a custom function executor type.
        
        Args:
            executor_type: Name for the executor type (e.g., 'cached', 'streaming')
            executor_class: Executor class that inherits from BaseFunctionExecutor
            
        Raises:
            TypeError: If executor_class doesn't inherit from BaseFunctionExecutor
            ValueError: If executor_type is empty
            
        Example:
            ```python
            class CachedFunctionExecutor(BaseFunctionExecutor):
                def __init__(self, spec, func):
                    super().__init__(spec, func)
                    self.cache = {}
                
                async def _execute_function(self, args, ctx, timeout):
                    cache_key = str(args)
                    if cache_key in self.cache:
                        return self.cache[cache_key]
                    result = await asyncio.wait_for(
                        self.func(args, ctx), 
                        timeout=timeout
                    )
                    self.cache[cache_key] = result
                    return result
            
            FunctionExecutorFactory.register('cached', CachedFunctionExecutor)
            
            # Now use it
            executor = FunctionExecutorFactory.create_executor(
                spec, func, executor_type='cached'
            )
            ```
        """
        if not executor_type:
            raise ValueError("Executor type cannot be empty")
        
        if not issubclass(executor_class, BaseFunctionExecutor):
            raise TypeError(
                f"Executor class must inherit from BaseFunctionExecutor, "
                f"got {executor_class}"
            )
        
        cls._executors[executor_type.lower()] = executor_class
    
    @classmethod
    def unregister(cls, executor_type: str) -> None:
        """
        Unregister a function executor type.
        
        Args:
            executor_type: Name of the executor type to remove
            
        Raises:
            ValueError: If executor_type doesn't exist or is 'standard'/'default'
            
        Note:
            Cannot unregister 'standard' or 'default' executor types.
        """
        executor_type = executor_type.lower()
        
        if executor_type in ('standard', 'default'):
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
            types = FunctionExecutorFactory.list_executor_types()
            print(types)  # ['standard', 'default', 'cached', 'streaming']
            ```
        """
        return list(cls._executors.keys())
    
    @classmethod
    def get_executor_class(cls, executor_type: str) -> Type[BaseFunctionExecutor]:
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

