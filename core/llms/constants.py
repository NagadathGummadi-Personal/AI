"""
Constants for LLM Subsystem.

This module defines all constants used throughout the LLM subsystem including
log messages, configuration keys, defaults, and limits.
"""

# ============================================================================
# ENCODING & FORMAT
# ============================================================================

UTF_8 = "utf-8"
JSON_CONTENT_TYPE = "application/json"
TEXT_CONTENT_TYPE = "text/plain"

# ============================================================================
# LOG MESSAGES
# ============================================================================

# Connection & initialization
LOG_CONNECTOR_INITIALIZING = "Initializing LLM connector"
LOG_CONNECTOR_CONNECTED = "LLM connector connected successfully"
LOG_CONNECTOR_DISCONNECTED = "LLM connector disconnected"
LOG_CONNECTOR_CONNECTION_FAILED = "LLM connector connection failed"
LOG_CONNECTOR_TESTING = "Testing LLM connector connection"
LOG_CONNECTOR_TEST_SUCCESS = "LLM connector test successful"
LOG_CONNECTOR_TEST_FAILED = "LLM connector test failed"

# Request lifecycle
LOG_LLM_REQUEST_STARTING = "Starting LLM request"
LOG_LLM_REQUEST_COMPLETED = "LLM request completed successfully"
LOG_LLM_REQUEST_FAILED = "LLM request failed"
LOG_LLM_STREAMING_STARTED = "LLM streaming started"
LOG_LLM_STREAMING_CHUNK = "Received LLM streaming chunk"
LOG_LLM_STREAMING_COMPLETED = "LLM streaming completed"
LOG_LLM_STREAMING_FAILED = "LLM streaming failed"

# Validation
LOG_VALIDATING_INPUT = "Validating LLM input"
LOG_VALIDATION_PASSED = "LLM input validation passed"
LOG_VALIDATION_FAILED = "LLM input validation failed"
LOG_VALIDATING_PARAMETERS = "Validating LLM parameters"
LOG_PARAMETER_VALIDATION_PASSED = "LLM parameter validation passed"
LOG_PARAMETER_VALIDATION_FAILED = "LLM parameter validation failed"

# Token management
LOG_ESTIMATING_TOKENS = "Estimating token count"
LOG_TOKEN_LIMIT_EXCEEDED = "Token limit exceeded"
LOG_TOKEN_LIMIT_WARNING = "Approaching token limit"

# Model registry
LOG_REGISTERING_MODEL = "Registering model in registry"
LOG_MODEL_REGISTERED = "Model registered successfully"
LOG_MODEL_LOOKUP = "Looking up model in registry"
LOG_MODEL_NOT_FOUND = "Model not found in registry"
LOG_REGISTRY_INITIALIZING = "Initializing model registry"

# Cost & usage
LOG_CALCULATING_COST = "Calculating LLM usage cost"
LOG_COST_CALCULATED = "LLM cost calculated"
LOG_USAGE_TRACKED = "LLM usage tracked"

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_INVALID_INPUT = "Invalid input provided to LLM"
ERROR_UNSUPPORTED_INPUT_TYPE = "Unsupported input media type: {input_type}"
ERROR_UNSUPPORTED_OUTPUT_TYPE = "Unsupported output media type: {output_type}"
ERROR_MODEL_NOT_FOUND = "Model not found: {model_name}"
ERROR_PROVIDER_NOT_AVAILABLE = "Provider not available: {provider}"
ERROR_CONNECTION_FAILED = "Connection to provider failed: {provider}"
ERROR_AUTHENTICATION_FAILED = "Authentication failed for provider: {provider}"
ERROR_RATE_LIMIT_EXCEEDED = "Rate limit exceeded for provider: {provider}"
ERROR_QUOTA_EXCEEDED = "Quota exceeded for model: {model_name}"
ERROR_INVALID_RESPONSE = "Invalid response from provider: {provider}"
ERROR_JSON_PARSE_FAILED = "Failed to parse JSON response"
ERROR_TOKEN_LIMIT_EXCEEDED = "Token limit exceeded: {tokens} > {limit}"
ERROR_INVALID_PARAMETER = "Invalid parameter: {parameter}"
ERROR_MISSING_PARAMETER = "Missing required parameter: {parameter}"
ERROR_TIMEOUT = "Request timed out after {timeout}s"
ERROR_SERVICE_UNAVAILABLE = "Service unavailable: {provider}"

