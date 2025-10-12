# AI Project - Technical Documentation

## Overview
This is a comprehensive Python project that implements an AI tools specification system with advanced logging capabilities. The project is designed with modular architecture, supporting multiple tool types, environments, and comprehensive logging features.

## Project Structure

### Root Level Files
- **`README.md`** - Minimal project description
- **`pyproject.toml`** - Main project configuration with dependencies and tool configurations
- **`uv.lock`** - Lock file for dependency management using `uv`
- **`run_checks.bat`** - Windows batch script for running quality checks
- **`run_tests.py`** - Test runner script

### Core Modules

#### `core/tools/` - Tool Execution System
This is the main business logic module providing a comprehensive tool execution framework.

**Key Files:**
- **`__init__.py`** - Module exports and system overview
- **`enum.py`** - Core enumerations for tool types, return formats, and parameter types
- **`constants.py`** - Centralized constants for error codes, logging formats, and system values
- **`defaults.py`** - Default configuration values and helper functions

**Subdirectories:**
- **`spec/`** - Data model specifications
- **`interfaces/`** - Protocol interfaces for pluggable components
- **`executors/`** - Implementation classes for tool execution

**Core Components:**

1. **Tool Types** (`enum.py`):
   ```python
   class ToolType(str, Enum):
       FUNCTION = 'function'  # Function-based tools
       HTTP = 'http'         # HTTP API tools
       DB = 'db'             # Database tools

   class ToolReturnType(str, Enum):
       JSON = 'json'         # JSON response format
       TEXT = 'text'         # Plain text response

   class ToolReturnTarget(str, Enum):
       HUMAN = 'human'       # Results sent to human
       LLM = 'llm'          # Results sent to LLM
       AGENT = 'agent'       # Results sent to agent
       STEP = 'step'         # Part of workflow step
   ```

2. **Tool Specifications** (`spec/`):
   - **`tool_types.py`** - Base `ToolSpec` and specialized tool specifications
   - **`tool_parameters.py`** - Parameter definitions with validation
   - **`tool_context.py`** - Execution context with tracing and auth
   - **`tool_result.py`** - Standardized result format
   - **`tool_config.py`** - Configuration for retries, circuit breakers, and idempotency

3. **Interfaces** (`interfaces/`):
   - Protocol definitions for pluggable components
   - Support for validators, security, policies, metrics, tracing, and rate limiting

4. **Executors** (`executors/`):
   - **`executors.py`** - Base executor classes and specific implementations
   - **`usage_calculators/`** - Cost, token, and usage calculation utilities

**Key Features:**
- **SOLID Architecture** - Modular, extensible design
- **Async Support** - Asynchronous execution patterns
- **Circuit Breaker** - Fault tolerance with circuit breaker pattern
- **Idempotency** - Duplicate request handling
- **Tracing** - Distributed tracing support
- **Metrics** - Usage and performance metrics
- **Rate Limiting** - Request rate limiting
- **Security** - Authorization and egress checking

#### `utils/` - Utility Functions and Logging
Comprehensive logging and utility system.

**Key Files:**
- **`main.py`** - Simple test utility
- **`README.md`** - Package documentation

**Subdirectories:**
- **`logging/`** - Complete logging framework
- **`circuitBreaker/`** - Circuit breaker implementation

**Logging System Features:**
1. **LoggerAdaptor** - Unified logging interface
2. **Multiple Backends** - Standard, JSON, and detailed logging formats
3. **Environment Support** - Development, staging, production, testing configs
4. **Redaction** - Sensitive data redaction with regex patterns
5. **Context Management** - Structured logging with persistent context
6. **Duration Logging** - Performance timing and logging
7. **Delayed Logging** - Asynchronous logging for high-throughput scenarios

**Configuration Management:**
- JSON-based configuration files per environment
- Automatic environment detection
- Runtime configuration reloading

**Redaction Capabilities:**
- Credit card numbers, SSNs, emails, phone numbers
- Custom regex patterns with configurable placeholders
- Support for multiple redaction strategies

