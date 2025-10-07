"""
Central constants for literals, error codes, event names, and logging formats.
"""

# Error/Status Codes
ERROR_TIMEOUT = "TIMEOUT"
ERROR_UNAVAILABLE = "UNAVAILABLE"
ERROR_TOOL = "TOOL_ERROR"
ERROR_MATH = "MATH_ERROR"
ERROR_UNAUTHORIZED = "UNAUTHORIZED"
ERROR_INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
ERROR_UNAUTHORIZED_ROLE = "UNAUTHORIZED_ROLE"
ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
ERROR_INVALID_OPERATION = "INVALID_OPERATION"

# Event/Metric Names
METRIC_TOOL_EXECUTION_STARTED = "tool.execution.started"
METRIC_TOOL_EXECUTION_SUCCESS = "tool.execution.success"
METRIC_TOOL_EXECUTION_FAILED = "tool.execution.failed"
METRIC_TOOL_EXECUTION_TIME = "tool.execution_time"
METRIC_ADDITION_SUCCESS = "addition.success"
METRIC_ADDITION_DURATION = "addition.duration"
METRIC_ADDITION_ERROR = "addition.error"

# Logging Messages (format strings)
LOG_STARTING_EXECUTION = "Starting tool execution"
LOG_PARAMETERS = "Tool parameters"
LOG_VALIDATING = "Validating parameters"
LOG_VALIDATION_PASSED = "Parameter validation passed"
LOG_VALIDATION_SKIPPED = "No validator available - skipping parameter validation"
LOG_AUTH_CHECK = "Checking authorization"
LOG_AUTH_PASSED = "Authorization passed"
LOG_AUTH_SKIPPED = "No security component available - skipping authorization"
LOG_EGRESS_CHECK = "Checking egress permissions"
LOG_EGRESS_PASSED = "Egress check passed"
LOG_EGRESS_SKIPPED = "No security component available - skipping egress check"
LOG_IDEMPOTENCY_CACHE_HIT = "Using cached result for idempotency"
LOG_EXECUTION_COMPLETED = "Tool execution completed"
LOG_EXECUTION_FAILED = "Tool execution failed"
LOG_HTTP_STARTING = "Starting HTTP tool execution"
LOG_HTTP_COMPLETED = "HTTP tool execution completed"
LOG_HTTP_FAILED = "HTTP tool execution failed"
LOG_DB_STARTING = "Starting database tool execution"
LOG_DB_COMPLETED = "Database tool execution completed"
LOG_DB_FAILED = "Database tool execution failed"

# Demo/Example event names
EVENT_EXECUTION_STARTED = "EXECUTION_STARTED"
EVENT_PARAMETER_EXTRACTION = "PARAMETER_EXTRACTION"
EVENT_TYPE_COERCION = "TYPE_COERCION"
EVENT_TYPE_COERCION_FAILED = "TYPE_COERCION_FAILED"
EVENT_SIMULATED_ERROR = "SIMULATED_ERROR"
EVENT_CALCULATION_STARTED = "CALCULATION_STARTED"
EVENT_CALCULATION_COMPLETED = "CALCULATION_COMPLETED"
EVENT_METRICS_RECORDED = "METRICS_RECORDED"
EVENT_TRACING_SPAN_CREATED = "TRACING_SPAN_CREATED"
EVENT_CACHE_OPERATION = "CACHE_OPERATION"
EVENT_EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
EVENT_EXECUTION_ERROR = "EXECUTION_ERROR"

# Other constants
PARAMETER_TYPE_STRING = "string"
PARAMETER_TYPE_NUMBER = "number"
PARAMETER_TYPE_INTEGER = "integer"
PARAMETER_TYPE_BOOLEAN = "boolean"
PARAMETER_TYPE_BOOLEAN_TRUE = "true"
PARAMETER_TYPE_BOOLEAN_YES = "yes"
PARAMETER_TYPE_BOOLEAN_ON = "on"
PARAMETER_TYPE_BOOLEAN_1 = "1"
PARAMETER_TYPE_BOOLEAN_FALSE = "false"
PARAMETER_TYPE_BOOLEAN_NO = "no"
PARAMETER_TYPE_BOOLEAN_OFF = "off"
PARAMETER_TYPE_BOOLEAN_0 = "0"
PARAMETER_TYPE_ARRAY = "array"
PARAMETER_TYPE_OBJECT = "object"


# Derived collections
BOOLEAN_TRUE_STRINGS = (
    PARAMETER_TYPE_BOOLEAN_TRUE,
    PARAMETER_TYPE_BOOLEAN_1,
    PARAMETER_TYPE_BOOLEAN_YES,
    PARAMETER_TYPE_BOOLEAN_ON,
)
BOOLEAN_FALSE_STRINGS = (
    PARAMETER_TYPE_BOOLEAN_FALSE,
    PARAMETER_TYPE_BOOLEAN_0,
    PARAMETER_TYPE_BOOLEAN_NO,
    PARAMETER_TYPE_BOOLEAN_OFF,
)

# Python type mapping for parameter types
PARAMETER_PY_TYPES = {
    PARAMETER_TYPE_STRING: str,
    PARAMETER_TYPE_NUMBER: (int, float),
    PARAMETER_TYPE_INTEGER: int,
    PARAMETER_TYPE_BOOLEAN: bool,
    PARAMETER_TYPE_ARRAY: (list, tuple),
    PARAMETER_TYPE_OBJECT: dict,
}

# Error message format strings
MSG_UNKNOWN_PARAMETERS = "Unknown parameter(s): {params}"
MSG_MISSING_REQUIRED_PARAMETER = "Missing required parameter: {name}"
MSG_PARAMETER_FAILED_VALIDATION = "Parameter '{name}' failed validation"
MSG_UNAUTHORIZED_USER = "User {user_id} is not authorized to execute tool {tool_name}"
MSG_MISSING_REQUIRED_PERMISSIONS = "User {user_id} missing required permissions: {missing_perms}"
MSG_UNAUTHORIZED_ROLE = "User role {user_role} is not authorized to execute tool {tool_name}"
MSG_DIVISION_BY_ZERO = "Division by zero"
MSG_UNKNOWN_OPERATION = "Unknown operation: {operation}"

#HTTP Execution Status
HTTP_EXECUTION_STATUS_COMPLETED = "HTTP {self.spec.method} to {self.spec.url} completed"
HTTP_EXECUTION_STATUS_FAILED = "HTTP {self.spec.method} to {self.spec.url} failed"
DB_EXECUTION_STATUS_COMPLETED = "Database execution completed"
DB_EXECUTION_STATUS_FAILED = "Database execution failed"
TOOL_EXECUTION_STATUS_COMPLETED = "Tool execution completed"
TOOL_EXECUTION_STATUS_FAILED = "Tool execution failed"