# ============================================================================
# CONFIGURATION KEYS
# ============================================================================

# Connector configuration
CONFIG_PROVIDER = "provider"
CONFIG_API_KEY = "api_key"
CONFIG_API_KEY_ENV = "api_key_env"
CONFIG_ENDPOINT = "endpoint"
CONFIG_REGION = "region"
CONFIG_DEPLOYMENT_NAME = "deployment_name"
CONFIG_API_VERSION = "api_version"
CONFIG_TIMEOUT = "timeout"
CONFIG_MAX_RETRIES = "max_retries"
CONFIG_RETRY_DELAY = "retry_delay"

# Model configuration
CONFIG_MODEL_NAME = "model_name"
CONFIG_MAX_TOKENS = "max_tokens"
CONFIG_TEMPERATURE = "temperature"
CONFIG_TOP_P = "top_p"
CONFIG_FREQUENCY_PENALTY = "frequency_penalty"
CONFIG_PRESENCE_PENALTY = "presence_penalty"
CONFIG_STOP_SEQUENCES = "stop"
CONFIG_STREAM = "stream"

# ============================================================================
# DEFAULT VALUES
# ============================================================================

# Connection defaults
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 1
DEFAULT_BACKOFF_FACTOR = 2

# Parameter defaults
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TOP_P = 1.0
DEFAULT_FREQUENCY_PENALTY = 0.0
DEFAULT_PRESENCE_PENALTY = 0.0

# Token limits (conservative estimates)
DEFAULT_MAX_CONTEXT_LENGTH = 8192
DEFAULT_MAX_INPUT_TOKENS = 4096
DEFAULT_MAX_OUTPUT_TOKENS = 4096

# Streaming
DEFAULT_STREAM_BUFFER_SIZE = 1024
DEFAULT_STREAM_TIMEOUT = 60

# ============================================================================
# STANDARD PARAMETER NAMES (OpenAI-style)
# ============================================================================

PARAM_MAX_TOKENS = "max_tokens"
PARAM_TEMPERATURE = "temperature"
PARAM_TOP_P = "top_p"
PARAM_FREQUENCY_PENALTY = "frequency_penalty"
PARAM_PRESENCE_PENALTY = "presence_penalty"
PARAM_STOP = "stop"
PARAM_STREAM = "stream"
PARAM_N = "n"
PARAM_LOGPROBS = "logprobs"
PARAM_ECHO = "echo"
PARAM_BEST_OF = "best_of"
PARAM_LOGIT_BIAS = "logit_bias"
PARAM_USER = "user"

# ============================================================================
# METADATA KEYS
# ============================================================================

META_MODEL_NAME = "model_name"
META_PROVIDER = "provider"
META_MODEL_FAMILY = "model_family"
META_REQUEST_ID = "request_id"
META_TIMESTAMP = "timestamp"
META_DURATION_MS = "duration_ms"
META_INPUT_TOKENS = "input_tokens"
META_OUTPUT_TOKENS = "output_tokens"
META_TOTAL_TOKENS = "total_tokens"
META_FINISH_REASON = "finish_reason"
META_COST_USD = "cost_usd"

# ============================================================================
# METRIC NAMES
# ============================================================================

METRIC_LLM_CALLS = "llm.calls"
METRIC_LLM_ERRORS = "llm.errors"
METRIC_LLM_LATENCY = "llm.latency"
METRIC_LLM_TOKENS_INPUT = "llm.tokens.input"
METRIC_LLM_TOKENS_OUTPUT = "llm.tokens.output"
METRIC_LLM_COST = "llm.cost"