#### `tests/` - Test Suite
Comprehensive test coverage with pytest.

**Test Structure:**
- **`logging/`** - Tests for logging framework
- **`circuitBreaker/`** - Tests for circuit breaker functionality

**Test Categories:**
- Unit tests for individual components
- Integration tests across modules
- Parametrized tests for multiple scenarios
- Mock-based testing for external dependencies

**Test Markers:**
- `logger` - Logging-related tests
- `duration` - Duration logging tests
- `delayed` - Asynchronous logging tests
- `config` - Configuration management tests

### Configuration Files

#### Environment-Specific Logging Configurations
- **`log_config_dev.json`** - Development logging configuration
- **`log_config_staging.json`** - Staging environment configuration
- **`log_config_prod.json`** - Production logging configuration
- **`log_config_test.json`** - Testing environment configuration

**Configuration Structure:**
```json
{
  "backend": "json|standard|detailed",
  "level": "INFO|DEBUG|WARNING|ERROR",
  "formatters": {
    "default": {
      "format": "...",
      "datefmt": "..."
    }
  },
  "handlers": {
    "console": {...},
    "file": {...}
  },
  "redaction": {
    "enabled": true,
    "patterns": [...]
  },
  "duration_logging": {
    "slow_threshold_seconds": 1.0,
    "warn_threshold_seconds": 5.0,
    "error_threshold_seconds": 30.0
  }
}
```

## Technical Implementation Details

### Tool Execution System Architecture

#### Core Data Models

1. **ToolSpec** - Base tool specification:
   ```python
   class ToolSpec(BaseModel):
       id: str                          # Unique tool identifier
       version: str = "1.0.0"           # Tool version
       tool_name: str                   # Human-readable name
       description: str                 # Tool description
       tool_type: ToolType             # FUNCTION, HTTP, or DB
       parameters: List[ToolParameter]  # Input parameter definitions
       return_type: ToolReturnType     # JSON or TEXT
       return_target: ToolReturnTarget # HUMAN, LLM, AGENT, or STEP
       required: bool = False          # Whether tool is required
       owner: Optional[str] = None     # Tool owner
       permissions: List[str] = []     # Required permissions
       timeout_s: int = 30             # Execution timeout
       examples: List[Dict] = []       # Usage examples
       retry: RetryConfig              # Retry configuration
       circuit_breaker: CircuitBreakerConfig  # Circuit breaker settings
       idempotency: IdempotencyConfig  # Idempotency configuration
   ```

2. **ToolContext** - Execution context:
   ```python
   class ToolContext(BaseModel):
       tenant_id: Optional[str] = None   # Multi-tenant support
       user_id: Optional[str] = None     # User identification
       session_id: Optional[str] = None  # Session tracking
       trace_id: Optional[str] = None    # Distributed tracing
       span_id: Optional[str] = None     # Current span
       parent_span_id: Optional[str] = None  # Parent span
       locale: Optional[str] = None      # Localization
       timezone: Optional[str] = None    # Timezone handling
       deadline_ts: Optional[float] = None  # Execution deadline
       auth: Dict[str, Any] = {}         # Authentication data
       extras: Dict[str, Any] = {}       # Additional context
       run_id: Optional[str] = None      # Execution run ID
       idempotency_key: Optional[str] = None  # Idempotency key
       # Injected dependencies
       memory: Optional[IToolMemory] = None
       metrics: Optional[IToolMetrics] = None
       tracer: Optional[IToolTracer] = None
       limiter: Optional[IToolLimiter] = None
       validator: Optional[IToolValidator] = None
       security: Optional[IToolSecurity] = None
   ```

3. **ToolResult** - Standardized result format:
   ```python
   class ToolResult(BaseModel):
       return_type: ToolReturnType        # Response format
       return_target: ToolReturnTarget   # Result destination
       content: Any                      # Actual result data
       artifacts: Optional[Dict[str, bytes]] = None  # Binary artifacts
       usage: Optional[ToolUsage] = None # Usage statistics
       latency_ms: Optional[int] = None  # Execution latency
       warnings: List[str] = []          # Warning messages
       logs: List[str] = []              # Execution logs
   ```

