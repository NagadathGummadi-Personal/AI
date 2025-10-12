"""
Centralized default values for the llms package.

These constants are used across spec models and implementations to
avoid scattering literal defaults and to make production tuning easier.
"""

from .enums import InputType, OutputMediaType, LLMProvider
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
DEFAULT_SUPPORTED_INPUT_TYPES = {InputType.TEXT}
DEFAULT_SUPPORTED_OUTPUT_TYPES = {OutputMediaType.TEXT}
DEFAULT_STREAMING_SUPPORTED = True

# Environment defaults
DEFAULT_LLM_VERSION = "1.0.0"
DEFAULT_LLM_ENVIRONMENT = "dev"

# Provider-specific defaults
AZURE_OPENAI_DEFAULT_API_VERSION = "2023-12-01-preview"
AZURE_OPENAI_DEFAULT_BASE_URL = None  # Will use default Azure endpoint
BEDROCK_DEFAULT_REGION = "us-east-1"
BEDROCK_DEFAULT_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
GEMINI_DEFAULT_API_VERSION = "v1"
GEMINI_DEFAULT_LOCATION = "us-central1"

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


def DEFAULT_LLM_USAGE_DATA(tokens_in: int = 0, tokens_out: int = 0, cost_usd: float = 0.0):
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
        "content": content,
        "usage": usage or DEFAULT_LLM_USAGE_DATA(),
        "success": True,
    }


def DEFAULT_LLM_ERROR_RESPONSE(error: str = "Mock LLM error"):
    """Default error response for testing."""
    return {
        "error": error,
        "success": False,
    }


def DEFAULT_LLM_STREAM_CHUNK(content: str = "Mock stream chunk", is_final: bool = False):
    """Default streaming chunk for testing."""
    return {
        "content": content,
        "is_final": is_final,
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
