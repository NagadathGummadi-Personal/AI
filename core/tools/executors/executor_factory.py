"""
Executor Factory for Tools Specification System.

Provides a centralized way to create executors based on tool specifications.
"""

from typing import Union, Dict, Type

from .base_executor import BaseToolExecutor
from .function_executor import FunctionToolExecutor
from .http_executor import HttpToolExecutor
from .db_executor import DbToolExecutor
from .noop_executor import NoOpExecutor
from ..spec.tool_types import ToolSpec, FunctionToolSpec, HttpToolSpec, DbToolSpec
from ..enum import ToolType


class ExecutorFactory:
    """
    Factory for creating executor instances based on tool specifications.
    
    The factory automatically selects the appropriate executor type based on
    the tool specification's type or class.
    
    Usage:
        # Create executor from spec
        spec = FunctionToolSpec(...)
        executor = ExecutorFactory.create_executor(spec, my_function)
        
        # Or use tool type
        executor = ExecutorFactory.get_executor_for_type(ToolType.HTTP)
    """
    
    @classmethod
    def create_executor(
        cls,
        spec: Union[ToolSpec, FunctionToolSpec, HttpToolSpec, DbToolSpec],
        func=None
    ) -> BaseToolExecutor:
        """
        Create an executor based on the tool specification.
        
        Args:
            spec: Tool specification (FunctionToolSpec, HttpToolSpec, or DbToolSpec)
            func: Function to execute (required for FunctionToolSpec)
            
        Returns:
            Appropriate executor instance
            
        Raises:
            ValueError: If tool type is not supported or func is missing for function tools
        """
        # Determine executor type based on spec class or tool_type
        if isinstance(spec, FunctionToolSpec) or spec.tool_type == ToolType.FUNCTION:
            if func is None:
                raise ValueError("Function is required for FunctionToolSpec")
            return FunctionToolExecutor(spec, func)
        elif isinstance(spec, HttpToolSpec) or spec.tool_type == ToolType.HTTP:
            return HttpToolExecutor(spec)
        elif isinstance(spec, DbToolSpec) or spec.tool_type == ToolType.DB:
            return DbToolExecutor(spec)
        else:
            raise ValueError(
                f"Unsupported tool type: {spec.tool_type}. "
                f"Supported types: {ToolType.FUNCTION}, {ToolType.HTTP}, {ToolType.DB}"
            )
    
    # Executor registry for custom executors
    _executor_map: Dict[ToolType, Type[BaseToolExecutor]] = {
        ToolType.FUNCTION: FunctionToolExecutor,
        ToolType.HTTP: HttpToolExecutor,
        ToolType.DB: DbToolExecutor,
    }
    
    @classmethod
    def get_executor_class_for_type(cls, tool_type: ToolType):
        """
        Get the executor class for a given tool type.
        
        Args:
            tool_type: Tool type (FUNCTION, HTTP, or DB)
            
        Returns:
            Executor class
            
        Raises:
            ValueError: If tool type is not supported
        """
        executor_class = cls._executor_map.get(tool_type)
        
        if not executor_class:
            raise ValueError(
                f"Unsupported tool type: {tool_type}. "
                f"Supported types: {', '.join(str(t) for t in cls._executor_map.keys())}"
            )
        
        return executor_class
    
    @classmethod
    def register(cls, tool_type: ToolType, executor_class: Type[BaseToolExecutor]):
        """
        Register a custom executor for a tool type.
        
        Args:
            tool_type: Tool type to register
            executor_class: Executor class to use for this tool type
        
        Example:
            class CustomExecutor(BaseToolExecutor):
                async def execute(self, args, ctx):
                    # Custom logic
                    pass
            
            ExecutorFactory.register(ToolType.CUSTOM, CustomExecutor)
        """
        cls._executor_map[tool_type] = executor_class

