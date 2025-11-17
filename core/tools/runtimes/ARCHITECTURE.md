# Executors Architecture

This document describes the modular architecture of the Tools Executors system, designed for extensibility and maintainability following SOLID principles.

## 📁 Folder Structure

```
executors/
├── __init__.py                    # Main exports
├── ARCHITECTURE.md                # This file
├── base_executor.py               # Base class for all executors
├── executor.py                    # IExecutor interface
├── executor_factory.py            # Factory for creating executors
├── function_executor.py           # Function tool execution
├── http_executor.py               # HTTP tool execution
├── db_executor.py                 # DB tool execution (factory)
├── noop_executor.py               # No-op placeholder
│
├── db_executors/                  # 🗄️ Database-specific executors
│   ├── __init__.py
│   ├── README.md                  # Extensibility guide
│   ├── base_db_executor.py        # Base class for DB executors
│   └── dynamodb_executor.py       # DynamoDB implementation
│
├── function_executors/            # 🔧 Function-based executors (future)
│   └── __init__.py
│
├── http_executors/                # 🌐 HTTP-based executors (future)
│   └── __init__.py
│
├── db_strategies/                 # 📊 Database operation strategies
│   ├── __init__.py
│   ├── README.md                  # Strategy pattern guide
│   ├── strategy_interface.py      # IDbOperationStrategy
│   ├── dynamodb_strategy.py       # DynamoDB operations
│   └── strategy_factory.py        # DbStrategyFactory
│
├── policies/                      # 🔄 Resilience policies
│   ├── __init__.py
│   ├── README.md
│   ├── circuit_breaker/           # Circuit breaker implementations
│   └── retry/                     # Retry implementations
│
├── idempotency/                   # 🔑 Idempotency key generators
│   ├── __init__.py
│   ├── README.md
│   └── idempotency_key_generator.py
│
├── validators/                    # ✅ Parameter validators
│   ├── __init__.py
│   ├── validator.py
│   ├── basic_validator.py
│   ├── noop_validator.py
│   └── validator_factory.py
│
└── usage_calculators/             # 📈 Usage/cost calculators
    ├── token_calculators.py
    ├── cost_calculator.py
    └── generic_calculator.py
```

## 🏗️ Architecture Patterns

### 1. Strategy Pattern (Database Operations)

Database operations use the Strategy pattern to allow runtime selection of database-specific implementations:

```
IDbOperationStrategy (Interface)
├── DynamoDBStrategy
├── PostgreSQLStrategy (future)
├── MySQL Strategy (future)
└── SQLiteStrategy (future)

DbStrategyFactory (Manages strategies)
```

**Benefits:**
- Easy to add new database providers
- No changes to executor code
- Strategies are testable in isolation

### 2. Template Method Pattern (Executors)

Base executors define the execution template, subclasses implement specific steps:

```
BaseToolExecutor (Template)
├── execute() - Common flow
├── _calculate_usage() - Shared logic
└── _create_result() - Shared logic

BaseDbExecutor extends BaseToolExecutor
├── execute() - DB-specific template
└── _execute_db_operation() - Abstract (implemented by subclasses)

DynamoDBExecutor extends BaseDbExecutor
└── _execute_db_operation() - DynamoDB-specific
```

**Benefits:**
- Consistent execution flow
- Shared validation, auth, idempotency
- Subclasses focus on business logic

### 3. Factory Pattern (Executor Creation)

```
ExecutorFactory
├── create_executor(spec, func) -> IToolExecutor
└── register(type, class) - Custom registration
```

**Benefits:**
- Centralized executor creation
- Runtime type selection
- Easy testing with mock executors

## 🔧 Usage Examples

### Using Database Executors

```python
from core.tools.executors.db_executors import DynamoDBExecutor
from core.tools.spec.tool_types import DynamoDbToolSpec

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

# Execute
result = await executor.execute({
    'operation': 'get_item',
    'key': {'id': 'user123'}
}, ctx)
```

### Creating Custom Database Executor

```python
from core.tools.executors.db_executors import BaseDbExecutor
from core.tools.executors.db_strategies import IDbOperationStrategy, DbStrategyFactory
from typing import Any, Dict

# Step 1: Create strategy
class MongoDBStrategy(IDbOperationStrategy):
    async def execute_operation(self, args, spec, timeout):
        # MongoDB implementation
        return {'operation': 'find', 'status': 'success', 'results': []}

# Step 2: Register strategy
DbStrategyFactory.register_strategy('mongodb', MongoDBStrategy())

# Step 3: Create executor
class MongoDBExecutor(BaseDbExecutor):
    def __init__(self, spec):
        super().__init__(spec)
        self.strategy = DbStrategyFactory.get_strategy('mongodb')
    
    async def _execute_db_operation(self, args, ctx, timeout):
        return await self.strategy.execute_operation(args, self.spec, timeout)

# Step 4: Use it
executor = MongoDBExecutor(spec)
result = await executor.execute(args, ctx)
```

## 🎯 Design Principles

