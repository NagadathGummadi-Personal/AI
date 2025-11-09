# Tool Executors - Comprehensive Test Suite

## Overview

This directory contains comprehensive tests for the generic tool execution system with full support for Function, HTTP, and Database tools using the Strategy pattern for extensibility.

## What Was Accomplished

### 1. **Generic Database Executor with Strategy Pattern** ✅

Created a fully generic database executor that can work with any database backend:

- **Strategy Interface** (`IDbOperationStrategy`): Defines contract for database operations
- **Concrete Strategies**:
  - `DynamoDBStrategy`: AWS DynamoDB operations with automatic float→Decimal conversion
  - `PostgreSQLStrategy`: PostgreSQL async operations using asyncpg
  - `MySQLStrategy`: MySQL async operations using aiomysql
  - `SQLiteStrategy`: SQLite async operations using aiosqlite
- **Factory Pattern** (`DbStrategyFactory`): Creates appropriate strategy based on driver
- **Extensibility**: Easy to add new database backends by implementing `IDbOperationStrategy`

### 2. **Three Fully Implemented Tools** ✅

#### Tool 1: Division Function Tool
- **Purpose**: Performs division with error handling
- **Features**:
  - Division by zero error handling
  - Float and negative number support
  - Full ToolResult and ToolError implementation
  - Type coercion for string inputs

#### Tool 2: HTTP API Tool
- **Purpose**: Interacts with REST API (GET and POST)
- **Endpoint**: `https://kdahhpfkwb.execute-api.us-west-2.amazonaws.com/api/items`
- **Features**:
  - GET requests to list items
  - POST requests to create items
  - Custom headers and query parameters support
  - JSON request/response handling

#### Tool 3: DynamoDB Tool
- **Purpose**: Add items to DynamoDB table
- **Table**: `api-test-items`
- **Features**:
  - Put item operations
  - Automatic float→Decimal conversion for DynamoDB compatibility
  - Support for all DynamoDB data types
  - Real AWS DynamoDB integration

### 3. **Mock Implementations for Testing** ✅

Complete mock implementations for all tool interfaces:

- **MockMemory**: In-memory key-value storage with locking
- **MockMetrics**: Metrics collection (increments, observations, timings)
- **MockTracer**: Distributed tracing with span tracking
- **MockLimiter**: Rate limiting simulation
- **MockValidator**: Parameter validation with configurable failures
- **MockSecurity**: Authorization and egress checks

### 4. **Comprehensive Test Suite** ✅

**21 tests** covering all aspects of tool execution:

#### Division Tool Tests (8 tests)
- ✅ Successful division
- ✅ Division by zero error handling
- ✅ Float division
- ✅ Negative numbers
- ✅ Minimal context (without optional services)
- ✅ Idempotency with caching
- ✅ Validation failure handling
- ✅ Authorization failure handling

#### HTTP Tool Tests (6 tests)
- ✅ GET requests
- ✅ POST requests with body
- ✅ Custom headers
- ✅ Query parameters
- ✅ Idempotency
- ✅ Minimal context

#### DynamoDB Tool Tests (5 tests)
- ✅ Successful put_item operation
- ✅ Full context with all services (metrics, tracer, limiter, etc.)
- ✅ Idempotency with result caching
- ✅ Minimal context
- ✅ Multiple items insertion

#### Integration Tests (2 tests)
- ✅ All three tools with shared context
- ✅ Parallel execution of multiple operations

## Test Results

```
21 passed in 14.50s
```

All tests pass successfully with:
- Full logging integration
- Metrics collection
- Distributed tracing
- Rate limiting
- Memory/caching
- Security checks
- Parameter validation

## Key Features Demonstrated

### 1. Full Tool Context Usage

Every test demonstrates comprehensive usage of `ToolContext`:

