# Tools Specification System (v1.2.0)

A modular, asynchronous tool execution system designed for production-grade orchestration with SOLID separation, strict validation, security, idempotency, tracing, metrics, and circuit breaker-aware retries.

## Overview

This specification defines a comprehensive system for creating, validating, and executing tools in a robust and extensible manner. The system is designed to support:

- **Multiple Tool Types**: Function, HTTP, and Database tools
- **Rich Parameter Validation**: Schema-driven validation with optional coercion
- **Robust Error Handling**: Structured error reporting with retry information
- **Idempotency**: Built-in support for caching and replay protection
- **Observability**: Comprehensive tracing, metrics, and logging
- **Security**: Authorization and egress controls
- **Resilience**: Circuit breaker pattern and configurable retry policies

## Key Features

### 🔧 Tool Types
- **Function**: Python functions with async support
- **HTTP**: REST API endpoints with configurable methods and headers
- **Database**: SQL queries with connection management

### 📝 Parameter Schema
Rich parameter definitions with:
- Type validation (string, number, integer, boolean, array, object)
- Constraints (min/max values, length limits, regex patterns)
- Optional coercion between compatible types
- Enum values and default parameters
- Format validation (email, URI, date-time, etc.)

### 🔄 Execution Control
- **Retry Policies**: Configurable attempts, delays, and jitter
- **Circuit Breaker**: Automatic failure detection and recovery
- **Idempotency**: Key-based caching and result reuse
- **Timeouts**: Per-tool execution time limits

### 📊 Observability
- **Tracing**: Distributed tracing with span context
- **Metrics**: Usage statistics, performance timing, and custom tags
- **Events**: Structured event emission for monitoring
- **Logging**: Detailed execution logs and warnings

### 🔒 Security
- **Authorization**: Role-based access control
- **Egress Checks**: Network and resource access validation
- **Audit Trails**: Comprehensive execution history

## Architecture

The system follows SOLID principles with narrow, focused interfaces:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ToolSpec      │    │  ToolContext     │    │  ToolResult     │
│                 │    │                  │    │                 │
│ - Metadata      │    │ - Tracing        │    │ - Content       │
│ - Parameters    │    │ - Dependencies   │    │ - Usage Stats   │
│ - Configuration │    │ - Auth Context   │    │ - Artifacts     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └──────────┬────────────┼─────────────┬─────────┘
                    │            │             │
         ┌──────────▼────────────▼─────────────▼─────────┐
         │              ToolExecutor                     │
         │                                               │
         │ - BaseToolExecutor                            │
         │ - FunctionToolExecutor                        │
         │ - HttpToolExecutor                            │
         │ - DbToolExecutor                              │
         └───────────────────────────────────────────────┘
                    │
         ┌──────────▼────────────┐
         │   Pluggable Components   │
         │                          │
         │ - IToolValidator         │
         │ - IToolSecurity          │
         │ - IToolPolicy            │
         │ - IToolMemory            │
         │ - IToolMetrics           │
         │ - IToolTracer            │
         │ - IToolLimiter           │
         └──────────────────────────┘
```

## Quick Start

### 1. Define a Tool

```python
from core.tools import (
    ToolSpec, ToolParameter, ToolType, ToolReturnType, ToolReturnTarget
)

# Create a calculator tool specification
def create_calculator_tool() -> ToolSpec:
    parameters = [
        ToolParameter(
            name="operation",
            type="string",
            description="Mathematical operation",
            required=True,
            enum=["add", "subtract", "multiply", "divide"]
        ),
        ToolParameter(
            name="a",
            type="number",
            description="First number",
            required=True
        ),
        ToolParameter(
            name="b",
            type="number",
            description="Second number",
            required=True
        )
    ]

    return ToolSpec(
        id="calculator-v1",
        version="1.0.0",
        tool_name="calculator",
        description="Performs basic mathematical operations",
        tool_type=ToolType.FUNCTION,
        parameters=parameters,
        return_type=ToolReturnType.JSON,
        return_target=ToolReturnTarget.STEP
    )
```

### 2. Implement the Tool

```python
from core.tools import FunctionToolExecutor, ToolContext

