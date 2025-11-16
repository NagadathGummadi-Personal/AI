"""
Executors for Tools Specification System.

This module provides executor implementations for different tool types,
following a modular architecture with separate files for each executor type.

Strategy Pattern Implementation:
=================================
All executors implement IExecutor (via IToolExecutor), allowing runtime selection
of the appropriate execution strategy for each tool type.

Available Executors:
====================
- BaseToolExecutor: Base class with common functionality
- FunctionToolExecutor: Executes user-provided async functions
- HttpToolExecutor: Makes HTTP requests
- DbToolExecutor: Executes database operations (factory for DB-specific executors)
- NoOpExecutor: Placeholder executor (for testing/development)

Usage:
    from core.tools.executors import FunctionToolExecutor
    
    # Create executor
    executor = FunctionToolExecutor(spec, my_function)
    
    # Or use factory
    from core.tools.executors import ExecutorFactory
    executor = ExecutorFactory.create_executor(spec, my_function)

Extending:
==========
Create custom executor by inheriting from BaseToolExecutor:

    class CustomExecutor(BaseToolExecutor):
        async def execute(self, args, ctx):
            # Your execution logic
            pass
    
    # Register with factory if needed
    ExecutorFactory.register(ToolType.CUSTOM, CustomExecutor)
"""

from .executor import IExecutor
from .base_executor import BaseToolExecutor
from .function_executor import FunctionToolExecutor
from .http_executor import HttpToolExecutor
from .db_executor import DbToolExecutor
from .noop_executor import NoOpExecutor
from .executor_factory import ExecutorFactory

__all__ = [
    "IExecutor",
    "BaseToolExecutor",
    "FunctionToolExecutor",
    "HttpToolExecutor",
    "DbToolExecutor",
    "NoOpExecutor",
    "ExecutorFactory",
]


