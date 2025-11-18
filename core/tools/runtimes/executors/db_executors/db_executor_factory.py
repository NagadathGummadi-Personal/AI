"""
Factory for creating database executor instances.

This factory manages the creation of database-specific executors based on
the database driver type specified in the tool spec.
"""

from typing import Dict, Type
from .base_db_executor import BaseDbExecutor
from .dynamodb_executor import DynamoDBExecutor
from ....spec.tool_types import DbToolSpec
from ....constants import (
    UNKNOWN_DB_EXECUTOR_ERROR,
    COMMA,
    SPACE
)


class DbExecutorFactory:
    """
    Factory for creating database executor instances.
    
    Built-in Executors:
        - 'dynamodb': DynamoDBExecutor (AWS DynamoDB)
        - 'postgresql'/'postgres': PostgreSQLExecutor (future)
        - 'mysql': MySQLExecutor (future)
        - 'sqlite': SQLiteExecutor (future)
    
    Usage:
        # Create executor from spec
        spec = DynamoDbToolSpec(...)
        executor = DbExecutorFactory.get_executor(spec)
        
        # Register custom executor
        DbExecutorFactory.register('mongodb', MongoDBExecutor)
        executor = DbExecutorFactory.get_executor(mongodb_spec)
    
    Example:
        from core.tools.runtimes.executors.db_executors import DbExecutorFactory
        from core.tools.spec.tool_types import DynamoDbToolSpec
        
        spec = DynamoDbToolSpec(
            id="users-v1",
            tool_name="get_user",
            description="Get user from DynamoDB",
            driver="dynamodb",
            region="us-west-2",
            table_name="users",
            parameters=[...]
        )
        
        executor = DbExecutorFactory.get_executor(spec)
        result = await executor.execute({'operation': 'get_item', 'key': {'id': '123'}}, ctx)
    """
    
    # Registry mapping driver names to executor classes
    _executors: Dict[str, Type[BaseDbExecutor]] = {
        'dynamodb': DynamoDBExecutor,
        # Future database executors:
        # 'postgresql': PostgreSQLExecutor,
        # 'postgres': PostgreSQLExecutor,  # Alias
        # 'mysql': MySQLExecutor,
        # 'sqlite': SQLiteExecutor,
        # 'mongodb': MongoDBExecutor,
        # 'redis': RedisExecutor,
    }
    
    @classmethod
    def get_executor(cls, spec: DbToolSpec) -> BaseDbExecutor:
        """
        Get the appropriate database executor for the given spec.
        
        Args:
            spec: Database tool specification with driver information
            
        Returns:
            BaseDbExecutor: Database executor instance
            
        Raises:
            ValueError: If driver is not supported. Error message includes
                       list of supported drivers.
        
        Example:
            spec = DynamoDbToolSpec(driver="dynamodb", ...)
            executor = DbExecutorFactory.get_executor(spec)
        """
        driver = getattr(spec, 'driver', None)
        
        if not driver:
            # Try to infer driver from spec type
            spec_type = type(spec).__name__.lower()
            if 'dynamodb' in spec_type:
                driver = 'dynamodb'
            elif 'postgres' in spec_type:
                driver = 'postgresql'
            elif 'mysql' in spec_type:
                driver = 'mysql'
            elif 'sqlite' in spec_type:
                driver = 'sqlite'
            else:
                raise ValueError(
                    f"Could not infer driver from spec type: {type(spec).__name__}. "
                    "Please specify 'driver' attribute in spec."
                )
        
        driver_lower = driver.lower()
        executor_class = cls._executors.get(driver_lower)
        
        if not executor_class:
            raise ValueError(
                UNKNOWN_DB_EXECUTOR_ERROR.format(
                    DRIVER=driver,
                    AVAILABLE_DRIVERS=((COMMA+SPACE).join(sorted(cls._executors.keys())))
                )
            )
        
        return executor_class(spec)
    
    @classmethod
    def register(cls, driver: str, executor_class: Type[BaseDbExecutor]):
        """
        Register a custom database executor.
        
        Args:
            driver: Database driver name (case-insensitive)
            executor_class: Executor class (not instance) that extends BaseDbExecutor
        
        Example:
            from core.tools.runtimes.executors.db_executors import BaseDbExecutor
            
            class MongoDBExecutor(BaseDbExecutor):
                def __init__(self, spec):
                    super().__init__(spec)
                    self.strategy = DbStrategyFactory.get_strategy('mongodb')
                
                async def _execute_db_operation(self, args, ctx, timeout):
                    return await self.strategy.execute_operation(args, self.spec, timeout)
            
            # Register the custom executor
            DbExecutorFactory.register('mongodb', MongoDBExecutor)
            
            # Now it can be used
            spec = DbToolSpec(driver='mongodb', ...)
            executor = DbExecutorFactory.get_executor(spec)
        
        Note:
            Registering a driver name that already exists will override the
            existing executor. This allows replacing built-in executors with
            custom implementations if needed.
        """
        cls._executors[driver.lower()] = executor_class
    
    @classmethod
    def list_drivers(cls) -> list[str]:
        """
        List all registered database drivers.
        
        Returns:
            List of registered driver names
        
        Example:
            drivers = DbExecutorFactory.list_drivers()
            print(f"Available drivers: {', '.join(drivers)}")
        """
        return sorted(cls._executors.keys())