#### Tool Execution Flow

1. **Validation** - Parameter validation using configured validators
2. **Authorization** - Security checks and permission validation
3. **Idempotency** - Check for cached results if enabled
4. **Execution** - Execute tool with optional rate limiting and tracing
5. **Metrics** - Record execution metrics and usage statistics
6. **Caching** - Store result for future idempotent requests

#### Circuit Breaker Implementation

The system implements a circuit breaker pattern to prevent cascading failures:

- **States**: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- **Failure Threshold** - Configurable consecutive failure count
- **Recovery Timeout** - Time before attempting recovery
- **Error Code Filtering** - Specific errors that trigger circuit opening

#### Idempotency System

Ensures identical requests return the same result:

- **Key Generation** - SHA-256 hash of request parameters and context
- **TTL Support** - Configurable result expiration
- **Selective Caching** - Optional field-based key generation
- **Result Persistence** - Store results for reuse

### Logging System Architecture

#### LoggerAdaptor - Core Logging Component

**Backend Types:**
1. **Standard** - Traditional Python logging format
2. **JSON** - Structured JSON logging for log aggregation
3. **Detailed** - Verbose context-aware logging

**Key Methods:**
```python
class LoggerAdaptor:
    def __init__(self, name: str, environment: str = None, config: dict = None)
    def get_logger(cls, name: str, environment: str = None, config: dict = None) -> 'LoggerAdaptor'
    def debug(self, *args, **kwargs)
    def info(self, *args, **kwargs)
    def warning(self, *args, **kwargs)
    def error(self, *args, **kwargs)
    def critical(self, *args, **kwargs)
    def set_context(self, **kwargs)  # Persistent context
    def log_duration(self, operation_name: str, duration_seconds: float, **kwargs)
    def enable_redaction(self, enabled: bool = True)
    def add_redaction_pattern(self, pattern: str, placeholder: str = "[REDACTED]")
```

#### Configuration Management

**Environment Detection:**
```python
@staticmethod
def detect_environment() -> str:
    env = os.getenv('ENVIRONMENT', os.getenv('ENV', 'prod')).lower()
    return {
        'dev': 'development',
        'staging': 'staging',
        'prod': 'production',
        'test': 'testing'
    }.get(env, 'production')
```

**Configuration Loading:**
- Automatic environment-based config file loading
- JSON configuration validation
- Runtime configuration reloading
- Default configuration fallbacks

#### Redaction System

**Pattern-Based Redaction:**
```python
class RedactionManager:
    def __init__(self, config: dict)
    def redact_message(self, message: str) -> str
    def redact_data(self, data: Any) -> Any  # Recursive redaction
```

**Built-in Patterns:**
- Credit card numbers: `\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}`
- SSN: `\b\d{3}-?\d{2}-?\d{4}\b`
- Email: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- Phone: `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b`

#### Duration Logging

**Performance Monitoring:**
```python
@durationlogger
def expensive_operation():
    # Operation code here
    pass

# Or as context manager
with durationlogger.time_operation("database_query") as timer:
    result = query_database()
    timer.add_metadata(rows_affected=len(result))
```

**Threshold-Based Logging:**
- DEBUG: < 1 second (slow threshold)
- INFO: 1-5 seconds (warn threshold)
- WARNING: 5-30 seconds (error threshold)
- ERROR: > 30 seconds

#### Delayed Logging

**Asynchronous Logging:**
```python
class DelayedLogger:
    def __init__(self, logger: Any)
    def configure(self, config: Dict[str, Any])
    def info_delayed(self, *args, **kwargs)  # Queued logging
    def flush_delayed_logs(self)             # Force flush queue
```

**Queue Management:**
- Background thread processing
- Configurable queue size limits
- Automatic flushing on exceptions
- Lambda environment compatibility warnings

## Dependencies

