"""
Centralized default values for the llms package.

These constants are used across spec models and implementations to
avoid scattering literal defaults and to make production tuning easier.
"""

from .enums import InputMediaType, OutputMediaType
from .constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TOP_P,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ERROR_LLM,
    ERROR_RATE_LIMIT,
    TOKENS_IN,
    TOKENS_OUT,
    COST_USD,
    MODEL_NAME,
    PROVIDER,
    REQUEST_ID,
    TIMESTAMP,
    DURATION_MS,
    STREAMING,
    VERSION_1_0_0,
    DEV,
    AZURE_OPENAI_DEFAULT_API_VERSION,
    BEDROCK_DEFAULT_REGION,
    BEDROCK_DEFAULT_MODEL_ID,
    GEMINI_DEFAULT_API_VERSION,
    GEMINI_DEFAULT_LOCATION,
    CONTENT,
    USAGE,
    SUCCESS,
    ERROR,
    IS_FINAL,
    MSG_INVALID_TEMPERATURE_RANGE_AZURE_OPENAI,
    MSG_INVALID_TEMPERATURE_RANGE_BEDROCK,
    MSG_INVALID_TEMPERATURE_RANGE_GEMINI,
    MSG_INVALID_MAX_TOKENS_POSITIVE,
    MSG_AT_LEAST_ONE_INPUT_TYPE_SUPPORTED,
    MSG_AT_LEAST_ONE_OUTPUT_TYPE_SUPPORTED,
    MSG_JSON_OUTPUT_REQUIRES_JSON_SCHEMA_OR_JSON_CLASS,
    MSG_MISSING_API_KEY,
    MSG_MISSING_MODEL_NAME,
    MSG_ENDPOINT_OR_DEPLOYMENT_NAME_REQUIRED_AZURE_OPENAI,
    MSG_REGION_REQUIRED_BEDROCK,
    MSG_MODEL_ID_REQUIRED_BEDROCK,
    MSG_PROJECT_ID_REQUIRED_GEMINI,
    MSG_PROVIDER_NOT_SUPPORTED,
    EXC_ANSWER_NOT_IMPLEMENTED,
    EXC_STREAMING_NOT_IMPLEMENTED,
)

# LLM Configuration defaults
DEFAULT_LLM_TEMPERATURE = DEFAULT_TEMPERATURE
DEFAULT_LLM_MAX_TOKENS = DEFAULT_MAX_TOKENS
DEFAULT_LLM_TOP_P = DEFAULT_TOP_P
DEFAULT_LLM_FREQUENCY_PENALTY = DEFAULT_FREQUENCY_PENALTY
DEFAULT_LLM_PRESENCE_PENALTY = DEFAULT_PRESENCE_PENALTY
DEFAULT_LLM_TIMEOUT = DEFAULT_TIMEOUT
DEFAULT_LLM_MAX_RETRIES = DEFAULT_MAX_RETRIES

# Supported input/output defaults
DEFAULT_SUPPORTED_INPUT_TYPES = {InputMediaType.TEXT}
DEFAULT_SUPPORTED_OUTPUT_TYPES = {OutputMediaType.TEXT}
DEFAULT_STREAMING_SUPPORTED = True

# Environment defaults

DEFAULT_LLM_VERSION = VERSION_1_0_0
DEFAULT_LLM_ENVIRONMENT = DEV

# Provider-specific defaults
AZURE_OPENAI_DEFAULT_API_VERSION = AZURE_OPENAI_DEFAULT_API_VERSION
AZURE_OPENAI_DEFAULT_BASE_URL = None  # Will use default Azure endpoint
BEDROCK_DEFAULT_REGION = BEDROCK_DEFAULT_REGION
BEDROCK_DEFAULT_MODEL_ID = BEDROCK_DEFAULT_MODEL_ID
GEMINI_DEFAULT_API_VERSION = GEMINI_DEFAULT_API_VERSION
GEMINI_DEFAULT_LOCATION = GEMINI_DEFAULT_LOCATION

# -------- Context data builders --------


def DEFAULT_LLM_CONTEXT_DATA(spec, ctx):
    """Standard context dict for LLM requests."""
    return {
        MODEL_NAME: getattr(spec, MODEL_NAME, None),
        PROVIDER: getattr(spec, PROVIDER, None),
        REQUEST_ID: getattr(ctx, REQUEST_ID, None),
        TIMESTAMP: getattr(ctx, TIMESTAMP, None),
        DURATION_MS: getattr(ctx, DURATION_MS, None),
        STREAMING: getattr(ctx, STREAMING, False),
    }


def DEFAULT_LLM_USAGE_DATA(
    tokens_in: int = 0, tokens_out: int = 0, cost_usd: float = 0.0
):
    """Standard usage data structure for LLM requests."""
    return {
        TOKENS_IN: tokens_in,
        TOKENS_OUT: tokens_out,
        COST_USD: cost_usd,
    }


# -------- Dev-only mock result builders --------
def DEFAULT_LLM_SUCCESS_RESPONSE(content: str = "Mock LLM response", usage=None):
    """Default success response for testing."""
    return {
        CONTENT: content,
        USAGE: usage or DEFAULT_LLM_USAGE_DATA(),
        SUCCESS: True,
    }


def DEFAULT_LLM_ERROR_RESPONSE(error: str = "Mock LLM error"):
    """Default error response for testing."""
    return {
        ERROR: error,
        SUCCESS: False,
    }


def DEFAULT_LLM_STREAM_CHUNK(
    content: str = "Mock stream chunk", is_final: bool = False
):
    """Default streaming chunk for testing."""
    return {
        CONTENT: content,
        IS_FINAL: is_final,
    }


# Retry defaults (following tools pattern)
RETRY_DEFAULT_MAX_ATTEMPTS = DEFAULT_LLM_MAX_RETRIES
RETRY_DEFAULT_BASE_DELAY_S = 0.2
RETRY_DEFAULT_MAX_DELAY_S = 2.0
RETRY_DEFAULT_JITTER_S = 0.1

# Circuit breaker defaults (following tools pattern)
CB_DEFAULT_ENABLED = True
CB_DEFAULT_FAILURE_THRESHOLD = 5
CB_DEFAULT_RECOVERY_TIMEOUT_S = 30
CB_DEFAULT_HALF_OPEN_MAX_CALLS = 1
CB_DEFAULT_ERROR_CODES_TO_TRIP = [
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ERROR_LLM,
    ERROR_RATE_LIMIT,
]

# Idempotency defaults (following tools pattern)
IDEMPOTENCY_DEFAULT_ENABLED = True
IDEMPOTENCY_DEFAULT_TTL_S = 3600
IDEMPOTENCY_DEFAULT_PERSIST_RESULT = True
IDEMPOTENCY_DEFAULT_BYPASS_ON_MISSING_KEY = False

# Rate limiting defaults
RATE_LIMIT_DEFAULT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_DEFAULT_BURST_SIZE = 10

# JSON processing defaults
JSON_DEFAULT_INDENT = 2
JSON_DEFAULT_SEPARATORS = (", ", ": ")
JSON_DEFAULT_ENSURE_ASCII = False
