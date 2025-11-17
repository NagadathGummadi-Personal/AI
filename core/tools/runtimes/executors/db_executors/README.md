# Database Executors

This module provides database-specific executors for various database providers. Each executor implements the database-specific logic while inheriting common patterns from `BaseDbExecutor`.

## Architecture

```
BaseToolExecutor (from base_executor.py)
└── BaseDbExecutor (base class for all DB executors)
    ├── DynamoDBExecutor (AWS DynamoDB)
    ├── PostgreSQLExecutor (PostgreSQL - to be implemented)
    ├── MySQLExecutor (MySQL - to be implemented)
    └── SQLiteExecutor (SQLite - to be implemented)
```

## Available Executors

### DynamoDBExecutor
- **Provider:** AWS DynamoDB
- **Status:** ✅ Implemented
- **Operations:** put_item, get_item, query, scan
- **Dependencies:** `boto3`

### PostgreSQLExecutor
- **Provider:** PostgreSQL
- **Status:** 🔨 To be implemented
- **Operations:** SELECT, INSERT, UPDATE, DELETE
- **Dependencies:** `asyncpg`

### MySQLExecutor
- **Provider:** MySQL
- **Status:** 🔨 To be implemented
- **Operations:** SELECT, INSERT, UPDATE, DELETE
- **Dependencies:** `aiomysql`

### SQLiteExecutor
- **Provider:** SQLite
- **Status:** 🔨 To be implemented
- **Operations:** SELECT, INSERT, UPDATE, DELETE
- **Dependencies:** `aiosqlite`

## Usage

### Using Built-in Executors

```python
from core.tools.executors.db_executors import DynamoDBExecutor
from core.tools.spec.tool_types import DynamoDbToolSpec
from core.tools.spec.tool_context import ToolContext

# Create spec
spec = DynamoDbToolSpec(
    id="user-data-v1",
    tool_name="get_user",
    description="Get user from DynamoDB",
    region="us-west-2",
    table_name="users",
    parameters=[...]
)

# Create executor
executor = DynamoDBExecutor(spec)

# Execute operation
ctx = ToolContext(user_id="user123", memory=memory)
result = await executor.execute({
    'operation': 'get_item',
    'key': {'id': 'user123'}
}, ctx)
```

## Creating Custom Database Executors

To add support for a new database provider, follow these steps:

### Step 1: Implement the Strategy

First, create a strategy for your database operations:

```python
from core.tools.executors.db_strategies import IDbOperationStrategy
from typing import Any, Dict, Optional

class MongoDBStrategy(IDbOperationStrategy):
    """Strategy for MongoDB operations."""
    
    async def execute_operation(
        self,
        args: Dict[str, Any],
        spec: Any,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute MongoDB operation."""
        import motor.motor_asyncio
        
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(
            spec.connection_string,
            serverSelectionTimeoutMS=timeout * 1000 if timeout else None
        )
        db = client[spec.database]
        
        # Execute operation
        operation = args.get('operation')
        
        if operation == 'find':
            collection = db[args['collection']]
            query = args.get('query', {})
            results = await collection.find(query).to_list(length=args.get('limit', 100))
            return {
                'operation': 'find',
                'collection': args['collection'],
                'results': results,
                'count': len(results),
                'status': 'success'
            }
        
        elif operation == 'insert_one':
            collection = db[args['collection']]
            result = await collection.insert_one(args['document'])
            return {
                'operation': 'insert_one',
                'collection': args['collection'],
                'inserted_id': str(result.inserted_id),
                'status': 'success'
            }
        
        else:
            raise ValueError(f"Unsupported MongoDB operation: {operation}")
```

### Step 2: Register the Strategy

```python
from core.tools.executors.db_strategies import DbStrategyFactory

# Register your custom strategy
DbStrategyFactory.register_strategy('mongodb', MongoDBStrategy())
```

### Step 3: Create the Executor

