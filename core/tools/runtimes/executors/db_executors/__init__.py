"""
Database Executors for Tools Specification System.

This module provides database-specific executors for various database providers,
following a modular architecture with interface, factory, and implementations.

Strategy Pattern Implementation:
=================================
All executors extend BaseDbExecutor, allowing runtime selection of the appropriate
execution strategy for each database type via DbExecutorFactory.

Available Components:
=====================
- DbExecutorFactory: Factory for creating database executors
- BaseDbExecutor: Base implementation with common patterns
- DynamoDBExecutor: AWS DynamoDB operations

Available Executors:
====================
- DynamoDBExecutor: AWS DynamoDB operations
- PostgreSQLExecutor: PostgreSQL operations (future)
- MySQLExecutor: MySQL operations (future)
- SQLiteExecutor: SQLite operations (future)

Architecture:
=============
BaseDbExecutor (Base implementation)
├── DynamoDBExecutor (AWS DynamoDB)
├── PostgreSQLExecutor (PostgreSQL - to be implemented)
├── MySQLExecutor (MySQL - to be implemented)
└── SQLiteExecutor (SQLite - to be implemented)

DbExecutorFactory (Creates executors)

Usage:
    # Using factory (recommended)
    from core.tools.runtimes.executors.db_executors import DbExecutorFactory
    from core.tools.spec.tool_types import DynamoDbToolSpec
    
    spec = DynamoDbToolSpec(
        id="dynamodb-tool-v1",
        tool_name="user_data",
        description="Get user data from DynamoDB",
        driver="dynamodb",
        region="us-west-2",
        table_name="users",
        parameters=[...]
    )
    
    executor = DbExecutorFactory.get_executor(spec)
    result = await executor.execute(args, ctx)
    
    # Or create directly
    from core.tools.runtimes.executors.db_executors import DynamoDBExecutor
    
    executor = DynamoDBExecutor(spec)
    result = await executor.execute(args, ctx)

Extending with Custom Executors:
==================================
To add a new database executor:

1. Implement the executor by inheriting from BaseDbExecutor:

    from core.tools.runtimes.executors.db_executors import BaseDbExecutor
    
    class MongoDBExecutor(BaseDbExecutor):
        def __init__(self, spec: DbToolSpec):
            super().__init__(spec)
            # Your initialization
        
        async def _execute_db_operation(self, args, ctx, timeout):
            # Your database-specific logic
            return {
                'operation': 'find',
                'results': your_data,
                'status': 'success'
            }

2. Register with the factory:

    from core.tools.runtimes.executors.db_executors import DbExecutorFactory
    
    DbExecutorFactory.register('mongodb', MongoDBExecutor)

3. Use it:

    spec = DbToolSpec(driver='mongodb', ...)
    executor = DbExecutorFactory.get_executor(spec)
    result = await executor.execute(args, ctx)

Note:
    Executors are stateless - they maintain failure counts and state
    across multiple executions via the context and metrics systems.
"""

from .db_executor_factory import DbExecutorFactory
from .base_db_executor import BaseDbExecutor
from .dynamodb_executor import DynamoDBExecutor

__all__ = [
    "DbExecutorFactory",
    "BaseDbExecutor",
    "DynamoDBExecutor",
]


