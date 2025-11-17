# Execution Policies - Pluggable Strategy Pattern

## Overview

This module implements pluggable strategies for circuit breakers and retry logic, allowing you to configure different resilience patterns at tool spec creation time without affecting the execution flow.

## Problem Solved

**Before:** Circuit breaker and retry logic was either hardcoded or configured through simple config objects that couldn't be customized per tool.

**After:** Circuit breaking and retry logic is now pluggable - you can:
- Choose from built-in strategies
- Create custom strategies
- Configure at tool build time
- Change without affecting execution flow
- Mix and match policies for different tools

## Architecture

```
Policies/
├── Circuit Breaker Policies
│   ├── ICircuitBreakerPolicy (Interface)
│   ├── StandardCircuitBreakerPolicy (uses pybreaker)
│   ├── AdaptiveCircuitBreakerPolicy (dynamic thresholds)
│   ├── NoOpCircuitBreakerPolicy (disabled)
│   └── CircuitBreakerPolicyFactory
│
└── Retry Policies
    ├── IRetryPolicy (Interface)
    ├── NoRetryPolicy (immediate failure)
    ├── FixedRetryPolicy (fixed delay)
    ├── ExponentialBackoffRetryPolicy (exponential backoff)
    ├── CustomRetryPolicy (user function)
    └── RetryPolicyFactory
```

## Quick Start

### 1. Circuit Breaker Policies

#### Standard Circuit Breaker

```python
from core.tools.executors.policies import StandardCircuitBreakerPolicy
from core.tools.spec.tool_types import FunctionToolSpec

# Create tool spec
spec = FunctionToolSpec(
    id="payment-v1",
    tool_name="process_payment",
    description="Process payment",
    # ... other config
)

# Configure circuit breaker at build time
spec.circuit_breaker_policy = StandardCircuitBreakerPolicy(
    failure_threshold=5,    # Open circuit after 5 failures
    recovery_timeout=30     # Try recovery after 30 seconds
)

# Circuit breaker states:
# CLOSED -> Normal operation
# OPEN -> Fails immediately (circuit open)
# HALF_OPEN -> Testing recovery
```

#### Adaptive Circuit Breaker

```python
from core.tools.executors.policies import AdaptiveCircuitBreakerPolicy

# Adjusts thresholds based on error rates
spec.circuit_breaker_policy = AdaptiveCircuitBreakerPolicy(
    base_threshold=5,           # Minimum failures before opening
    max_threshold=20,           # Maximum failures (when healthy)
    error_rate_threshold=0.5,   # 50% error rate triggers adjustment
    window_size=100             # Consider last 100 requests
)

# Threshold adapts:
# - Low error rate -> increases to max_threshold
# - High error rate -> decreases to base_threshold
# - Self-adjusting to service behavior
```

#### Disable Circuit Breaker

```python
from core.tools.executors.policies import NoOpCircuitBreakerPolicy

# For development/testing
spec.circuit_breaker_policy = NoOpCircuitBreakerPolicy()
# All requests pass through, no circuit breaking
```

### 2. Retry Policies

#### No Retry (Default)

```python
from core.tools.executors.policies import NoRetryPolicy

# Fail immediately on first error
spec.retry_policy = NoRetryPolicy()
```

#### Fixed Delay Retry

```python
from core.tools.executors.policies import FixedRetryPolicy

spec.retry_policy = FixedRetryPolicy(
    max_attempts=3,         # Total attempts (including first)
    delay_seconds=2.0,      # Wait 2 seconds between retries
    jitter=0.5              # ±0.5 seconds random jitter
)

# Timeline:
# Attempt 1: Immediate
# Fails -> Wait 2 seconds
# Attempt 2: Execute
# Fails -> Wait 2 seconds
# Attempt 3: Execute
# If fails -> Raise exception
```

#### Exponential Backoff

```python
from core.tools.executors.policies import ExponentialBackoffRetryPolicy

spec.retry_policy = ExponentialBackoffRetryPolicy(
    max_attempts=5,
    base_delay=1.0,        # Start with 1 second
    max_delay=30.0,        # Cap at 30 seconds
    multiplier=2.0,        # Double each time
    jitter=0.1             # 10% jitter
)

# Timeline:
# Attempt 1: Immediate
# Fails -> Wait 1 second
# Attempt 2: Execute
# Fails -> Wait 2 seconds
# Attempt 3: Execute
# Fails -> Wait 4 seconds
# Attempt 4: Execute
# Fails -> Wait 8 seconds
# Attempt 5: Execute
```

#### Custom Retry Logic

