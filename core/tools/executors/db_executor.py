"""
Database Tool Executor for Tools Specification System.

This module provides the executor for database-based tools that acts as a factory
to delegate to appropriate database-specific executors.
"""

from .base_executor import BaseToolExecutor
from ..interfaces.tool_interfaces import IToolExecutor
from ..spec.tool_types import DbToolSpec


class DbToolExecutor(BaseToolExecutor, IToolExecutor):
    """
    Database tool executor factory.
    
    This executor acts as a factory that delegates to the appropriate
    database-specific executor based on the driver type.
    
    Supported drivers:
        - dynamodb: DynamoDBExecutor
        - postgresql/postgres: PostgreSQLExecutor (future)
        - mysql: MySQLExecutor (future)
        - sqlite: SQLiteExecutor (future)
    
    The specific executor is selected at initialization time based on
    spec.driver value.
    """

    def __init__(self, spec: DbToolSpec):
        """
        Initialize database executor by selecting appropriate driver-specific executor.
        
        Args:
            spec: Database tool specification
            
        Raises:
            ValueError: If driver is not supported
        """
        super().__init__(spec)
        self.spec: DbToolSpec = spec
        
        # Import specific DB executors
        from .db import DynamoDBExecutor
        
        # Map drivers to executor classes
        driver_executors = {
            'dynamodb': DynamoDBExecutor,
            # Future executors
            # 'postgresql': PostgreSQLExecutor,
            # 'postgres': PostgreSQLExecutor,
            # 'mysql': MySQLExecutor,
            # 'sqlite': SQLiteExecutor,
        }
        
        # Get the appropriate executor class
        driver_lower = spec.driver.lower()
        executor_class = driver_executors.get(driver_lower)
        
        if not executor_class:
            raise ValueError(
                f"Unsupported database driver: {spec.driver}. "
                f"Supported drivers: {', '.join(driver_executors.keys())}"
            )
        
        # Create the specific executor instance
        self._executor = executor_class(spec)
    
    async def execute(self, args, ctx):
        """
        Execute the database operation by delegating to the specific executor.
        
        Args:
            args: Database operation arguments
            ctx: Tool execution context
            
        Returns:
            ToolResult containing operation results
        """
        return await self._executor.execute(args, ctx)

