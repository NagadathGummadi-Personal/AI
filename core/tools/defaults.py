"""
Centralized default values for the tools package.

These constants are used across spec models and implementations to
avoid scattering literal defaults and to make production tuning easier.
"""

from .enum import ToolReturnTarget, ToolReturnType

# ToolSpec defaults
DEFAULT_TOOL_VERSION = "1.0.0"
DEFAULT_TOOL_TIMEOUT_S = 30
DEFAULT_RETURN_TYPE = ToolReturnType.JSON
DEFAULT_RETURN_TARGET = ToolReturnTarget.STEP

# Retry defaults
RETRY_DEFAULT_MAX_ATTEMPTS = 3
RETRY_DEFAULT_BASE_DELAY_S = 0.2
RETRY_DEFAULT_MAX_DELAY_S = 2.0
RETRY_DEFAULT_JITTER_S = 0.1

# Circuit breaker defaults
CB_DEFAULT_ENABLED = True
CB_DEFAULT_FAILURE_THRESHOLD = 5
CB_DEFAULT_RECOVERY_TIMEOUT_S = 30
CB_DEFAULT_HALF_OPEN_MAX_CALLS = 1
CB_DEFAULT_ERROR_CODES_TO_TRIP = ["TIMEOUT", "UNAVAILABLE", "TOOL_ERROR"]

# Idempotency defaults
IDEMPOTENCY_DEFAULT_ENABLED = True
IDEMPOTENCY_DEFAULT_TTL_S = 3600
IDEMPOTENCY_DEFAULT_PERSIST_RESULT = True
IDEMPOTENCY_DEFAULT_BYPASS_ON_MISSING_KEY = False

# HTTP/DB defaults
HTTP_DEFAULT_METHOD = "POST"
DB_DEFAULT_DRIVER = "postgresql"


