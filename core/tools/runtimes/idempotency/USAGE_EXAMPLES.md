# Idempotency Key Generation - Usage Examples

## Overview

This document provides examples of how to use different idempotency key generation strategies when building tools. The idempotency key generator can be specified at tool build time and determines how duplicate operations are detected.

## Table of Contents

1. [Default Strategy](#1-default-strategy)
2. [Field-Based Strategy](#2-field-based-strategy)
3. [Hash-Based Strategy](#3-hash-based-strategy)
4. [Custom Strategy](#4-custom-strategy)
5. [Factory Pattern](#5-factory-pattern)
6. [Use Case Examples](#6-use-case-examples)

---

## 1. Default Strategy

The default strategy uses SHA-256 hash of tool ID, user/session context, and all arguments.

### Example

```python
from core.tools.spec.tool_types import FunctionToolSpec
from core.tools.enum import ToolType, ToolReturnType, ToolReturnTarget

# Create tool spec without specifying generator
# Will use DefaultIdempotencyKeyGenerator
spec = FunctionToolSpec(
    id="payment-processor-v1",
    tool_name="process_payment",
    description="Process payment transaction",
    tool_type=ToolType.FUNCTION,
    parameters=[],
    return_type=ToolReturnType.JSON,
    return_target=ToolReturnTarget.STEP
)

# Idempotency is enabled in config
spec.idempotency.enabled = True
spec.idempotency.persist_result = True

# Key will be generated from: tool_id + user_id + session_id + all_args
# Result: SHA-256 hash (e.g., "a3f2b1...")
```

**When to use:**
- General-purpose tools
- When you want to consider all arguments for idempotency
- When user/session context is important

---

## 2. Field-Based Strategy

Uses only specified fields from arguments, ignoring user/session context.

### Example 1: Payment Processing

```python
from core.tools.spec.tool_types import FunctionToolSpec
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator
from core.tools.spec.tool_parameters import StringParameter, NumericParameter

# Payment tool - idempotent by transaction_id
spec = FunctionToolSpec(
    id="payment-processor-v1",
    tool_name="process_payment",
    description="Process payment transaction",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="transaction_id", required=True),
        StringParameter(name="customer_id", required=True),
        NumericParameter(name="amount", required=True),
        StringParameter(name="currency", required=True)
    ],
)

# Configure idempotency with field-based strategy
spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id']  # Only use transaction_id
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()

# Key will be generated from: tool_id + transaction_id
# Multiple calls with same transaction_id will be treated as duplicates
# Even if customer_id, amount, or currency differ!
```

### Example 2: Order Fulfillment

```python
# Order fulfillment - idempotent by order_id
spec = FunctionToolSpec(
    id="order-fulfillment-v1",
    tool_name="fulfill_order",
    description="Fulfill customer order",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="order_id", required=True),
        StringParameter(name="warehouse_id", required=False),
        StringParameter(name="shipping_method", required=False)
    ],
)

spec.idempotency.enabled = True
spec.idempotency.key_fields = ['order_id']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()

# Key = tool_id + order_id
# Same order won't be fulfilled twice, regardless of warehouse or shipping method
```

**When to use:**
- Business transactions with unique IDs
- When specific fields determine uniqueness
- When user context should NOT affect idempotency

---

## 3. Hash-Based Strategy

Advanced hash strategy with configurable algorithm and context inclusion.

### Example 1: High-Security Payment Processing

```python
from core.tools.executors.idempotency import HashBasedIdempotencyKeyGenerator

# Use SHA-512 for high security
spec = FunctionToolSpec(
    id="secure-payment-v1",
    tool_name="secure_payment",
    description="High-security payment processing",
    tool_type=ToolType.FUNCTION,
    parameters=[],
)

spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id', 'amount', 'timestamp']
spec.idempotency_key_generator = HashBasedIdempotencyKeyGenerator(
    algorithm='sha512',              # More secure than SHA-256
    include_user_context=True,       # Include user_id
    include_session_context=False    # Exclude session_id
)

# Key = SHA-512(tool_id + user_id + selected_fields)
# More secure but slower than SHA-256
```

### Example 2: Stateless API

```python
# API tool without session context
spec = HttpToolSpec(
    id="api-call-v1",
    tool_name="external_api",
    description="Call external API",
    tool_type=ToolType.HTTP,
    url="https://api.example.com/data",
)

spec.idempotency.enabled = True
spec.idempotency_key_generator = HashBasedIdempotencyKeyGenerator(
    algorithm='sha256',
    include_user_context=True,
    include_session_context=False  # Stateless - no session
)

# Key = SHA-256(tool_id + user_id + all_args)
# Works across different sessions for same user
```

**When to use:**
- Security-critical operations
- When you need specific hash algorithm
- When you want control over context inclusion

---

## 4. Custom Strategy

Implement your own key generation logic.

### Example 1: Time-Based Keys

```python
from core.tools.executors.idempotency import CustomIdempotencyKeyGenerator
from datetime import datetime

def time_based_key(args, ctx, spec):
    """
    Generate key that includes timestamp for time-sensitive operations.
    Operations are only considered duplicate within same minute.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')  # minute precision
    user_id = ctx.user_id or 'anonymous'
    request_id = args.get('request_id', '')
    return f"{spec.id}:{user_id}:{request_id}:{timestamp}"

spec = FunctionToolSpec(
    id="timed-operation-v1",
    tool_name="timed_operation",
    description="Operation with time-based idempotency",
    tool_type=ToolType.FUNCTION,
    parameters=[StringParameter(name="request_id", required=True)],
)

spec.idempotency.enabled = True
spec.idempotency_key_generator = CustomIdempotencyKeyGenerator(time_based_key)

# Same request_id within same minute = duplicate
# Same request_id in different minute = allowed
```

### Example 2: Geographic Partitioning

```python
def geo_based_key(args, ctx, spec):
    """
    Generate key that includes geographic region.
    Same operation can run in different regions.
    """
    region = args.get('region', 'default')
    user_id = ctx.user_id or 'anonymous'
    order_id = args.get('order_id', '')
    return f"{spec.id}:{region}:{user_id}:{order_id}"

spec = FunctionToolSpec(
    id="geo-distributed-v1",
    tool_name="process_order",
    description="Process order in specific region",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="order_id", required=True),
        StringParameter(name="region", required=True)
    ],
)

spec.idempotency.enabled = True
spec.idempotency_key_generator = CustomIdempotencyKeyGenerator(geo_based_key)

# Same order in US-WEST = separate from same order in EU-CENTRAL
```

### Example 3: External Service Integration

```python
import requests

def external_id_service_key(args, ctx, spec):
    """
    Use external ID generation service for distributed uniqueness.
    """
    # Call external service to generate distributed unique ID
    response = requests.post('https://id-service.internal/generate', json={
        'tool_id': spec.id,
        'user_id': ctx.user_id,
        'data': args
    })
    return response.json()['unique_id']

spec = FunctionToolSpec(
    id="distributed-tool-v1",
    tool_name="distributed_operation",
    description="Operation with distributed ID generation",
    tool_type=ToolType.FUNCTION,
    parameters=[],
)

spec.idempotency.enabled = True
spec.idempotency_key_generator = CustomIdempotencyKeyGenerator(external_id_service_key)

# Uses centralized service for ID generation
# Ensures uniqueness across distributed systems
```

**When to use:**
- Complex business rules
- Time-sensitive operations
- Geographic/tenant partitioning
- Integration with external ID services

---

## 5. Factory Pattern

Use the factory to register and retrieve generators by name.

### Example

```python
from core.tools.executors.idempotency import (
    IdempotencyKeyGeneratorFactory,
    IIdempotencyKeyGenerator
)

# 1. Create custom generator class
class TenantBasedIdempotencyKeyGenerator(IIdempotencyKeyGenerator):
    def generate_key(self, args, ctx, spec):
        tenant_id = ctx.tenant_id or 'default'
        user_id = ctx.user_id or 'anonymous'
        import hashlib
        data = f"{spec.id}:{tenant_id}:{user_id}:{json.dumps(args, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()

# 2. Register the custom generator
IdempotencyKeyGeneratorFactory.register(
    'tenant_based',
    TenantBasedIdempotencyKeyGenerator()
)

# 3. Use the registered generator
generator = IdempotencyKeyGeneratorFactory.get_generator('tenant_based')

spec = FunctionToolSpec(
    id="multi-tenant-tool-v1",
    tool_name="tenant_operation",
    description="Multi-tenant operation",
    tool_type=ToolType.FUNCTION,
    parameters=[],
)

spec.idempotency.enabled = True
spec.idempotency_key_generator = generator

# Key includes tenant isolation
```

**When to use:**
- Sharing generators across multiple tools
- Central configuration management
- Plugin-style architecture

---

## 6. Use Case Examples

### Use Case 1: E-Commerce Payment Processing

```python
# Requirement: Payment should be idempotent by transaction_id
# Same transaction_id should never be processed twice

from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator

payment_spec = FunctionToolSpec(
    id="ecommerce-payment-v1",
    tool_name="process_payment",
    description="Process e-commerce payment",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="transaction_id", required=True),
        StringParameter(name="order_id", required=True),
        NumericParameter(name="amount", required=True),
        StringParameter(name="payment_method", required=True)
    ],
)

payment_spec.idempotency.enabled = True
payment_spec.idempotency.persist_result = True
payment_spec.idempotency.ttl_s = 86400  # 24 hours
payment_spec.idempotency.key_fields = ['transaction_id']
payment_spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()

# Result: Only transaction_id matters
# Retry with same transaction_id = returns cached result
# Different transaction_id = processes payment
```

### Use Case 2: User Registration

```python
# Requirement: User registration should be idempotent by email
# Same email should not be registered twice

from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator

registration_spec = FunctionToolSpec(
    id="user-registration-v1",
    tool_name="register_user",
    description="Register new user account",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="email", required=True),
        StringParameter(name="username", required=True),
        StringParameter(name="password", required=True)
    ],
)

registration_spec.idempotency.enabled = True
registration_spec.idempotency.persist_result = True
registration_spec.idempotency.key_fields = ['email']
registration_spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()

# Result: Email uniqueness enforced
# Retry with same email = returns existing user
# Different email = creates new user
```

### Use Case 3: API Rate Limiting with User Context

```python
# Requirement: Rate limit per user, but same request can be retried

from core.tools.executors.idempotency import HashBasedIdempotencyKeyGenerator

api_spec = HttpToolSpec(
    id="external-api-v1",
    tool_name="call_external_api",
    description="Call external API with rate limiting",
    tool_type=ToolType.HTTP,
    url="https://api.external.com/endpoint",
)

api_spec.idempotency.enabled = True
api_spec.idempotency.persist_result = True
api_spec.idempotency.ttl_s = 300  # 5 minutes
api_spec.idempotency_key_generator = HashBasedIdempotencyKeyGenerator(
    algorithm='sha256',
    include_user_context=True,      # Per-user caching
    include_session_context=False   # Works across sessions
)

# Result: Same user, same args = cached for 5 minutes
# Different user, same args = separate cache entry
# Reduces load on external API
```

### Use Case 4: Distributed Lock with Custom Strategy

```python
# Requirement: Distributed lock using Redis for key generation

from core.tools.executors.idempotency import CustomIdempotencyKeyGenerator
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def redis_based_key(args, ctx, spec):
    """Use Redis INCR for distributed unique IDs"""
    # Generate distributed unique ID
    unique_id = redis_client.incr('tool:counter')
    return f"{spec.id}:{ctx.user_id}:{unique_id}"

lock_spec = FunctionToolSpec(
    id="distributed-lock-v1",
    tool_name="acquire_lock",
    description="Acquire distributed lock",
    tool_type=ToolType.FUNCTION,
    parameters=[StringParameter(name="resource_id", required=True)],
)

lock_spec.idempotency.enabled = True
lock_spec.idempotency_key_generator = CustomIdempotencyKeyGenerator(redis_based_key)

# Result: Guaranteed unique keys across distributed system
# Uses Redis for atomic counter
```

---

## Summary

| Strategy | Use When | Key Components |
|----------|----------|----------------|
| **Default** | General purpose | tool_id + user_id + session_id + all_args |
| **Field-Based** | Business transactions | tool_id + specified_fields |
| **Hash-Based** | Security/control | Configurable hash + selective context |
| **Custom** | Complex requirements | Your custom logic |

### Best Practices

1. **Choose the right strategy for your use case**
   - Payments/Orders: Field-Based with transaction ID
   - User operations: Field-Based with user identifier
   - API calls: Hash-Based with user context
   - Complex logic: Custom strategy

2. **Configure TTL appropriately**
   - Short-lived operations: 5-15 minutes
   - Business transactions: 24 hours
   - User registrations: Indefinite (or very long)

3. **Test your idempotency strategy**
   - Verify same inputs produce same key
   - Test across different users/sessions
   - Validate duplicate detection works

4. **Document your choice**
   - Explain why you chose specific strategy
   - Document which fields are used
   - Note any caveats or limitations

---

## Migration from Old System

If you have existing tools using the old hardcoded idempotency key generation:

```python
# Old way (hardcoded in executor)
spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id']
# Key generation was hardcoded in BaseToolExecutor

# New way (explicit strategy)
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator

spec.idempotency.enabled = True
spec.idempotency.key_fields = ['transaction_id']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()
# OR leave as None to use default (backward compatible)
```

**Note:** If `idempotency_key_generator` is `None`, the system uses `DefaultIdempotencyKeyGenerator`, which maintains backward compatibility with the old behavior.