```python
context = ToolContext(
    tenant_id="tenant-test-001",
    user_id="user-test-001",
    session_id="session-{uuid}",
    trace_id="trace-{uuid}",
    locale="en-US",
    timezone="America/Los_Angeles",
    memory=MockMemory(),        # Caching and idempotency
    metrics=MockMetrics(),      # Performance tracking
    tracer=MockTracer(),        # Distributed tracing
    limiter=MockLimiter(),      # Rate limiting
    validator=MockValidator(),  # Input validation
    security=MockSecurity()     # Authorization
)
```

### 2. Error Handling

All tools properly handle errors and return `ToolResult` with error information instead of raising exceptions:

```python
# Division by zero returns error result, not exception
result = await executor.execute({'numerator': 10, 'denominator': 0}, ctx)
assert 'error' in result.content
```

### 3. Idempotency

Tools support idempotency with automatic caching:

```python
spec.idempotency.enabled = True
spec.idempotency.persist_result = True
result1 = await executor.execute(args, ctx)  # Execute
result2 = await executor.execute(args, ctx)  # Uses cache
```

### 4. Metrics & Tracing

All executions record metrics and create trace spans:

```python
# Metrics recorded
assert metrics.get_incr_count('tool.executions') > 0
assert len(metrics.timings) > 0

# Trace spans created
assert any('division.execute' in span['name'] for span in tracer.spans)
```

## Architecture Highlights

### Strategy Pattern Implementation

```python
# Factory creates appropriate strategy based on driver
strategy = DbStrategyFactory.get_strategy('dynamodb')  # or 'postgresql', 'mysql', 'sqlite'

# Execute using strategy
result = await strategy.execute_operation(args, spec, timeout)
```

### Extensibility

Adding a new database backend is simple:

```python
class MongoDBStrategy(IDbOperationStrategy):
    async def execute_operation(self, args, spec, timeout):
        # Implement MongoDB operations
        pass

# Register the strategy
DbStrategyFactory.register_strategy('mongodb', MongoDBStrategy())
```

## Running the Tests

```bash
# Run all tool tests
uv run pytest tests/tools/test_tool_executors.py -v

# Run specific tool tests
uv run pytest tests/tools/test_tool_executors.py::TestDivisionTool -v
uv run pytest tests/tools/test_tool_executors.py::TestHttpTool -v
uv run pytest tests/tools/test_tool_executors.py::TestDynamoDBTool -v

# Run integration tests
uv run pytest tests/tools/test_tool_executors.py::TestToolIntegration -v
```

## Dependencies

```bash
# Install test dependencies
uv pip install pytest pytest-asyncio boto3

# For actual database operations (optional for tests):
# uv pip install asyncpg aiomysql aiosqlite
```

## Files Created

1. **`core/tools/executors/db_strategies.py`** - Database strategy pattern implementation
2. **`tests/tools/mocks.py`** - Mock implementations for all interfaces
3. **`tests/tools/tool_implementations.py`** - Three tool implementations
4. **`tests/tools/test_tool_executors.py`** - Comprehensive test suite
5. **`tests/tools/README.md`** - This documentation

## Notable Implementation Details

### DynamoDB Float Conversion

DynamoDB requires `Decimal` types for numbers with decimal points. The strategy automatically converts:

```python
# Input: {'price': 99.99} (float)
# Converted to: {'price': Decimal('99.99')}
item_converted = DynamoDBStrategy._convert_floats_to_decimal(item)
```

### Circular Import Fix

Fixed circular import between `tool_interfaces`, `tool_result`, and `tool_context` using `TYPE_CHECKING`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..spec.tool_result import ToolResult
    from ..spec.tool_types import ToolSpec
```

### Asyncio Configuration

Added pytest configuration for async tests in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = ["asyncio: marks tests as async tests"]
asyncio_mode = "auto"
```

## Next Steps

- Add more database strategies (MongoDB, Redis, etc.)
- Add retry logic tests
- Add circuit breaker tests
- Add timeout handling tests
- Add more HTTP methods (PUT, DELETE, PATCH)
- Add batch DynamoDB operations


