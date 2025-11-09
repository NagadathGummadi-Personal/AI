"""
Database Operation Strategies for Generic DB Tool Execution.

This module provides strategy pattern implementations for different database
backends, making the DbToolExecutor fully generic and extensible. New database
backends can be added by implementing the IDbOperationStrategy interface.

Strategy Pattern Implementation:
=================================
The module follows the Strategy pattern to allow runtime selection of database
operation implementations based on the driver type (e.g., 'dynamodb', 'postgresql').

Available Strategies:
=====================
- DynamoDBStrategy: AWS DynamoDB operations with automatic type conversion
- PostgreSQLStrategy: PostgreSQL async operations using asyncpg
- MySQLStrategy: MySQL async operations using aiomysql
- SQLiteStrategy: SQLite async operations using aiosqlite

Factory:
========
- DbStrategyFactory: Creates appropriate strategy instances based on driver name
  and provides strategy registration for custom implementations

Usage:
    from core.tools.executors.db_strategies import DbStrategyFactory
    
    # Get strategy for a specific database
    strategy = DbStrategyFactory.get_strategy('dynamodb')
    
    # Execute database operation
    result = await strategy.execute_operation(
        args={'operation': 'put_item', 'item': {...}},
        spec=db_tool_spec,
        timeout=30.0
    )
    
    # Register custom strategy
    class CustomDBStrategy(IDbOperationStrategy):
        async def execute_operation(self, args, spec, timeout):
            # Custom implementation
            pass
    
    DbStrategyFactory.register_strategy('customdb', CustomDBStrategy())

Extending:
==========
To add support for a new database backend:

1. Create a new strategy class implementing IDbOperationStrategy
2. Implement the execute_operation method
3. Register the strategy using DbStrategyFactory.register_strategy()

Example:
    class MongoDBStrategy(IDbOperationStrategy):
        async def execute_operation(self, args, spec, timeout):
            # MongoDB implementation
            pass
    
    DbStrategyFactory.register_strategy('mongodb', MongoDBStrategy())

Note:
    Each strategy is responsible for:
    - Establishing database connections
    - Executing operations with proper error handling
    - Converting types as needed for the specific database
    - Returning standardized result dictionaries
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import asyncio
import json


class IDbOperationStrategy(ABC):
    """
    Interface for database operation strategies.
    
    This abstract base class defines the contract that all database operation
    strategies must implement. Each concrete strategy handles operations for
    a specific database backend (e.g., DynamoDB, PostgreSQL, MySQL).
    
    Methods:
        execute_operation: Execute a database operation asynchronously
    
    Implementing Classes:
        DynamoDBStrategy: AWS DynamoDB operations
        PostgreSQLStrategy: PostgreSQL operations
        MySQLStrategy: MySQL operations
        SQLiteStrategy: SQLite operations
    """
    
    @abstractmethod
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,  # DbToolSpec
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute the database operation asynchronously.
        
        Args:
            args: Operation arguments containing:
                - operation: Type of operation (e.g., 'put_item', 'query', 'select')
                - Additional operation-specific parameters
            spec: Database tool specification (DbToolSpec) containing:
                - connection_string or connection parameters
                - database name
                - driver type
            timeout: Optional timeout in seconds for the operation
            
        Returns:
            Dictionary containing operation results with keys:
                - operation: The operation that was executed
                - status: 'success' or error information
                - Additional result-specific data
                
        Raises:
            ImportError: If required database library is not installed
            Exception: Database-specific errors from the underlying driver
        """
        pass


