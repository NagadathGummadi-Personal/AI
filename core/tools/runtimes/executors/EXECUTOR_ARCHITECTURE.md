# Executor Architecture - Standardized Structure

## Overview

All executor types now follow a consistent, standardized architecture with:
- **Interface**: Abstract protocol defining the executor contract
- **Base Class**: Common implementation with shared functionality
- **Factory**: Centralized creation and registration system
- **Implementations**: Concrete executor classes

This architecture ensures:
✅ Consistent patterns across all executor types
✅ Easy extensibility with custom executors
✅ Factory-based creation for flexibility
✅ Clean separation of concerns

---

## Architecture Pattern

```
Interface (IExecutor)
    ↓
Base Class (BaseExecutor)
    ↓
Factory (ExecutorFactory) ←→ Implementations (ConcreteExecutor)
```

### Standard Files Per Executor Type:

```
executor_type/
├── __init__.py                      # Exports all components
├── {type}_executor_interface.py     # Interface definition
├── base_{type}_executor.py          # Base implementation
├── {type}_executor_factory.py       # Factory for creation/registration
├── {type}_executor.py               # Standard implementation
└── [custom_executor.py]             # Optional custom implementations
```

---

## 1. Database Executors (`db_executors/`)

### ✅ Structure:
```
db_executors/
├── __init__.py
├── db_executor.py                   # IDbExecutor interface
├── base_db_executor.py              # BaseDbExecutor base class
├── db_executor_factory.py           # DbExecutorFactory
├── dynamodb_executor.py             # DynamoDBExecutor implementation
└── README.md
```

### Components:
- **Interface**: `IDbExecutor`
- **Base**: `BaseDbExecutor`
- **Factory**: `DbExecutorFactory`
- **Implementations**: `DynamoDBExecutor`

### Usage:
```python
from core.tools.runtimes.executors.db_executors import DbExecutorFactory

# Using factory
executor = DbExecutorFactory.get_executor(spec)
result = await executor.execute(args, ctx)

# Custom executor
class MongoDBExecutor(BaseDbExecutor):
    async def _execute_db_operation(self, args, ctx, timeout):
        # Your MongoDB logic
        return {'status': 'success', 'data': data}

DbExecutorFactory.register('mongodb', MongoDBExecutor)
```

---

## 2. Function Executors (`function_executors/`)

### ✅ Structure:
```
function_executors/
├── __init__.py
├── function_executor_interface.py   # IFunctionExecutor interface
├── base_function_executor.py        # BaseFunctionExecutor base class  ✅ NEW
├── function_executor_factory.py     # FunctionExecutorFactory          ✅ NEW
└── function_executor.py             # FunctionToolExecutor implementation
```

### Components:
- **Interface**: `IFunctionExecutor`
- **Base**: `BaseFunctionExecutor` ✅ **NEW**
- **Factory**: `FunctionExecutorFactory` ✅ **NEW**
- **Implementations**: `FunctionToolExecutor`

### Usage:
```python
from core.tools.runtimes.executors.function_executors import FunctionExecutorFactory

# Using factory
executor = FunctionExecutorFactory.create_executor(spec, my_function)
result = await executor.execute(args, ctx)

# Custom executor
class CachedFunctionExecutor(BaseFunctionExecutor):
    def __init__(self, spec, func):
        super().__init__(spec, func)
        self.cache = {}
    
    async def _execute_function(self, args, ctx, timeout):
        cache_key = str(args)
        if cache_key in self.cache:
            return self.cache[cache_key]
        result = await asyncio.wait_for(self.func(args, ctx), timeout=timeout)
        self.cache[cache_key] = result
        return result

FunctionExecutorFactory.register('cached', CachedFunctionExecutor)
```

---

## 3. HTTP Executors (`http_executors/`)

### ✅ Structure:
```
http_executors/
├── __init__.py
├── http_executor_interface.py       # IHttpExecutor interface
├── base_http_executor.py            # BaseHttpExecutor base class        ✅ NEW
├── http_executor_factory.py         # HttpExecutorFactory                ✅ NEW
└── http_executor.py                 # HttpToolExecutor implementation
```

### Components:
- **Interface**: `IHttpExecutor`
- **Base**: `BaseHttpExecutor` ✅ **NEW**
- **Factory**: `HttpExecutorFactory` ✅ **NEW**
- **Implementations**: `HttpToolExecutor`

### Usage:
```python
from core.tools.runtimes.executors.http_executors import HttpExecutorFactory

# Using factory
executor = HttpExecutorFactory.create_executor(spec)
result = await executor.execute(args, ctx)

# Custom executor (GraphQL example)
class GraphQLExecutor(BaseHttpExecutor):
    async def _execute_http_request(self, args, ctx, timeout):
        query = args.get('query')
        variables = args.get('variables', {})
        
        session = await self._get_session()
        async with session.post(
            self.spec.base_url,
            json={'query': query, 'variables': variables},
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            data = await response.json()
            return {'status': response.status, 'data': data}

HttpExecutorFactory.register('graphql', GraphQLExecutor)
```

**Note**: HTTP executors require `aiohttp`. Install with: `pip install aiohttp`

---

## Factory Methods

All factories now support consistent methods:

### Common Factory API:

```python
# List registered executor types
types = Factory.list_executor_types()
# Returns: ['standard', 'default', 'custom1', 'custom2']

# Get executor class
executor_class = Factory.get_executor_class('standard')

# Register custom executor
Factory.register('custom_name', CustomExecutorClass)

# Unregister (except built-in types)
Factory.unregister('custom_name')

# Create executor
executor = Factory.create_executor(spec, ...)
```

### Factory-Specific Creation:

