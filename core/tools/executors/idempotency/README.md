# Idempotency Key Generation - Pluggable Strategy Pattern

## Overview

This module implements a pluggable strategy pattern for idempotency key generation, allowing you to configure different key generation approaches at tool build time without affecting the execution flow.

## Problem Solved

**Before:** Idempotency key generation was hardcoded in `BaseToolExecutor`, making it inflexible and difficult to customize for different business requirements.

**After:** Idempotency key generation is now pluggable - you can:
- Choose from built-in strategies
- Create custom strategies
- Configure at tool build time
- Change without affecting execution flow

## Architecture

```
IIdempotencyKeyGenerator (Interface)
├── DefaultIdempotencyKeyGenerator
├── FieldBasedIdempotencyKeyGenerator
├── HashBasedIdempotencyKeyGenerator
└── CustomIdempotencyKeyGenerator

IdempotencyKeyGeneratorFactory
└── Manages and creates strategy instances
```

## Available Strategies

### 1. DefaultIdempotencyKeyGenerator (Default)

**Uses:** `tool_id + user_id + session_id + all_args`

```python
# Automatically used if no generator specified
spec = FunctionToolSpec(...)
spec.idempotency.enabled = True
# Uses default strategy
```

**When to use:**
- General-purpose tools
- When all context and arguments matter
- Backward compatibility with existing tools

---

### 2. FieldBasedIdempotencyKeyGenerator

**Uses:** `tool_id + specified_fields_only`

```python
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator

spec = FunctionToolSpec(...)
spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()
```

**When to use:**
- Payment processing (key by transaction ID)
- Order fulfillment (key by order ID)
- User registration (key by email)
- Any business transaction with unique identifier

---

### 3. HashBasedIdempotencyKeyGenerator

**Uses:** Configurable hash algorithm with selective context

```python
from core.tools.executors.idempotency import HashBasedIdempotencyKeyGenerator

spec = FunctionToolSpec(...)
spec.idempotency.enabled = True
spec.idempotency_key_generator = HashBasedIdempotencyKeyGenerator(
    algorithm='sha512',              # Or 'sha256', 'md5', etc.
    include_user_context=True,
    include_session_context=False
)
```

**When to use:**
- High-security scenarios (SHA-512)
- Performance-critical scenarios (MD5)
- Fine-grained control over context inclusion

---

### 4. CustomIdempotencyKeyGenerator

**Uses:** Your custom function

```python
from core.tools.executors.idempotency import CustomIdempotencyKeyGenerator

def my_custom_key(args, ctx, spec):
    # Your logic here
    return f"{spec.id}:{args['order_id']}:{args['timestamp']}"

spec = FunctionToolSpec(...)
spec.idempotency.enabled = True
spec.idempotency_key_generator = CustomIdempotencyKeyGenerator(my_custom_key)
```

**When to use:**
- Complex business rules
- Time-based keys
- Geographic partitioning
- Integration with external ID services

---

## Quick Start

### Example 1: Payment Processing

```python
from core.tools.spec.tool_types import FunctionToolSpec
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator
from core.tools.executors.executors import FunctionToolExecutor

# Define payment processing function
async def process_payment(args):
    # Payment logic
    return {"status": "success", "transaction_id": args['transaction_id']}

# Create tool spec
spec = FunctionToolSpec(
    id="payment-v1",
    tool_name="process_payment",
    description="Process payment",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="transaction_id", required=True),
        NumericParameter(name="amount", required=True)
    ]
)

# Configure idempotency - key by transaction_id only
spec.idempotency.enabled = True
spec.idempotency.persist_result = True
spec.idempotency.ttl_s = 86400  # 24 hours
spec.idempotency.key_fields = ['transaction_id']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()

# Create executor
executor = FunctionToolExecutor(spec, process_payment)

# Execute - will be idempotent by transaction_id
ctx = ToolContext(user_id="user123")
result = await executor.execute({
    'transaction_id': 'tx-12345',
    'amount': 99.99
}, ctx)
```

### Example 2: User Registration

```python
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator

spec = FunctionToolSpec(
    id="register-user-v1",
    tool_name="register_user",
    description="Register new user",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="email", required=True),
        StringParameter(name="username", required=True)
    ]
)

# Idempotent by email - prevent duplicate registrations
spec.idempotency.enabled = True
spec.idempotency.key_fields = ['email']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()
```

### Example 3: Custom Time-Based Keys

```python
from datetime import datetime
from core.tools.executors.idempotency import CustomIdempotencyKeyGenerator

def time_window_key(args, ctx, spec):
    """Keys are unique within 5-minute windows"""
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
    timestamp = timestamp[:-1] + '0'  # Round to 10-minute window
    return f"{spec.id}:{ctx.user_id}:{args['request_id']}:{timestamp}"

spec = FunctionToolSpec(
    id="rate-limited-api-v1",
    tool_name="call_api",
    description="Rate-limited API call",
    tool_type=ToolType.FUNCTION,
    parameters=[StringParameter(name="request_id", required=True)]
)

spec.idempotency.enabled = True
spec.idempotency.ttl_s = 600  # 10 minutes
spec.idempotency_key_generator = CustomIdempotencyKeyGenerator(time_window_key)
```