class DynamoDBStrategy(IDbOperationStrategy):
    """
    Strategy for AWS DynamoDB operations.
    
    Handles DynamoDB-specific operations including put_item, get_item, query, and scan.
    Automatically converts Python float types to Decimal for DynamoDB compatibility.
    
    Supported Operations:
        - put_item: Insert or replace an item
        - get_item: Retrieve an item by key
        - query: Query items with conditions
        - scan: Scan table with optional filters
    
    Type Conversion:
        Python floats are automatically converted to Decimal types as required
        by DynamoDB's number type system.
    
    Dependencies:
        Requires boto3 library: pip install boto3
    
    Note:
        AWS credentials should be configured via environment variables,
        AWS config files, or IAM roles when running on AWS infrastructure.
    """
    
    @staticmethod
    def _convert_floats_to_decimal(obj: Any) -> Any:
        """
        Recursively convert floats to Decimal for DynamoDB compatibility.
        
        DynamoDB requires numeric values with decimal points to be Decimal type,
        not Python float. This method recursively converts all floats in nested
        data structures.
        
        Args:
            obj: Object to convert (can be dict, list, float, or other types)
            
        Returns:
            Object with all floats converted to Decimal
        """
        from decimal import Decimal
        
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: DynamoDBStrategy._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBStrategy._convert_floats_to_decimal(item) for item in obj]
        return obj
    
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute DynamoDB operation"""
        try:
            import boto3
            from botocore.config import Config
            
            # Configure boto3 client
            config_dict = {}
            if timeout:
                config_dict['connect_timeout'] = timeout
                config_dict['read_timeout'] = timeout
            
            config = Config(**config_dict) if config_dict else None
            
            def _do_dynamodb_operation():
                # Get configuration from spec (NOT from args!)
                table_name = spec.table_name
                region = getattr(spec, 'region', 'us-west-2')
                endpoint_url = getattr(spec, 'endpoint_url', None)
                
                # Create DynamoDB resource
                if endpoint_url:
                    # Use custom endpoint (for testing with LocalStack)
                    dynamodb = boto3.resource(
                        'dynamodb',
                        region_name=region,
                        endpoint_url=endpoint_url,
                        config=config
                    )
                else:
                    dynamodb = boto3.resource('dynamodb', region_name=region, config=config)
                
                table = dynamodb.Table(table_name)
                
                # Determine operation type
                operation = args.get('operation', 'put_item')
                
                if operation == 'put_item':
                    item = args.get('item', {})
                    # Convert floats to Decimal for DynamoDB compatibility
                    item_converted = DynamoDBStrategy._convert_floats_to_decimal(item)
                    response = table.put_item(Item=item_converted)
                    return {
                        'operation': 'put_item',
                        'table_name': table_name,
                        'item': item,
                        'response': response,
                        'status': 'success'
                    }
                    
                elif operation == 'get_item':
                    key = args.get('key', {})
                    response = table.get_item(Key=key)
                    return {
                        'operation': 'get_item',
                        'table_name': table_name,
                        'key': key,
                        'item': response.get('Item'),
                        'status': 'success'
                    }
                    
                elif operation == 'query':
                    query_params = args.get('query_params', {})
                    response = table.query(**query_params)
                    return {
                        'operation': 'query',
                        'table_name': table_name,
                        'items': response.get('Items', []),
                        'count': response.get('Count', 0),
                        'status': 'success'
                    }
                    
                elif operation == 'scan':
                    scan_params = args.get('scan_params', {})
                    response = table.scan(**scan_params)
                    return {
                        'operation': 'scan',
                        'table_name': table_name,
                        'items': response.get('Items', []),
                        'count': response.get('Count', 0),
                        'status': 'success'
                    }
                    
                else:
                    raise ValueError(f"Unsupported DynamoDB operation: {operation}")
            
            # Run in thread to avoid blocking
            result = await asyncio.to_thread(_do_dynamodb_operation)
            return result
            
        except ImportError:
            raise ImportError("boto3 is required for DynamoDB operations. Install with: pip install boto3")


class PostgreSQLStrategy(IDbOperationStrategy):
    """Strategy for PostgreSQL operations"""
    
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute PostgreSQL operation"""
        try:
            import asyncpg
            
            # Build connection string or use individual params
            conn_string = spec.connection_string
            if not conn_string:
                conn_string = f"postgresql://{spec.username}:{spec.password}@{spec.host}:{spec.port}/{spec.database}"
            
            # Execute query
            query = args.get('query', 'SELECT 1')
            params = args.get('params', [])
            
            async with asyncpg.create_pool(conn_string, timeout=timeout) as pool:
                async with pool.acquire() as conn:
                    if query.strip().upper().startswith('SELECT'):
                        results = await conn.fetch(query, *params)
                        return {
                            'operation': 'select',
                            'query': query,
                            'rows': [dict(r) for r in results],
                            'row_count': len(results),
                            'status': 'success'
                        }
                    else:
                        result = await conn.execute(query, *params)
                        # Parse result like "INSERT 0 5" or "UPDATE 3"
                        parts = result.split()
                        rows_affected = int(parts[-1]) if parts else 0
                        return {
                            'operation': 'execute',
                            'query': query,
                            'rows_affected': rows_affected,
                            'status': 'success'
                        }
                        
        except ImportError:
            raise ImportError("asyncpg is required for PostgreSQL operations. Install with: pip install asyncpg")