### 1. Single Responsibility Principle (SRP)
- Each executor handles ONE tool type
- Strategies handle ONE database provider
- Validators handle ONE validation concern

### 2. Open/Closed Principle (OCP)
- Open for extension (new executors, strategies)
- Closed for modification (base classes stable)

### 3. Liskov Substitution Principle (LSP)
- All executors can replace IToolExecutor
- All strategies can replace IDbOperationStrategy

### 4. Interface Segregation Principle (ISP)
- Small, focused interfaces (IToolExecutor, IDbOperationStrategy)
- Clients don't depend on unused methods

### 5. Dependency Inversion Principle (DIP)
- Depend on abstractions (interfaces)
- Not on concrete implementations

## 🚀 Extensibility Guide

### Adding a New Database Provider

1. **Create Strategy** (`db_strategies/cassandra_strategy.py`):
```python
from .strategy_interface import IDbOperationStrategy

class CassandraStrategy(IDbOperationStrategy):
    async def execute_operation(self, args, spec, timeout):
        # Cassandra implementation
        pass
```

2. **Register Strategy**:
```python
from core.tools.executors.db_strategies import DbStrategyFactory
DbStrategyFactory.register_strategy('cassandra', CassandraStrategy())
```

3. **Create Executor** (`db_executors/cassandra_executor.py`):
```python
from .base_db_executor import BaseDbExecutor
from ..db_strategies import DbStrategyFactory

class CassandraExecutor(BaseDbExecutor):
    def __init__(self, spec):
        super().__init__(spec)
        self.strategy = DbStrategyFactory.get_strategy('cassandra')
    
    async def _execute_db_operation(self, args, ctx, timeout):
        return await self.strategy.execute_operation(args, self.spec, timeout)
```

4. **Export** (update `db_executors/__init__.py`):
```python
from .cassandra_executor import CassandraExecutor

__all__ = [
    ...
    "CassandraExecutor",
]
```

### Adding Custom Policies

Retry and circuit breaker policies follow the same pattern - see `policies/README.md`.

## 📊 Comparison with Old Structure

### Before (Monolithic)
```
executors/
├── executors.py (471 lines)    # All executors in one file
└── db_strategies.py (522 lines) # All strategies in one file
```

**Problems:**
- Hard to navigate
- Difficult to extend
- Tight coupling
- Large files

### After (Modular)
```
executors/
├── db_executors/              # Organized by type
│   ├── base_db_executor.py
│   └── dynamodb_executor.py
├── db_strategies/             # Separate concerns
│   ├── strategy_interface.py
│   ├── dynamodb_strategy.py
│   └── strategy_factory.py
└── function_executors/        # Future extensibility
```

**Benefits:**
- ✅ Clear organization
- ✅ Easy to find code
- ✅ Simple to extend
- ✅ Testable in isolation
- ✅ Follows standards (like policies/)

## 🧪 Testing Strategy

### Unit Tests
- Test each executor in isolation
- Mock dependencies (strategies, validators)
- Test error handling

### Integration Tests  
- Test executor + strategy integration
- Test with real database connections (LocalStack for DynamoDB)
- Test full execution flow

### Example Test Structure
```python
tests/
└── tools/
    ├── test_db_executors.py         # Executor tests
    ├── test_db_strategies.py        # Strategy tests
    └── test_executor_integration.py # End-to-end tests
```

## 📝 Coding Standards

All new executors and strategies must follow these standards:

### 1. Documentation
- Module-level docstring with purpose, classes, usage
- Class-level docstring with description, attributes, methods
- Method-level docstring with Args, Returns, Raises, Examples

### 2. Type Hints
- All parameters and return values typed
- Use `Dict[str, Any]` for flexible dictionaries
- Use `Optional[T]` for nullable types

### 3. Error Handling
- Catch specific exceptions
- Provide clear error messages
- Include installation instructions for missing dependencies

### 4. Async/Await
- Use `async def` for I/O operations
- Use `asyncio.to_thread()` for blocking calls
- Respect timeout parameters

### 5. Stateless Design
- No instance variables for connections/state
- Create connections per operation
- Close resources properly

## 🔗 Related Documentation

- [Database Executors README](db_executors/README.md)
- [Database Strategies README](db_strategies/README.md)
- [Policies README](policies/README.md)
- [Idempotency README](idempotency/README.md)
- [Validators README](validators/README.md)

## 💡 Future Enhancements

### Planned
- [ ] PostgreSQL executor and strategy
- [ ] MySQL executor and strategy
- [ ] SQLite executor and strategy
- [ ] Function executors folder organization
- [ ] HTTP executors folder organization

### Under Consideration
- [ ] MongoDB strategy
- [ ] Redis strategy
- [ ] Elasticsearch strategy
- [ ] GraphQL executor
- [ ] gRPC executor

## 📞 Contributing

When adding new executors or strategies:

1. Follow the folder structure
2. Implement required interfaces
3. Add comprehensive documentation
4. Include usage examples
5. Write unit tests
6. Update this ARCHITECTURE.md
7. Update relevant README.md files

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0

