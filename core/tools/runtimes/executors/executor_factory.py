"""
Executor Factory for Tools Specification System.

Provides a centralized way to create executors based on tool specifications.
"""

from typing import Union, Dict, Type

from .base_executor import BaseToolExecutor
from .function_executors import FunctionToolExecutor
from .http_executors import HttpToolExecutor
from .db_executors import DbExecutorFactory
from ...spec.tool_types import ToolSpec, FunctionToolSpec, HttpToolSpec, DbToolSpec
from ...enum import ToolType


class ExecutorFactory:
    """
    Factory for creating executor instances based on tool specifications.
    
    The factory automatically selects the appropriate executor type based on
    the tool specification's type or class.
    
    Architecture:
    =============
    This factory integrates with the modular executor structure:
    - FunctionToolExecutor from function_executors/
    - HttpToolExecutor from http_executors/
    - DbExecutorFactory from db_executors/ (for database executors)
    
    Usage:
        # Create executor from spec
        spec = FunctionToolSpec(...)
        executor = ExecutorFactory.create_executor(spec, my_function)
        
        # Database executor (uses DbExecutorFactory internally)
        spec = DynamoDbToolSpec(driver="dynamodb", ...)
        executor = ExecutorFactory.create_executor(spec)
        
        # HTTP executor
        spec = HttpToolSpec(...)
        executor = ExecutorFactory.create_executor(spec)
        
        # Register custom executor
        ExecutorFactory.register(ToolType.CUSTOM, CustomExecutor)
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
        
        Example:
            # Function executor
            async def my_func(args):
                return {'result': args['x'] + args['y']}
            
            spec = FunctionToolSpec(...)
            executor = ExecutorFactory.create_executor(spec, my_func)
            
            # Database executor (automatically selects DynamoDBExecutor, etc.)
            spec = DynamoDbToolSpec(driver="dynamodb", ...)
            executor = ExecutorFactory.create_executor(spec)
            
            # HTTP executor
            spec = HttpToolSpec(...)
            executor = ExecutorFactory.create_executor(spec)
        """
        # Determine executor type based on spec class or tool_type
        if isinstance(spec, FunctionToolSpec) or spec.tool_type == ToolType.FUNCTION:
            if func is None:
                raise ValueError("Function is required for FunctionToolSpec")
            return FunctionToolExecutor(spec, func)
        
        elif isinstance(spec, HttpToolSpec) or spec.tool_type == ToolType.HTTP:
            return HttpToolExecutor(spec)
        
        elif isinstance(spec, DbToolSpec) or spec.tool_type == ToolType.DB:
            # Use DbExecutorFactory to get the appropriate database executor
            return DbExecutorFactory.get_executor(spec)
        
        else:
            raise ValueError(
                f"Unsupported tool type: {spec.tool_type}. "
                f"Supported types: {ToolType.FUNCTION}, {ToolType.HTTP}, {ToolType.DB}"
            )
    
    # Executor registry for custom executors
    _executor_map: Dict[ToolType, Type[BaseToolExecutor]] = {
        ToolType.FUNCTION: FunctionToolExecutor,
        ToolType.HTTP: HttpToolExecutor,
        # Note: DB executor type uses DbExecutorFactory, not a single class
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
        
        Note:
            For DB tool type, returns None since databases use DbExecutorFactory
            to select the appropriate executor class based on the driver.
        """
        if tool_type == ToolType.DB:
            # DB executors are selected via DbExecutorFactory based on driver
            return None
        
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
            from core.tools.runtimes.executors import BaseToolExecutor, ExecutorFactory
            from core.tools.enum import ToolType
            
            class GraphQLExecutor(BaseToolExecutor):
                async def execute(self, args, ctx):
                    # Custom GraphQL execution logic
                    return ToolResult(content=result, tool_name=self.spec.tool_name)
            
            # Register custom executor
            ExecutorFactory.register(ToolType.GRAPHQL, GraphQLExecutor)
            
            # Now it can be used
            spec = GraphQLToolSpec(tool_type=ToolType.GRAPHQL, ...)
            executor = ExecutorFactory.create_executor(spec)
        
        Note:
            For database executors, use DbExecutorFactory.register() instead:
                from core.tools.runtimes.executors.db_executors import DbExecutorFactory
                DbExecutorFactory.register('mongodb', MongoDBExecutor)
        """
        cls._executor_map[tool_type] = executor_class
    
    @classmethod
    def list_tool_types(cls) -> list[ToolType]:
        """
        List all registered tool types.
        
        Returns:
            List of registered tool types
        
        Example:
            types = ExecutorFactory.list_tool_types()
            print(f"Available types: {types}")
        """
        return list(cls._executor_map.keys())