class MySQLStrategy(IDbOperationStrategy):
    """Strategy for MySQL operations"""
    
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute MySQL operation"""
        try:
            import aiomysql
            
            # Execute query
            query = args.get('query', 'SELECT 1')
            params = args.get('params', [])
            
            conn = await aiomysql.connect(
                host=spec.host,
                port=spec.port,
                user=spec.username,
                password=spec.password,
                db=spec.database,
                connect_timeout=timeout
            )
            
            try:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    
                    if query.strip().upper().startswith('SELECT'):
                        results = await cursor.fetchall()
                        return {
                            'operation': 'select',
                            'query': query,
                            'rows': results,
                            'row_count': len(results),
                            'status': 'success'
                        }
                    else:
                        await conn.commit()
                        return {
                            'operation': 'execute',
                            'query': query,
                            'rows_affected': cursor.rowcount,
                            'status': 'success'
                        }
            finally:
                conn.close()
                
        except ImportError:
            raise ImportError("aiomysql is required for MySQL operations. Install with: pip install aiomysql")


class SQLiteStrategy(IDbOperationStrategy):
    """Strategy for SQLite operations"""
    
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute SQLite operation"""
        import aiosqlite
        
        # Get database path
        db_path = spec.connection_string or spec.database or ':memory:'
        
        # Execute query
        query = args.get('query', 'SELECT 1')
        params = args.get('params', [])
        
        async with aiosqlite.connect(db_path, timeout=timeout) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                if query.strip().upper().startswith('SELECT'):
                    results = await cursor.fetchall()
                    return {
                        'operation': 'select',
                        'query': query,
                        'rows': [dict(r) for r in results],
                        'row_count': len(results),
                        'status': 'success'
                    }
                else:
                    await db.commit()
                    return {
                        'operation': 'execute',
                        'query': query,
                        'rows_affected': cursor.rowcount,
                        'status': 'success'
                    }


class DbStrategyFactory:
    """
    Factory for creating database operation strategies.
    
    This factory class manages strategy instances and provides methods to
    retrieve strategies by driver name. It supports both built-in strategies
    and custom strategy registration.
    
    Built-in Strategies:
        - dynamodb: AWS DynamoDB operations
        - postgresql/postgres: PostgreSQL operations
        - mysql: MySQL operations
        - sqlite: SQLite operations
    
    Class Methods:
        get_strategy: Retrieve strategy by driver name
        register_strategy: Register a custom strategy
    
    Usage:
        # Get built-in strategy
        strategy = DbStrategyFactory.get_strategy('dynamodb')
        
        # Register custom strategy
        DbStrategyFactory.register_strategy('mongodb', MongoDBStrategy())
    
    Note:
        Strategy instances are shared (singleton pattern) for efficiency.
        Each strategy should be stateless to support concurrent operations.
    """
    
    _strategies: Dict[str, IDbOperationStrategy] = {
        'dynamodb': DynamoDBStrategy(),
        'postgresql': PostgreSQLStrategy(),
        'postgres': PostgreSQLStrategy(),
        'mysql': MySQLStrategy(),
        'sqlite': SQLiteStrategy(),
    }
    
    @classmethod
    def get_strategy(cls, driver: str) -> IDbOperationStrategy:
        """
        Get the appropriate database strategy for the given driver.
        
        Args:
            driver: Database driver name (e.g., 'dynamodb', 'postgresql', etc.)
                   Case-insensitive.
            
        Returns:
            IDbOperationStrategy: Database operation strategy instance
            
        Raises:
            ValueError: If driver is not supported. Error message includes
                       list of supported drivers.
        
        Example:
            strategy = DbStrategyFactory.get_strategy('DynamoDB')
            result = await strategy.execute_operation(args, spec, timeout)
        """
        driver_lower = driver.lower()
        strategy = cls._strategies.get(driver_lower)
        
        if not strategy:
            raise ValueError(
                f"Unsupported database driver: {driver}. "
                f"Supported drivers: {', '.join(cls._strategies.keys())}"
            )
        
        return strategy
    
    @classmethod
    def register_strategy(cls, driver: str, strategy: IDbOperationStrategy):
        """
        Register a custom database strategy.
        
        Allows registration of custom database strategies at runtime. This is
        useful for adding support for additional databases without modifying
        the core codebase.
        
        Args:
            driver: Database driver name (case-insensitive). This will be the
                   identifier used to retrieve the strategy via get_strategy().
            strategy: Strategy implementation instance that implements the
                     IDbOperationStrategy interface.
        
        Example:
            class MongoDBStrategy(IDbOperationStrategy):
                async def execute_operation(self, args, spec, timeout):
                    # MongoDB implementation
                    pass
            
            # Register the custom strategy
            DbStrategyFactory.register_strategy('mongodb', MongoDBStrategy())
            
            # Now it can be used
            strategy = DbStrategyFactory.get_strategy('mongodb')
        
        Note:
            Registering a driver name that already exists will override the
            existing strategy.
        """
        cls._strategies[driver.lower()] = strategy

