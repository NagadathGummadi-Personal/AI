# Database Operation Strategies

This module implements the Strategy pattern for database operations, allowing runtime selection of database-specific implementations based on the driver type.

## Architecture

The Strategy pattern separates the database-specific implementation logic from the executor logic, making the system highly extensible and maintainable.

```
IDbOperationStrategy (Abstract Interface)
├── DynamoDBStrategy (AWS DynamoDB)
├── PostgreSQLStrategy (PostgreSQL - future)
├── MySQLStrategy (MySQL - future)
└── SQLiteStrategy (SQLite - future)

DbStrategyFactory (Manages strategies)
```

## Available Strategies

### DynamoDBStrategy
- **Database:** AWS DynamoDB
- **Status:** ✅ Implemented
- **Operations:** put_item, get_item, query, scan
- **Dependencies:** `boto3`
- **Features:** Automatic float→Decimal conversion

## Usage

### Using Built-in Strategies

```python
from core.tools.executors.db_strategies import DbStrategyFactory

# Get strategy
strategy = DbStrategyFactory.get_strategy('dynamodb')

# Execute operation
result = await strategy.execute_operation(
    args={
        'operation': 'put_item',
        'item': {'id': '123', 'name': 'John', 'price': 99.99}
    },
    spec=dynamodb_spec,
    timeout=30.0
)

# Result
print(result)
# {
#     'operation': 'put_item',
#     'table_name': 'users',
#     'item': {'id': '123', 'name': 'John', 'price': 99.99},
#     'status': 'success'
# }
```

## Creating Custom Strategies

### Step 1: Implement IDbOperationStrategy

```python
from core.tools.executors.db_strategies import IDbOperationStrategy
from typing import Any, Dict, Optional

class CassandraStrategy(IDbOperationStrategy):
    """
    Strategy for Apache Cassandra operations.
    
    Implements IDbOperationStrategy for Cassandra database operations.
    """
    
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute Cassandra operation."""
        try:
            from cassandra.cluster import Cluster
            from cassandra import ConsistencyLevel
            import asyncio
            
            def _execute_cassandra():
                # Connect to Cassandra cluster
                cluster = Cluster(
                    contact_points=spec.contact_points,
                    port=spec.port
                )
                session = cluster.connect(spec.keyspace)
                
                # Get CQL query from args
                cql = args.get('cql')
                params = args.get('params', ())
                
                # Execute query
                if cql.strip().upper().startswith('SELECT'):
                    result_set = session.execute(cql, params)
                    rows = [dict(row._asdict()) for row in result_set]
                    return {
                        'operation': 'select',
                        'cql': cql,
                        'rows': rows,
                        'row_count': len(rows),
                        'status': 'success'
                    }
                else:
                    session.execute(cql, params)
                    return {
                        'operation': 'execute',
                        'cql': cql,
                        'status': 'success'
                    }
            
            # Run in thread to avoid blocking
            result = await asyncio.to_thread(_execute_cassandra)
            return result
            
        except ImportError as e:
            raise ImportError(
                "cassandra-driver is required for Cassandra operations. "
                "Install with: pip install cassandra-driver"
            ) from e
```

### Step 2: Register the Strategy

```python
from core.tools.executors.db_strategies import DbStrategyFactory
from my_strategies import CassandraStrategy

# Register custom strategy
DbStrategyFactory.register_strategy('cassandra', CassandraStrategy())

# Verify registration
strategy = DbStrategyFactory.get_strategy('cassandra')
print(f"Registered: {strategy}")  # CassandraStrategy instance
```

### Step 3: Use the Strategy

```python
from core.tools.spec.tool_types import DbToolSpec

# Create spec with custom driver
spec = DbToolSpec(
    id="cassandra-tool",
    tool_name="user_query",
    description="Query users from Cassandra",
    driver="cassandra",  # Your custom driver name
    database="users_keyspace",
    parameters=[...]
)

# Get strategy from factory
strategy = DbStrategyFactory.get_strategy('cassandra')

# Execute operation
result = await strategy.execute_operation(
    args={
        'cql': 'SELECT * FROM users WHERE id = ?',
        'params': ('123',)
    },
    spec=spec,
    timeout=30.0
)
```

## Strategy Contract

All strategies must implement the `IDbOperationStrategy` interface:

```python
class IDbOperationStrategy(ABC):
    @abstractmethod
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        pass
```

### Method Parameters

- **args** (Dict[str, Any]): Operation arguments
  - `operation`: Type of operation (e.g., 'put_item', 'query', 'select')
  - Additional operation-specific parameters

- **spec** (DbToolSpec): Database tool specification
  - Configuration like connection strings, database names, regions, etc.
  - Provider-specific settings

- **timeout** (Optional[float]): Optional timeout in seconds

### Return Value

Must return a dictionary with these keys:

- **operation** (str): The operation that was executed
- **status** (str): 'success' or error status
- **Additional keys**: Operation-specific data (rows, items, count, etc.)