```python
from core.tools.executors.policies import CustomRetryPolicy

async def my_retry_logic(func, attempt, last_exception):
    """Custom retry with rate limit awareness"""
    if attempt >= 5:
        raise last_exception
    
    # Special handling for rate limits
    if isinstance(last_exception, RateLimitError):
        retry_after = last_exception.retry_after or 60
        await asyncio.sleep(retry_after)
    else:
        # Exponential backoff for other errors
        await asyncio.sleep(2 ** attempt)
    
    return await func()

spec.retry_policy = CustomRetryPolicy(my_retry_logic)
```

---

## Complete Example

### Payment Processing with Full Resilience

```python
from core.tools.executors.policies import (
    StandardCircuitBreakerPolicy,
    ExponentialBackoffRetryPolicy
)
from core.tools.executors.idempotency import FieldBasedIdempotencyKeyGenerator
from core.tools.spec.tool_types import FunctionToolSpec
from core.tools.spec.tool_parameters import StringParameter, NumericParameter

# Define payment function
async def process_payment(args):
    transaction_id = args['transaction_id']
    amount = args['amount']
    
    # Call payment gateway
    result = await payment_gateway.charge(transaction_id, amount)
    
    return {
        'transaction_id': transaction_id,
        'status': 'success',
        'confirmation': result['confirmation_code']
    }

# Create tool spec with ALL policies
spec = FunctionToolSpec(
    id="payment-processor-v1",
    tool_name="process_payment",
    description="Process payment with full resilience",
    tool_type=ToolType.FUNCTION,
    parameters=[
        StringParameter(name="transaction_id", required=True),
        NumericParameter(name="amount", required=True),
        StringParameter(name="currency", required=True)
    ],
    timeout_s=30
)

# 1. Idempotency - prevent duplicate charges
spec.idempotency.enabled = True
spec.idempotency.persist_result = True
spec.idempotency.ttl_s = 86400  # 24 hours
spec.idempotency.key_fields = ['transaction_id']
spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()

# 2. Circuit Breaker - prevent cascading failures
spec.circuit_breaker_policy = StandardCircuitBreakerPolicy(
    failure_threshold=5,
    recovery_timeout=60  # 1 minute before retry
)

# 3. Retry - handle transient failures
spec.retry_policy = ExponentialBackoffRetryPolicy(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0
)

# Create executor
from core.tools.executors import FunctionToolExecutor
executor = FunctionToolExecutor(spec, process_payment)

# Execute with full resilience
result = await executor.execute({
    'transaction_id': 'tx-12345',
    'amount': 99.99,
    'currency': 'USD'
}, ctx)

# What happens:
# 1. Check idempotency cache (tx-12345 already processed?)
# 2. If not cached, check circuit breaker (is payment gateway healthy?)
# 3. Execute with retry policy (handle transient failures)
# 4. Cache result for 24 hours
```

---

## Combining Policies

### Use Case: External API with Rate Limits

```python
# API that rate limits and occasionally times out
spec = FunctionToolSpec(...)

# Circuit breaker for API health
spec.circuit_breaker_policy = AdaptiveCircuitBreakerPolicy(
    base_threshold=10,      # More tolerant for external API
    max_threshold=50,
    error_rate_threshold=0.3  # 30% error rate
)

# Exponential backoff for rate limits
spec.retry_policy = ExponentialBackoffRetryPolicy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0  # Wait up to 1 minute
)

# Result: 
# - Retries with backoff for transient failures
# - Circuit opens if API consistently failing
# - Self-adapts to API health patterns
```

### Use Case: Database Operations

```python
# Database with connection pooling
spec = DbToolSpec(...)

# Circuit breaker for connection pool
spec.circuit_breaker_policy = StandardCircuitBreakerPolicy(
    failure_threshold=3,    # Fail fast for DB
    recovery_timeout=15     # Quick recovery check
)

# Fixed retry for connection issues
spec.retry_policy = FixedRetryPolicy(
    max_attempts=2,         # One retry only
    delay_seconds=0.5       # Quick retry
)

# Idempotency for duplicate prevention
spec.idempotency.enabled = True
spec.idempotency.key_fields = ['order_id']
```

---

## Factory Pattern

### Using Factories

```python
from core.tools.executors.policies import (
    CircuitBreakerPolicyFactory,
    RetryPolicyFactory
)

# Get built-in policies by name
circuit_breaker = CircuitBreakerPolicyFactory.get_policy('standard')
retry = RetryPolicyFactory.get_policy('exponential')

spec.circuit_breaker_policy = circuit_breaker
spec.retry_policy = retry
```

### Register Custom Policies