```python
# Database
DbExecutorFactory.get_executor(db_spec)

# Function  
FunctionExecutorFactory.create_executor(spec, func, executor_type='standard')

# HTTP
HttpExecutorFactory.create_executor(spec, executor_type='standard')
```

---

## Extending with Custom Executors

### Step 1: Create Your Executor

Inherit from the appropriate base class and implement required methods:

```python
from core.tools.runtimes.executors.function_executors import BaseFunctionExecutor
import asyncio

class StreamingFunctionExecutor(BaseFunctionExecutor):
    """Executor that supports streaming responses."""
    
    async def _execute_function(self, args, ctx, timeout):
        """Execute with streaming support."""
        # Your streaming logic
        async for chunk in self.func(args, ctx):
            yield chunk
```

### Step 2: Register with Factory

```python
from core.tools.runtimes.executors.function_executors import FunctionExecutorFactory

FunctionExecutorFactory.register('streaming', StreamingFunctionExecutor)
```

### Step 3: Use It

```python
# Create executor with your custom type
executor = FunctionExecutorFactory.create_executor(
    spec,
    my_streaming_function,
    executor_type='streaming'
)

# Execute
result = await executor.execute(args, ctx)
```

---

## Benefits of Standardized Architecture

### 1. **Consistency**
- Same patterns across all executor types
- Predictable API for all executors
- Easy to learn and use

### 2. **Extensibility**
- Simple registration system
- No need to modify core code
- Runtime addition of new executor types

### 3. **Testability**
- Easy to mock and test
- Consistent test patterns
- Factory makes testing flexible

### 4. **Maintainability**
- Clear separation of concerns
- Base classes handle common logic
- Implementations focus on specific behavior

### 5. **Flexibility**
- Choose executor type at runtime
- Mix and match implementations
- Easy A/B testing of executors

---

## Migration Guide

### From Direct Instantiation to Factory:

**Before:**
```python
executor = FunctionToolExecutor(spec, func)
```

**After:**
```python
executor = FunctionExecutorFactory.create_executor(spec, func)
```

### Benefits of Using Factory:
- ✅ Can switch executor types without code changes
- ✅ Custom executors available automatically
- ✅ Centralized configuration
- ✅ Better for testing (mock factory instead of class)

---

## Complete Example

### Creating a Custom Cached Function Executor:

```python
# 1. Define your executor
from core.tools.runtimes.executors.function_executors import BaseFunctionExecutor
import asyncio

class CachedFunctionExecutor(BaseFunctionExecutor):
    """Function executor with built-in caching."""
    
    def __init__(self, spec, func):
        super().__init__(spec, func)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def _execute_function(self, args, ctx, timeout):
        # Generate cache key
        cache_key = self._generate_cache_key(args)
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        # Execute function
        result = await asyncio.wait_for(
            self.func(args, ctx),
            timeout=timeout
        )
        
        # Store in cache
        self.cache[cache_key] = (result, time.time())
        
        return result
    
    def _generate_cache_key(self, args):
        return str(sorted(args.items()))

# 2. Register it
from core.tools.runtimes.executors.function_executors import FunctionExecutorFactory

FunctionExecutorFactory.register('cached', CachedFunctionExecutor)

# 3. Use it
spec = ToolSpec(tool_name="expensive_operation", ...)

async def expensive_operation(args, ctx):
    # Expensive computation
    await asyncio.sleep(5)
    return {'result': args['x'] * 2}

# Create cached executor
executor = FunctionExecutorFactory.create_executor(
    spec,
    expensive_operation,
    executor_type='cached'
)

# First call - executes function (slow)
result1 = await executor.execute({'x': 10}, ctx)  # Takes 5 seconds

# Second call - returns from cache (fast)
result2 = await executor.execute({'x': 10}, ctx)  # Instant!
```

---

## Summary

### What Changed:
1. ✅ Added `BaseFunctionExecutor` base class
2. ✅ Added `FunctionExecutorFactory` factory
3. ✅ Added `BaseHttpExecutor` base class
4. ✅ Added `HttpExecutorFactory` factory
5. ✅ Updated all __init__.py files to export new classes
6. ✅ Standardized architecture across all executor types

### What Stayed the Same:
- ✅ Existing `FunctionToolExecutor` still works
- ✅ Existing `HttpToolExecutor` still works
- ✅ All existing code continues to function
- ✅ No breaking changes

### What You Can Do Now:
- ✅ Create custom executors easily
- ✅ Register them with factories
- ✅ Use factory methods for creation
- ✅ Switch executor types at runtime
- ✅ Follow consistent patterns everywhere

---

## Files Created

### New Files:
1. `core/tools/runtimes/executors/function_executors/base_function_executor.py`
2. `core/tools/runtimes/executors/function_executors/function_executor_factory.py`
3. `core/tools/runtimes/executors/http_executors/base_http_executor.py`
4. `core/tools/runtimes/executors/http_executors/http_executor_factory.py`

### Modified Files:
1. `core/tools/runtimes/executors/function_executors/__init__.py`
2. `core/tools/runtimes/executors/function_executors/function_executor.py`
3. `core/tools/runtimes/executors/http_executors/__init__.py`
4. `core/tools/runtimes/executors/http_executors/http_executor.py`
5. `core/tools/runtimes/executors/__init__.py`

---

## Next Steps

1. ✅ **All executors now follow standard pattern**
2. ✅ **Factories available for all types**
3. ✅ **Easy to add custom implementations**
4. ⏭️ **Consider adding more built-in executor types** (streaming, batching, etc.)
5. ⏭️ **Add factory configuration via config files**

The executor architecture is now fully standardized and ready for use! 🎉