class CalculatorImpl:
    async def calculate(self, args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
        operation = args["operation"]
        a = args["a"]
        b = args["b"]

        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                from core.tools import ToolError
                raise ToolError("Division by zero", retryable=False)
            result = a / b

        return {"result": result}

# Create executor
spec = create_calculator_tool()
impl = CalculatorImpl()
executor = FunctionToolExecutor(spec, impl.calculate)
```

### 3. Execute the Tool

```python
from core.tools import ToolContext

# Create execution context
ctx = ToolContext(
    user_id="user123",
    session_id="session456"
)

# Execute the tool
result = await executor.execute({
    "operation": "add",
    "a": 10,
    "b": 5
}, ctx)

print(result.content)  # {"result": 15}
```

## Configuration

### Retry Configuration

```python
from core.tools import RetryConfig

retry_config = RetryConfig(
    max_attempts=5,
    base_delay_s=0.5,
    max_delay_s=10.0,
    jitter_s=0.2
)
```

### Circuit Breaker Configuration

```python
from core.tools import CircuitBreakerConfig

circuit_config = CircuitBreakerConfig(
    enabled=True,
    failure_threshold=5,
    recovery_timeout_s=30,
    half_open_max_calls=3,
    error_codes_to_trip=["TIMEOUT", "CONNECTION_ERROR"]
)
```

### Idempotency Configuration

```python
from core.tools import IdempotencyConfig

idempotency_config = IdempotencyConfig(
    enabled=True,
    key_fields=["user_id", "operation"],  # Use specific fields for key
    ttl_s=3600,                          # Cache for 1 hour
    persist_result=True,                 # Store results
    bypass_on_missing_key=False          # Require all key fields
)
```

## Advanced Usage

### Custom Validators

```python
from core.tools import IToolValidator, ToolSpec

class CustomValidator:
    async def validate(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        # Custom validation logic
        if spec.tool_name == "sensitive_operation":
            if not args.get("authorization"):
                raise ToolError("Authorization required")
```

### Custom Metrics

```python
from core.tools import IToolMetrics

class CustomMetrics:
    async def incr(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        # Send to your metrics system
        pass

    async def observe(self, name: str, value: float, tags: Dict[str, str] = None):
        # Record observations
        pass

    async def timing_ms(self, name: str, value_ms: int, tags: Dict[str, str] = None):
        # Record timing data
        pass
```

### Memory Integration

```python
from core.tools import IToolMemory
from contextlib import asynccontextmanager

class RedisMemory:
    async def get(self, key: str):
        # Get from Redis
        pass

    async def set(self, key: str, value: Any, ttl_s: int = None):
        # Set in Redis
        pass

    async def delete(self, key: str):
        # Delete from Redis
        pass

    @asynccontextmanager
    async def lock(self, key: str, ttl_s: int = 10):
        # Acquire distributed lock
        yield
```

## Examples

See `examples.py` for comprehensive examples including:

- Calculator tool implementation
- Weather API tool
- Database query tool
- Tool registry and execution patterns
- Error handling and retry scenarios

## Extensibility

The system is designed for easy extension:

1. **New Tool Types**: Implement `IToolExecutor` for custom tool types
2. **Custom Validation**: Implement `IToolValidator` for domain-specific rules
3. **Security Policies**: Implement `IToolSecurity` for custom authorization
4. **Storage Backends**: Implement `IToolMemory` for different caching systems
5. **Metrics Systems**: Implement `IToolMetrics` for custom monitoring
6. **Tracing Systems**: Implement `IToolTracer` for distributed tracing

## Version History

### v1.2.0 (Current)
- Added CircuitBreaker configuration
- Enhanced parameter validation with coercion
- Improved observability with structured events
- Added memory interface for caching and idempotency
- Enhanced security with egress checks

### v1.1.0
- Added tracing and metrics interfaces
- Improved error handling and retry logic
- Enhanced parameter schema validation

### v1.0.0
- Initial release with core tool specification
- Basic validation and execution framework
- Function, HTTP, and Database tool types

## Contributing

To extend the system:

1. Follow the existing patterns and interfaces
2. Maintain backward compatibility when possible
3. Add comprehensive tests for new components
4. Update documentation and examples
5. Use semantic versioning for changes

## License

This tools specification system is designed to be integrated into larger applications and SDKs. The interfaces and patterns can be freely adapted for your specific use cases.
