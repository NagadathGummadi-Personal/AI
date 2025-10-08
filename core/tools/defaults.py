"""
Centralized default values for the tools package.

These constants are used across spec models and implementations to
avoid scattering literal defaults and to make production tuning easier.
"""

from .enum import ToolReturnTarget, ToolReturnType
from .constants import (
    HTTP_EXECUTION_STATUS_COMPLETED,
    HTTP_EXECUTION_STATUS_FAILED,
    DB_EXECUTION_STATUS_FAILED,
    EXC_CALCULATION_NOT_IMPLEMENTED,
    DEFAULT_VERSION_STRING,
    DEFAULT_ENVIRONMENT_STRING,
    DB_DEFAULT_QUERY_STRING,
    USER_ID,
    SESSION_ID,
    TOOL_NAME,
    TRACE_ID,
    HTTP_METHOD,
    HTTP_URL,
    DB_HOST,
    DB_PORT,
    DB_DATABASE,
    STATUS_CODE,
    RESPONSE,
    ARGS,
    METHOD,
    URL,
    ROWS_AFFECTED,
    QUERY,
    CONNECTION,
    HOST,
    PORT,
    DATABASE,
    TOKENS_IN,
    TOKENS_OUT,
    COST_USD,
    ATTEMPTS,
    RETRIES,
    CACHED_HIT,
    IDEMPOTENCY_REUSED,
    CIRCUIT_OPENED,
    TIMEOUT,
    UNAVAILABLE,
    TOOL_ERROR,
    POST,
    POSTGRESQL,
)
from .config import is_dev

# ToolSpec defaults
DEFAULT_TOOL_VERSION = DEFAULT_VERSION_STRING
DEFAULT_TOOL_TIMEOUT_S = 30
DEFAULT_RETURN_TYPE = ToolReturnType.JSON
DEFAULT_RETURN_TARGET = ToolReturnTarget.STEP

# Environment defaults
DEFAULT_ENVIRONMENT = DEFAULT_ENVIRONMENT_STRING

# Dev-only mock response defaults
HTTP_DEFAULT_STATUS_CODE = 200
DB_DEFAULT_ROWS_AFFECTED = 1
DB_DEFAULT_QUERY = DB_DEFAULT_QUERY_STRING


# -------- Context data builders --------
def DEFAULT_TOOL_CONTEXT_DATA(spec, ctx):
    """Standard context dict for tool executions."""
    return {
        USER_ID: ctx.user_id,
        SESSION_ID: ctx.session_id,
        TOOL_NAME: spec.tool_name,
        TRACE_ID: ctx.trace_id,
    }


def DEFAULT_HTTP_CONTEXT_DATA(spec, ctx):
    data = DEFAULT_TOOL_CONTEXT_DATA(spec, ctx)
    data.update({
        HTTP_METHOD: getattr(spec, METHOD, None),
        HTTP_URL: getattr(spec, URL, None),
    })
    return data


def DEFAULT_DB_CONTEXT_DATA(spec, ctx):
    data = DEFAULT_TOOL_CONTEXT_DATA(spec, ctx)
    data.update({
        DB_HOST: getattr(spec, HOST, None),
        DB_PORT: getattr(spec, PORT, None),
        DB_DATABASE: getattr(spec, DATABASE, None),
    })
    return data


# -------- Dev-only mock result builders --------
def HTTP_DEFAULT_SUCCESS_STATUS_RESPONSE(spec, args):
    return {
        STATUS_CODE: HTTP_DEFAULT_STATUS_CODE,
        RESPONSE: HTTP_EXECUTION_STATUS_COMPLETED.format(
            tool_name=spec.tool_name, method=spec.method, url=spec.url
        ),
        ARGS: args,
    }


def HTTP_DEFAULT_ERROR_STATUS_WARNING(spec, error: str) -> str:
    return HTTP_EXECUTION_STATUS_FAILED.format(
        tool_name=spec.tool_name, method=spec.method, url=spec.url, error=error
    )


def DB_DEFAULT_SUCCESS_RESULT_CONTENT(spec, args):
    return {
        ROWS_AFFECTED: DB_DEFAULT_ROWS_AFFECTED,
        QUERY: args.get(QUERY, DB_DEFAULT_QUERY),
        CONNECTION: {
            HOST : spec.host,
            PORT: spec.port,
            DATABASE: spec.database,
        },
    }


def DB_DEFAULT_ERROR_STATUS_WARNING(spec, error: str) -> str:
    return DB_EXECUTION_STATUS_FAILED.format(tool_name=spec.tool_name, error=error)


# -------- Usage calculation helpers --------
def calculate_tokens_in_dev() -> int:
    return 0


def calculate_tokens_out_dev() -> int:
    return 0


def calculate_cost_usd_dev() -> float:
    return 0.0


def calculate_attempts_dev() -> int:
    return 1


def calculate_retries_dev() -> int:
    return 0


def check_cached_hit_dev() -> bool:
    return False


def check_idempotency_reused_dev() -> bool:
    return False


def check_circuit_opened_dev() -> bool:
    return False


# -------- Env-aware wrappers (dev vs non-dev) --------
def calculate_tokens_in() -> int:
    if is_dev():
        return calculate_tokens_in_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=TOKENS_IN))


def calculate_tokens_out() -> int:
    if is_dev():
        return calculate_tokens_out_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=TOKENS_OUT))


def calculate_cost_usd() -> float:
    if is_dev():
        return calculate_cost_usd_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=COST_USD))


def calculate_attempts() -> int:
    if is_dev():
        return calculate_attempts_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=ATTEMPTS))


def calculate_retries() -> int:
    if is_dev():
        return calculate_retries_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=RETRIES))


def check_cached_hit() -> bool:
    if is_dev():
        return check_cached_hit_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=CACHED_HIT))


def check_idempotency_reused() -> bool:
    if is_dev():
        return check_idempotency_reused_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=IDEMPOTENCY_REUSED))


def check_circuit_opened() -> bool:
    if is_dev():
        return check_circuit_opened_dev()
    raise NotImplementedError(EXC_CALCULATION_NOT_IMPLEMENTED.format(name=CIRCUIT_OPENED))

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
CB_DEFAULT_ERROR_CODES_TO_TRIP = [TIMEOUT, UNAVAILABLE, TOOL_ERROR]

# Idempotency defaults
IDEMPOTENCY_DEFAULT_ENABLED = True
IDEMPOTENCY_DEFAULT_TTL_S = 3600
IDEMPOTENCY_DEFAULT_PERSIST_RESULT = True
IDEMPOTENCY_DEFAULT_BYPASS_ON_MISSING_KEY = False

# HTTP/DB defaults
HTTP_DEFAULT_METHOD = POST
DB_DEFAULT_DRIVER = POSTGRESQL