```python
return {
    'operation': 'query',
    'status': 'success',
    'rows': results,
    'row_count': len(results),
    'query_time_ms': 125.5
}
```

## Best Practices

### 1. Use Async Execution
Always use `asyncio.to_thread()` for blocking I/O operations:

```python
async def execute_operation(self, args, spec, timeout):
    def _blocking_operation():
        # Blocking database call
        return db.execute(query)
    
    result = await asyncio.to_thread(_blocking_operation)
    return result
```

### 2. Handle Timeouts Properly
Respect the timeout parameter:

```python
async def execute_operation(self, args, spec, timeout):
    # For async libraries
    async with asyncpg.create_pool(..., timeout=timeout) as pool:
        # Execute

    # For sync libraries with asyncio.to_thread
    def _execute():
        # Configure timeout in library-specific way
        conn = connect(..., connect_timeout=timeout)
    
    result = await asyncio.to_thread(_execute)
```

### 3. Type Conversion
Handle database-specific type requirements:

```python
@staticmethod
def _convert_types(obj):
    """Convert Python types to database-specific types."""
    if isinstance(obj, float):
        # DynamoDB example
        from decimal import Decimal
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: _convert_types(v) for k, v in obj.items()}
    return obj
```

### 4. Comprehensive Error Handling
Provide clear error messages:

```python
try:
    # Execute operation
    pass
except ImportError as e:
    raise ImportError(
        "Required library not installed. "
        "Install with: pip install library-name"
    ) from e
except ConnectionError as e:
    raise ConnectionError(
        f"Failed to connect to database: {str(e)}"
    ) from e
except Exception as e:
    raise Exception(
        f"Database operation failed: {str(e)}"
    ) from e
```

### 5. Stateless Design
Strategies should be stateless (no instance variables for connections):

```python
# ✅ Good - Stateless
class MyStrategy(IDbOperationStrategy):
    async def execute_operation(self, args, spec, timeout):
        # Create connection here
        conn = await connect(...)
        # Use connection
        # Close connection
        pass

# ❌ Bad - Stateful
class MyStrategy(IDbOperationStrategy):
    def __init__(self):
        self.connection = None  # Don't store state!
```

## Testing Custom Strategies

```python
import pytest
from my_strategies import CassandraStrategy
from core.tools.spec.tool_types import DbToolSpec

@pytest.mark.asyncio
async def test_cassandra_strategy():
    strategy = CassandraStrategy()
    
    spec = DbToolSpec(
        id="test",
        tool_name="test",
        description="Test",
        driver="cassandra",
        database="test_keyspace"
    )
    
    result = await strategy.execute_operation(
        args={'cql': 'SELECT * FROM users LIMIT 1', 'params': ()},
        spec=spec,
        timeout=30.0
    )
    
    assert result['status'] == 'success'
    assert 'rows' in result
```

## Directory Structure

```
db_strategies/
├── __init__.py                  # Exports
├── README.md                    # This file
├── strategy_interface.py        # IDbOperationStrategy interface
├── dynamodb_strategy.py         # DynamoDB implementation
├── postgresql_strategy.py       # PostgreSQL (future)
├── mysql_strategy.py            # MySQL (future)
├── sqlite_strategy.py           # SQLite (future)
└── strategy_factory.py          # DbStrategyFactory
```

## Examples

### Redis Strategy

```python
class RedisStrategy(IDbOperationStrategy):
    async def execute_operation(self, args, spec, timeout):
        import redis.asyncio as redis
        
        client = redis.Redis(
            host=spec.host,
            port=spec.port,
            db=spec.database,
            socket_timeout=timeout
        )
        
        operation = args.get('operation')
        if operation == 'get':
            value = await client.get(args['key'])
            return {
                'operation': 'get',
                'key': args['key'],
                'value': value.decode() if value else None,
                'status': 'success'
            }
        elif operation == 'set':
            await client.set(args['key'], args['value'])
            return {
                'operation': 'set',
                'key': args['key'],
                'status': 'success'
            }
```

### Elasticsearch Strategy

```python
class ElasticsearchStrategy(IDbOperationStrategy):
    async def execute_operation(self, args, spec, timeout):
        from elasticsearch import AsyncElasticsearch
        
        client = AsyncElasticsearch(
            hosts=[f"{spec.host}:{spec.port}"],
            timeout=timeout
        )
        
        operation = args.get('operation')
        if operation == 'search':
            result = await client.search(
                index=args['index'],
                body=args['query']
            )
            return {
                'operation': 'search',
                'index': args['index'],
                'hits': result['hits']['hits'],
                'total': result['hits']['total']['value'],
                'status': 'success'
            }
```

## Related Documentation

- [Database Executors](../db_executors/README.md) - Executor implementations
- [Tool Specification](../../spec/tool_types.py) - Tool spec definitions
- [Base Executor](../base_executor.py) - Common executor functionality

