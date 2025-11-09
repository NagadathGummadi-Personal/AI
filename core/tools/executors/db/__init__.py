"""
Database Executors for Tools Specification System.

This module provides database tool executors with a proper inheritance hierarchy.
Each database type has its own executor that inherits from BaseDbExecutor.

Executor Hierarchy:
===================
BaseToolExecutor (base_executor.py)
└── BaseDbExecutor (base_db_executor.py)
    ├── DynamoDBExecutor (dynamodb_executor.py)
    ├── PostgreSQLExecutor (postgresql_executor.py)
    ├── MySQLExecutor (mysql_executor.py)
    └── SQLiteExecutor (sqlite_executor.py)

Usage:
    from core.tools.executors.db import DynamoDBExecutor
    
    spec = DbToolSpec(driver='dynamodb', ...)
    executor = DynamoDBExecutor(spec)
    result = await executor.execute(args, ctx)

Extending:
==========
To add a new database executor:

1. Create a new file: my_db_executor.py
2. Inherit from BaseDbExecutor
3. Implement execute() method
4. Export from __init__.py

Example:
    class MongoDBExecutor(BaseDbExecutor):
        async def execute(self, args, ctx):
            # Your MongoDB logic
            pass
"""

from .base_db_executor import BaseDbExecutor
from .dynamodb_executor import DynamoDBExecutor

__all__ = [
    "BaseDbExecutor",
    "DynamoDBExecutor",
]
