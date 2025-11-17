"""
Executors for Tools Specification System.

This module provides executor implementations organized by type, following
a modular architecture with separate folders for each executor category.

Folder Structure:
=================
- executor.py: IExecutor interface (base protocol)
- base_executor.py: BaseToolExecutor base class
- executor_factory.py: ExecutorFactory for creating executors
- noop_executor.py: NoOpExecutor placeholder
- db_executors/: Database-specific executors with interface, factory, and implementations
- function_executors/: Function-based tool executors
- http_executors/: HTTP-based tool executors
- db_strategies/: Database operation strategies (Strategy pattern)

Each executor type follows a consistent pattern:
- Interface (IDbExecutor, IFunctionExecutor, IHttpExecutor)
- Factory (DbExecutorFactory for database executors)
- Base implementation (BaseDbExecutor)
- Concrete implementations (DynamoDBExecutor, PostgreSQLExecutor, etc.)

Available Components:
=====================
Core:
- IExecutor: Base executor protocol
- BaseToolExecutor: Base implementation with common functionality
- ExecutorFactory: Main factory for creating executors
- NoOpExecutor: Placeholder executor

Database Executors:
- IDbExecutor: Interface for database executors
- DbExecutorFactory: Factory for creating database executors
- BaseDbExecutor: Base class for database executors
- DynamoDBExecutor: AWS DynamoDB operations

Function Executors:
- IFunctionExecutor: Interface for function executors
- FunctionToolExecutor: Standard function executor

HTTP Executors:
- IHttpExecutor: Interface for HTTP executors
- HttpToolExecutor: Standard HTTP executor

Usage Examples:
===============

Using ExecutorFactory (Recommended):
    from core.tools.runtimes.executors import ExecutorFactory
    
    # Automatically selects the right executor
    executor = ExecutorFactory.create_executor(spec, func)
    result = await executor.execute(args, ctx)

Database Executors:
    from core.tools.runtimes.executors import DbExecutorFactory
    
    spec = DynamoDbToolSpec(driver="dynamodb", ...)
    executor = DbExecutorFactory.get_executor(spec)
    result = await executor.execute(args, ctx)

Function Executors:
    from core.tools.runtimes.executors import FunctionToolExecutor
    
    executor = FunctionToolExecutor(spec, my_async_function)
    result = await executor.execute(args, ctx)

HTTP Executors:
    from core.tools.runtimes.executors import HttpToolExecutor
    
    executor = HttpToolExecutor(spec)
    result = await executor.execute(args, ctx)

Extending:
==========
Each executor type can be extended by implementing the respective interface
and following the patterns established in the base implementations.

See README.md files in each subfolder for detailed extensibility guides.
"""

# Core components
from .executor import IExecutor
from .base_executor import BaseToolExecutor
from .executor_factory import ExecutorFactory
from .noop_executor import NoOpExecutor

# Re-export commonly used executors for convenience
from .db_executors import (
    IDbExecutor,
    DbExecutorFactory,
    BaseDbExecutor,
    DynamoDBExecutor,
)
from .function_executors import (
    IFunctionExecutor,
    FunctionToolExecutor,
)
from .http_executors import (
    IHttpExecutor,
    HttpToolExecutor,
)

__all__ = [
    # Core
    "IExecutor",
    "BaseToolExecutor",
    "ExecutorFactory",
    "NoOpExecutor",
    # Database executors
    "IDbExecutor",
    "DbExecutorFactory",
    "BaseDbExecutor",
    "DynamoDBExecutor",
    # Function executors
    "IFunctionExecutor",
    "FunctionToolExecutor",
    # HTTP executors
    "IHttpExecutor",
    "HttpToolExecutor",
]