```python
from core.tools.executors.db_executors import BaseDbExecutor
from core.tools.spec.tool_types import DbToolSpec
from core.tools.spec.tool_context import ToolContext
from core.tools.executors.db_strategies import DbStrategyFactory
from typing import Any, Dict

class MongoDBExecutor(BaseDbExecutor):
    """
    MongoDB-specific executor.
    
    Handles MongoDB operations using the MongoDB strategy pattern.
    """
    
    def __init__(self, spec: DbToolSpec):
        """Initialize MongoDB executor."""
        super().__init__(spec)
        # Get the MongoDB strategy
        self.strategy = DbStrategyFactory.get_strategy('mongodb')
    
    async def _execute_db_operation(
        self,
        args: Dict[str, Any],
        ctx: ToolContext,
        timeout: float | None
    ) -> Dict[str, Any]:
        """Execute MongoDB operation using the strategy pattern."""
        return await self.strategy.execute_operation(args, self.spec, timeout)
```

### Step 4: Use Your Custom Executor

```python
from my_executors import MongoDBExecutor
from core.tools.spec.tool_types import DbToolSpec

# Create spec
spec = DbToolSpec(
    id="mongodb-tool-v1",
    tool_name="user_query",
    description="Query users from MongoDB",
    driver="mongodb",
    database="myapp",
    parameters=[...]
)

# Create executor
executor = MongoDBExecutor(spec)

# Execute
result = await executor.execute({
    'operation': 'find',
    'collection': 'users',
    'query': {'age': {'$gt': 18}}
}, ctx)
```

## Best Practices

### 1. Stateless Strategies
Strategies should be stateless to support concurrent operations. Don't store connection objects or state in the strategy instance.

### 2. Proper Error Handling
Always handle database-specific errors and convert them to meaningful messages:

```python
async def execute_operation(self, args, spec, timeout):
    try:
        # Your database operations
        pass
    except ImportError as e:
        raise ImportError(
            f"Required library not found. Install with: pip install {library_name}"
        ) from e
    except Exception as e:
        raise Exception(f"Database operation failed: {str(e)}") from e
```

### 3. Standardized Return Format
Always return a dictionary with these keys:
- `operation`: The operation that was executed
- `status`: 'success' or error information
- Additional operation-specific data

```python
return {
    'operation': 'query',
    'status': 'success',
    'rows': results,
    'row_count': len(results)
}
```

### 4. Type Conversion
Handle type conversions specific to your database (like DynamoDB's float→Decimal conversion):

```python
@staticmethod
def _convert_types(obj):
    # Database-specific type conversions
    pass
```

### 5. Connection Pooling
For production use, implement connection pooling to avoid creating new connections for each operation.

## Testing Custom Executors

```python
import pytest
from core.tools.spec.tool_context import ToolContext
from tests.tools.mocks import MockMemory, MockMetrics

@pytest.mark.asyncio
async def test_custom_executor():
    spec = CustomDbToolSpec(
        id="test-tool",
        tool_name="test",
        description="Test",
        # ... spec config
    )
    
    executor = CustomDbExecutor(spec)
    ctx = ToolContext(
        user_id="test-user",
        memory=MockMemory(),
        metrics=MockMetrics()
    )
    
    result = await executor.execute({'operation': 'test_op'}, ctx)
    
    assert result.content['status'] == 'success'
```

## Directory Structure

```
db_executors/
├── __init__.py              # Exports
├── README.md                # This file
├── base_db_executor.py      # Base class for all DB executors
├── dynamodb_executor.py     # DynamoDB implementation
├── postgresql_executor.py   # PostgreSQL (future)
├── mysql_executor.py        # MySQL (future)
└── sqlite_executor.py       # SQLite (future)
```

## Related Documentation

- [Database Strategies](../db_strategies/README.md) - Strategy pattern implementation
- [Base Executor](../base_executor.py) - Common executor functionality
- [Tool Specification](../../spec/tool_types.py) - Tool spec definitions