```python
from core.tools.executors.policies import (
    ICircuitBreakerPolicy,
    CircuitBreakerPolicyFactory
)

class TenantAwareCircuitBreaker(ICircuitBreakerPolicy):
    """Circuit breaker that tracks state per tenant"""
    
    async def execute_with_breaker(self, func, tool_name):
        tenant_id = get_current_tenant()
        key = f"{tool_name}:{tenant_id}"
        # Your logic
        pass
    
    def get_state(self, tool_name):
        return 'closed'
    
    def reset(self, tool_name):
        pass

# Register it
CircuitBreakerPolicyFactory.register(
    'tenant_aware',
    TenantAwareCircuitBreaker()
)

# Use it
policy = CircuitBreakerPolicyFactory.get_policy('tenant_aware')
spec.circuit_breaker_policy = policy
```

---

## Benefits

### 1. **Flexibility** ✅
Configure policies per tool based on requirements

### 2. **Separation of Concerns** ✅
Resilience logic separated from business logic

### 3. **Reusability** ✅
Create once, use across multiple tools via factory

### 4. **Testability** ✅
Easy to test policies in isolation

### 5. **Backward Compatibility** ✅
Existing tools continue to work (policies default to None)

### 6. **Extensibility** ✅
Easy to add new policies without modifying core code

---

## Comparison Matrix

| Policy Type | Use When | Best For |
|-------------|----------|----------|
| **StandardCircuitBreaker** | Fixed failure tolerance | Stable services |
| **AdaptiveCircuitBreaker** | Variable service health | External APIs |
| **NoOpCircuitBreaker** | Development/testing | Local testing |
| **NoRetry** | Non-retryable operations | Validation errors |
| **FixedRetry** | Predictable delays | Network blips |
| **ExponentialBackoff** | Rate limits/overload | APIs, databases |
| **CustomRetry** | Complex business rules | Special requirements |

---

## Policy Interactions

### Execution Flow with All Policies

```
1. Idempotency Check
   └─> Cache hit? Return cached result
   
2. Circuit Breaker Check
   └─> Circuit open? Fail immediately
   
3. Retry Policy Execution
   ├─> Attempt 1
   ├─> Fail? Wait and retry (if policy allows)
   ├─> Attempt 2
   ├─> Fail? Wait and retry
   └─> Attempt 3
       └─> Success? Record with circuit breaker
       └─> Fail? Update circuit breaker state
       
4. Cache Result (if idempotency enabled)
```

---

## Best Practices

### 1. **Choose Appropriate Policies**
```python
# Payment processing
circuit_breaker_policy=StandardCircuitBreakerPolicy()  # Strict
retry_policy=ExponentialBackoffRetryPolicy()          # Persistent

# Read-only queries
circuit_breaker_policy=AdaptiveCircuitBreakerPolicy()  # Flexible
retry_policy=FixedRetryPolicy(max_attempts=2)         # Quick retry
```

### 2. **Configure Reasonable Timeouts**
```python
# Don't retry forever
retry_policy=ExponentialBackoffRetryPolicy(
    max_attempts=5,     # Reasonable limit
    max_delay=30.0      # Cap delays
)
```

### 3. **Match Policies to Service Characteristics**
```python
# Fast, reliable service
failure_threshold=10    # More tolerant
max_attempts=2          # Few retries

# Slow, flaky service
failure_threshold=20    # Very tolerant
max_attempts=5          # More retries
```

### 4. **Test Your Policies**
```python
# Simulate failures to verify policies work
async def failing_function(args):
    if random.random() < 0.7:  # 70% failure rate
        raise TimeoutError("Simulated timeout")
    return {"status": "success"}

# Verify circuit breaker opens
# Verify retries happen with correct delays
```

---

## Migration from Config-Based

### Old Way (Config Objects)

```python
spec.retry = RetryConfig(
    max_attempts=3,
    base_delay_s=1.0,
    max_delay_s=10.0
)
spec.circuit_breaker = CircuitBreakerConfig(
    enabled=True,
    failure_threshold=5,
    recovery_timeout_s=30
)
```

### New Way (Pluggable Policies)

```python
spec.retry_policy = ExponentialBackoffRetryPolicy(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0
)
spec.circuit_breaker_policy = StandardCircuitBreakerPolicy(
    failure_threshold=5,
    recovery_timeout=30
)
```

### Both Work!

The old config objects are still supported. The pluggable policies provide additional flexibility for advanced use cases.

---

## Summary

✅ **Pluggable** - Configure at tool build time  
✅ **Flexible** - Multiple strategies available  
✅ **Extensible** - Easy to add custom policies  
✅ **Backward Compatible** - Works with existing code  
✅ **Well Designed** - Follows strategy pattern  
✅ **Production Ready** - Based on proven libraries (pybreaker)

The policy system provides enterprise-grade resilience patterns that can be easily configured and customized for each tool's specific requirements!