---

## Factory Pattern

Register and reuse generators across multiple tools:

```python
from core.tools.executors.idempotency import (
    IdempotencyKeyGeneratorFactory,
    IIdempotencyKeyGenerator
)

# 1. Create custom generator
class TenantBasedGenerator(IIdempotencyKeyGenerator):
    def generate_key(self, args, ctx, spec):
        return f"{spec.id}:{ctx.tenant_id}:{json.dumps(args, sort_keys=True)}"

# 2. Register it
IdempotencyKeyGeneratorFactory.register('tenant_based', TenantBasedGenerator())

# 3. Use it in multiple tools
for tool_spec in [payment_spec, order_spec, user_spec]:
    generator = IdempotencyKeyGeneratorFactory.get_generator('tenant_based')
    tool_spec.idempotency_key_generator = generator
```

---

## Integration with BaseToolExecutor

The `BaseToolExecutor._generate_idempotency_key` method automatically uses the configured strategy:

```python
class BaseToolExecutor:
    def _generate_idempotency_key(self, args, ctx):
        # Uses custom generator if specified
        if self.spec.idempotency_key_generator:
            return self.spec.idempotency_key_generator.generate_key(args, ctx, self.spec)
        
        # Falls back to default
        return DefaultIdempotencyKeyGenerator().generate_key(args, ctx, self.spec)
```

This means:
- ✅ No changes needed to executor code
- ✅ Strategy is configured at tool spec level
- ✅ Backward compatible (uses default if not specified)
- ✅ Works with all executor types (Function, HTTP, DB)

---

## Testing

All strategies are fully tested with 19 passing tests:

```bash
$ uv run pytest tests/tools/test_idempotency_strategies.py -v

19 passed in 0.10s
```

Test coverage includes:
- ✅ Deterministic key generation
- ✅ Different arguments produce different keys
- ✅ User/session context handling
- ✅ Field-based filtering
- ✅ Hash algorithm variations
- ✅ Custom function strategies
- ✅ Factory pattern registration
- ✅ Integration with tool specs

---

## Benefits

### 1. **Flexibility**
Configure key generation per tool based on business requirements

### 2. **Separation of Concerns**
Key generation logic separated from execution logic

### 3. **Reusability**
Create once, use across multiple tools

### 4. **Testability**
Easy to test different strategies in isolation

### 5. **Backward Compatibility**
Existing tools continue to work without changes

### 6. **Extensibility**
Easy to add new strategies without modifying core code

---

## File Structure

```
core/tools/executors/idempotency/
├── __init__.py
├── idempotency_key_generator.py    # All strategy implementations
├── README.md                        # This file
└── USAGE_EXAMPLES.md                # Detailed usage examples

tests/tools/
└── test_idempotency_strategies.py   # Comprehensive tests
```

---

## Migration Guide

### From Old System

```python
# OLD: Hardcoded in executor
spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id']
# Key generation was internal

# NEW: Explicit strategy
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator

spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()
```

### Backward Compatibility

If you don't specify `idempotency_key_generator`, the system uses `DefaultIdempotencyKeyGenerator`, which produces the same keys as the old system.

```python
# These are equivalent:
spec.idempotency.enabled = True
# (no generator specified)

# VS

from core.tools.executors.idempotency import DefaultIdempotencyKeyGenerator
spec.idempotency.enabled = True
spec.idempotency_key_generator = DefaultIdempotencyKeyGenerator()
```

---

## Best Practices

1. **Choose the right strategy**
   - Payments/Orders: `FieldBasedIdempotencyKeyGenerator`
   - User operations: `FieldBasedIdempotencyKeyGenerator`
   - API calls: `HashBasedIdempotencyKeyGenerator`
   - Complex logic: `CustomIdempotencyKeyGenerator`

2. **Configure TTL appropriately**
   - Short operations: 5-15 minutes
   - Business transactions: 24 hours
   - User data: Long or indefinite

3. **Test your strategy**
   - Verify same inputs = same key
   - Test across different users/sessions
   - Validate duplicate detection

4. **Document your choice**
   - Explain why you chose the strategy
   - Document which fields are used
   - Note any caveats

---

## Further Reading

- See `USAGE_EXAMPLES.md` for more detailed examples
- See `tests/tools/test_idempotency_strategies.py` for usage patterns
- See `idempotency_key_generator.py` for implementation details

---

## Summary

✅ **Pluggable** - Configure at tool build time  
✅ **Flexible** - Multiple strategies available  
✅ **Extensible** - Easy to add custom strategies  
✅ **Backward Compatible** - Works with existing tools  
✅ **Well Tested** - 19 passing tests  
✅ **Production Ready** - Used in all tool executors