### Main Dependencies (`pyproject.toml`):
```toml
dependencies = [
    "pybreaker>=1.4.0",        # Circuit breaker functionality
    "pydantic>=2.11.9",        # Data validation and serialization
    "typing-extensions>=4.15.0"  # Enhanced type hints
]
```

### Development Dependencies:
```toml
dev = [
    "pylint>=3.3.8",      # Code quality and style checking
    "pytest>=8.4.1",      # Testing framework
    "ruff>=0.12.8"        # Fast Python linter and formatter
]
```

## Quality Assurance

### Code Quality Tools

**Ruff** - Fast Python linter:
```bash
# Check all Python files
uv tool run ruff check

# Auto-fix issues
uv tool run ruff check --fix

# Check specific file
uv tool run ruff check main.py
```

**Pylint** - Comprehensive code analysis:
```bash
# Check all Python files
uv tool run pylint .

# Check specific file
uv tool run pylint main.py

# Generate detailed report
uv tool run pylint --reports=y main.py
```

### Testing

**Test Execution:**
```bash
# Run all tests
uv run pytest

# Run specific test markers
uv run pytest -m "logger"        # Logging tests
uv run pytest -m "duration"      # Duration logging tests
uv run pytest -m "integration"   # Integration tests

# Run with coverage
uv run pytest --cov=utils tests/
```

**Test Markers:**
- `slow` - Long-running tests
- `integration` - Cross-module integration tests
- `unit` - Individual component tests
- `logger` - Logging framework tests
- `duration` - Duration logging tests
- `delayed` - Asynchronous logging tests
- `config` - Configuration management tests

## Development Workflow

### Environment Setup
1. Install dependencies: `uv sync`
2. Set environment: `export ENVIRONMENT=dev`
3. Configure logging per environment needs

### Tool Development
1. Define tool specification (`ToolSpec`)
2. Implement executor (`IToolExecutor`)
3. Add parameter validation (`IToolValidator`)
4. Configure security policies (`IToolSecurity`)
5. Add comprehensive tests

### Logging Integration
1. Get logger: `logger = LoggerAdaptor.get_logger("service_name")`
2. Set context: `logger.set_context(service="my_service", version="1.0")`
3. Log with structure: `logger.info("Operation completed", user_id="123")`
4. Monitor performance: Use `@durationlogger` decorator

## Production Considerations

### Performance Optimizations
- **Delayed Logging** - For high-throughput scenarios
- **Circuit Breaker** - Prevent cascade failures
- **Idempotency** - Reduce redundant computations
- **Rate Limiting** - Prevent resource exhaustion

### Security Considerations
- **Data Redaction** - Automatic sensitive data masking
- **Authorization** - Role-based access control
- **Audit Logging** - Comprehensive activity tracking
- **Environment Isolation** - Separate configs per environment

### Monitoring and Observability
- **Structured Logging** - JSON format for log aggregation
- **Metrics Collection** - Usage and performance metrics
- **Distributed Tracing** - Request flow tracking
- **Health Checks** - Circuit breaker state monitoring

## Future Enhancements

### Potential Improvements
1. **Plugin System** - Dynamic tool loading
2. **GraphQL Support** - Additional tool types
3. **WebSocket Tools** - Real-time tool execution
4. **Advanced Caching** - Redis/Memcached integration
5. **Metrics Export** - Prometheus/OpenTelemetry integration
6. **Distributed Locks** - Multi-instance coordination

### Scalability Considerations
1. **Horizontal Scaling** - Stateless design for multi-instance deployment
2. **Load Balancing** - Rate limiting and circuit breaker support
3. **Data Partitioning** - Multi-tenant data isolation
4. **Caching Strategies** - Multi-level caching architecture

## Conclusion

This project provides a robust, enterprise-ready framework for AI tool execution with comprehensive logging capabilities. The modular architecture supports multiple tool types, environments, and deployment scenarios while maintaining high standards for security, observability, and reliability.

The system is designed for production use with features like circuit breakers, idempotency, rate limiting, and comprehensive logging that make it suitable for high-throughput, mission-critical applications.