# ============================================================================
# LIMITS & CONSTRAINTS
# ============================================================================

# Token estimation (rough heuristics)
CHARS_PER_TOKEN_ESTIMATE = 4
TOKENS_PER_MESSAGE_OVERHEAD = 4  # Approximate per-message formatting tokens

# Retry limits
MAX_RETRY_ATTEMPTS = 5
MIN_RETRY_DELAY_MS = 100
MAX_RETRY_DELAY_MS = 32000

# Rate limiting
RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_REQUESTS_PER_MINUTE = 60

# ============================================================================
# API FIELD NAMES (Provider-specific mappings source)
# ============================================================================

# OpenAI/Azure field names
OPENAI_FIELD_MESSAGES = "messages"
OPENAI_FIELD_MODEL = "model"
OPENAI_FIELD_MAX_TOKENS = "max_tokens"
OPENAI_FIELD_TEMPERATURE = "temperature"
OPENAI_FIELD_TOP_P = "top_p"
OPENAI_FIELD_FREQUENCY_PENALTY = "frequency_penalty"
OPENAI_FIELD_PRESENCE_PENALTY = "presence_penalty"
OPENAI_FIELD_STOP = "stop"
OPENAI_FIELD_STREAM = "stream"
OPENAI_FIELD_FUNCTIONS = "functions"
OPENAI_FIELD_FUNCTION_CALL = "function_call"
OPENAI_FIELD_TOOLS = "tools"
OPENAI_FIELD_TOOL_CHOICE = "tool_choice"

# Response field names
RESPONSE_FIELD_CHOICES = "choices"
RESPONSE_FIELD_MESSAGE = "message"
RESPONSE_FIELD_CONTENT = "content"
RESPONSE_FIELD_ROLE = "role"
RESPONSE_FIELD_FINISH_REASON = "finish_reason"
RESPONSE_FIELD_USAGE = "usage"
RESPONSE_FIELD_PROMPT_TOKENS = "prompt_tokens"
RESPONSE_FIELD_COMPLETION_TOKENS = "completion_tokens"
RESPONSE_FIELD_TOTAL_TOKENS = "total_tokens"

# Stream response fields
STREAM_FIELD_DELTA = "delta"
STREAM_FIELD_CONTENT = "content"
STREAM_FIELD_ROLE = "role"

# ============================================================================
# CONTENT FILTERS & SAFETY
# ============================================================================

CONTENT_FILTER_HATE = "hate"
CONTENT_FILTER_VIOLENCE = "violence"
CONTENT_FILTER_SEXUAL = "sexual"
CONTENT_FILTER_SELF_HARM = "self_harm"

# ============================================================================
# REGISTRY KEYS
# ============================================================================

REGISTRY_KEY_MODELS = "models"
REGISTRY_KEY_PROVIDERS = "providers"
REGISTRY_KEY_FAMILIES = "families"

# ============================================================================
# ENVIRONMENT VARIABLE NAMES
# ============================================================================

ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_AZURE_OPENAI_KEY = "AZURE_OPENAI_KEY"
ENV_AZURE_OPENAI_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
ENV_AZURE_OPENAI_DEPLOYMENT = "AZURE_OPENAI_DEPLOYMENT"
ENV_AZURE_OPENAI_API_VERSION = "AZURE_OPENAI_API_VERSION"

# ============================================================================
# DEFAULT CONTEXT DATA GENERATORS (similar to tools)
# ============================================================================

def DEFAULT_LLM_CONTEXT_DATA(model_name: str, provider: str) -> dict:
    """Generate default context data for LLM logging."""
    return {
        META_MODEL_NAME: model_name,
        META_PROVIDER: provider,
    }


def LLM_ERROR_MESSAGE(error_type: str, details: str) -> str:
    """Format LLM error message."""
    return f"LLM Error [{error_type}]: {details}"

