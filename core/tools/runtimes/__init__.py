"""
Runtimes for Tools Specification System.

This module provides runtime components for tool execution including executors,
validators, policies, idempotency, and usage calculators.

Folder Structure:
=================
- executors/: Executor implementations organized by type
  - db_executors/: Database-specific executors
  - function_executors/: Function-based executors  
  - http_executors/: HTTP-based executors
  - db_strategies/: Database operation strategies
- policies/: Retry and circuit breaker policies
- idempotency/: Idempotency key generators
- validators/: Parameter validators
- usage_calculators/: Usage tracking and cost calculation

Core Components:
================
- IExecutor: Base executor interface
- BaseToolExecutor: Base implementation with common patterns
- ExecutorFactory: Factory for creating executors
- Various executor implementations (Function, HTTP, DB)

Usage:
    from core.tools.runtimes import FunctionToolExecutor, BaseToolExecutor
    from core.tools.runtimes.executors.db_executors import DynamoDBExecutor
    
    # Function executor
    executor = FunctionToolExecutor(spec, my_function)
    
    # Database executor
    db_executor = DynamoDBExecutor(spec)
    
    # Use factory
    executor = ExecutorFactory.create_executor(spec, my_function)

Extending:
==========
All executors follow SOLID principles and can be extended by inheriting
from base classes or implementing interfaces. See individual subfolder
README files for detailed extensibility guides.
"""

# Re-export from executors module
from .executors import (
    IExecutor,
    BaseToolExecutor,
    ExecutorFactory,
    NoOpExecutor,
    FunctionToolExecutor,
    HttpToolExecutor,
    BaseDbExecutor,
    DynamoDBExecutor,
    DbExecutorFactory,
)

__all__ = [
    # Core
    "IExecutor",
    "BaseToolExecutor",
    "ExecutorFactory",
    "NoOpExecutor",
    # Executors
    "FunctionToolExecutor",
    "HttpToolExecutor",
    # Database executors
    "BaseDbExecutor",
    "DynamoDBExecutor",
    "DbExecutorFactory",
]


