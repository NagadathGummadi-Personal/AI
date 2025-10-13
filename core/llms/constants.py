"""
Central constants for literals, error codes, event names, and logging formats for LLM operations.
"""

# Error codes
ERROR_TIMEOUT = "TIMEOUT"
ERROR_UNAVAILABLE = "UNAVAILABLE"
ERROR_LLM = "LLM_ERROR"
ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_JSON_PARSING = "JSON_PARSING_ERROR"
ERROR_INPUT_VALIDATION = "INPUT_VALIDATION_ERROR"
ERROR_PROVIDER = "PROVIDER_ERROR"
ERROR_RATE_LIMIT = "RATE_LIMIT_ERROR"
ERROR_CONFIGURATION = "CONFIGURATION_ERROR"

# Event/Metric Names
METRIC_LLM_REQUEST_STARTED = "llm.request.started"
METRIC_LLM_REQUEST_SUCCESS = "llm.request.success"
METRIC_LLM_REQUEST_FAILED = "llm.request.failed"
METRIC_LLM_REQUEST_TIME = "llm.request_time"
METRIC_LLM_TOKENS_IN = "llm.tokens_in"
METRIC_LLM_TOKENS_OUT = "llm.tokens_out"
METRIC_LLM_COST_USD = "llm.cost_usd"

# Logging Messages (format strings)
LOG_STARTING_LLM_REQUEST = "Starting LLM request"
LOG_LLM_PARAMETERS = "LLM request parameters"
LOG_LLM_VALIDATING = "Validating LLM input"
LOG_LLM_VALIDATION_PASSED = "LLM input validation passed"
LOG_LLM_VALIDATION_FAILED = "LLM input validation failed"
LOG_LLM_REQUEST_COMPLETED = "LLM request completed"
LOG_LLM_REQUEST_FAILED = "LLM request failed"
LOG_LLM_STREAMING_STARTED = "LLM streaming started"
LOG_LLM_STREAMING_CHUNK = "LLM streaming chunk received"
LOG_LLM_STREAMING_COMPLETED = "LLM streaming completed"
LOG_LLM_JSON_PROCESSING = "Processing JSON response"
LOG_LLM_JSON_PARSING_SUCCESS = "JSON response parsed successfully"
LOG_LLM_JSON_PARSING_FAILED = "JSON response parsing failed"
LOG_LLM_PROMPT_MERGING = "Merging system prompt with messages"
LOG_LLM_JUMP_START_TEST = "Testing LLM connectivity with jump_start"

# Provider-specific logging
LOG_AZURE_OPENAI_REQUEST = "Azure OpenAI request started"
LOG_AZURE_OPENAI_COMPLETED = "Azure OpenAI request completed"
LOG_AZURE_OPENAI_FAILED = "Azure OpenAI request failed"
LOG_BEDROCK_REQUEST = "Bedrock request started"
LOG_BEDROCK_COMPLETED = "Bedrock request completed"
LOG_BEDROCK_FAILED = "Bedrock request failed"
LOG_GEMINI_REQUEST = "Gemini request started"
LOG_GEMINI_COMPLETED = "Gemini request completed"
LOG_GEMINI_FAILED = "Gemini request failed"

# Demo/Example event names
EVENT_LLM_REQUEST_STARTED = "LLM_REQUEST_STARTED"
EVENT_LLM_REQUEST_COMPLETED = "LLM_REQUEST_COMPLETED"
EVENT_LLM_STREAM_CHUNK = "LLM_STREAM_CHUNK"
EVENT_LLM_STREAM_COMPLETED = "LLM_STREAM_COMPLETED"
EVENT_LLM_ERROR = "LLM_ERROR"
EVENT_LLM_VALIDATION = "LLM_VALIDATION"
EVENT_LLM_JSON_PROCESSING = "LLM_JSON_PROCESSING"

# Message roles
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_FUNCTION = "function"

# Content types
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_IMAGE = "image"
CONTENT_TYPE_AUDIO = "audio"
CONTENT_TYPE_VIDEO = "video"
CONTENT_TYPE_DOCUMENT = "document"
CONTENT_TYPE_MULTIMODAL = "multimodal"

# Media types
MEDIA_TYPE_TEXT = "text"
MEDIA_TYPE_AUDIO = "audio"
MEDIA_TYPE_IMAGE = "image"
MEDIA_TYPE_JSON = "json"
MEDIA_TYPE_EMBEDDING = "embedding"

# LLM Types
LLM_TYPE_CHAT = "chat"
LLM_TYPE_COMPLETION = "completion"
LLM_TYPE_EMBEDDING = "embedding"
LLM_TYPE_MULTIMODAL = "multimodal"

# Provider names
PROVIDER_AZURE_OPENAI = "azure_openai"
PROVIDER_BEDROCK = "bedrock"
PROVIDER_GEMINI = "gemini"

# Model enum class names (for __getattr__)
AZURE_OPENAI_MODEL = "AzureOpenAIModel"
BEDROCK_MODEL = "BedrockModel"
GEMINI_MODEL = "GeminiModel"
MODEL_CAPABILITIES = "MODEL_CAPABILITIES"
MODEL_PARAMETER_DEFAULTS = "MODEL_PARAMETER_DEFAULTS"

# Azure OpenAI model names
AZURE_OPENAI_GPT_4O = "gpt-4o"
AZURE_OPENAI_GPT_4_1_MINI = "gpt-4.1-mini"
AZURE_OPENAI_GPT_4O_MINI = "gpt-4o-mini"
AZURE_OPENAI_GPT_4_TURBO = "gpt-4-turbo"
AZURE_OPENAI_GPT_4 = "gpt-4"
AZURE_OPENAI_GPT_35_TURBO = "gpt-3.5-turbo"
AZURE_OPENAI_GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
AZURE_OPENAI_GPT_35_TURBO_0125 = "gpt-3.5-turbo-0125"

# Azure OpenAI model families
AZURE_MODEL_FAMILY_GPT_4O = "gpt-4o"
AZURE_MODEL_FAMILY_GPT_4 = "gpt-4"
AZURE_MODEL_FAMILY_GPT_35 = "gpt-3.5"

# Bedrock model names (Anthropic Claude)
BEDROCK_CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
BEDROCK_CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
BEDROCK_CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240229-v1:0"
BEDROCK_CLAUDE_35_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# Bedrock model families
BEDROCK_MODEL_FAMILY_CLAUDE_3 = "claude-3"
BEDROCK_MODEL_FAMILY_CLAUDE_35 = "claude-3.5"

# Gemini model names
GEMINI_PRO = "gemini-pro"
GEMINI_PRO_VISION = "gemini-pro-vision"
GEMINI_1_5_PRO = "gemini-1.5-pro"
GEMINI_1_5_FLASH = "gemini-1.5-flash"
GEMINI_1_5_PRO_002 = "gemini-1.5-pro-002"
GEMINI_1_5_FLASH_002 = "gemini-1.5-flash-002"

# Gemini model families
GEMINI_MODEL_FAMILY_PRO = "gemini-pro"
GEMINI_MODEL_FAMILY_1_5 = "gemini-1.5"

# Encoding constants
UTF_8 = "utf-8"

# Status constants
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_TIMEOUT = "timeout"
STATUS_RATE_LIMITED = "rate_limited"

# Generic constants
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TOP_P = 1.0
DEFAULT_FREQUENCY_PENALTY = 0.0
DEFAULT_PRESENCE_PENALTY = 0.0
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3

# Parameter names for unified interface
TEMPERATURE = "temperature"
MAX_TOKENS = "max_tokens"
TOP_P = "top_p"
FREQUENCY_PENALTY = "frequency_penalty"
PRESENCE_PENALTY = "presence_penalty"
STOP_SEQUENCES = "stop_sequences"
JSON_MODE = "json_mode"
STREAMING = "streaming"

# Gemini safety settings
GEMINI_SAFETY_HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
GEMINI_SAFETY_HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
GEMINI_SAFETY_HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
GEMINI_SAFETY_HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"
GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"

# JSON response format types
JSON_OBJECT_TYPE = "json_object"

# Keys for usage tracking
TOKENS_IN = "tokens_in"
TOKENS_OUT = "tokens_out"
COST_USD = "cost_usd"
MODEL_NAME = "model_name"
PROVIDER = "provider"
REQUEST_ID = "request_id"
TIMESTAMP = "timestamp"
DURATION_MS = "duration_ms"
STREAMING = "streaming"

# Error message format strings
MSG_INPUT_VALIDATION_FAILED = "Input validation failed for {input_type}: {error}"
MSG_UNSUPPORTED_INPUT_TYPE = "Unsupported input type: {input_type}"
MSG_UNSUPPORTED_OUTPUT_TYPE = "Unsupported output type: {output_type}"
MSG_TEXT_INPUT_MUST_BE_STRING = "Text input must be a string"
MSG_IMAGE_INPUT_MUST_BE_STRING_OR_BYTES = "Image input must be a string (URL/path) or bytes"
MSG_JSON_SCHEMA_REQUIRED = "JSON output enabled but no json_schema or json_class provided"
MSG_INVALID_TEMPERATURE = "Temperature must be between 0 and 2"
MSG_INVALID_MAX_TOKENS = "Max tokens must be positive"
MSG_MISSING_API_KEY = "API key is required for provider {provider}"
MSG_MISSING_MODEL_NAME = "Model name is required"
MSG_PROVIDER_NOT_SUPPORTED = "Provider {provider} is not supported"
MSG_JUMP_START_FAILED = "LLM jump_start connectivity test failed"
MSG_INVALID_TEMPERATURE_RANGE_AZURE_OPENAI = "Temperature must be between 0 and 2"
MSG_INVALID_TEMPERATURE_RANGE_BEDROCK = "Temperature must be between 0 and 1"
MSG_INVALID_TEMPERATURE_RANGE_GEMINI = "Temperature must be between 0 and 2"
MSG_INVALID_MAX_TOKENS_POSITIVE = "Max tokens must be positive"
MSG_AT_LEAST_ONE_INPUT_TYPE_SUPPORTED = "At least one input type must be supported"
MSG_AT_LEAST_ONE_OUTPUT_TYPE_SUPPORTED = "At least one output type must be supported"
MSG_JSON_OUTPUT_REQUIRES_JSON_SCHEMA_OR_JSON_CLASS = "json_output=True requires json_schema or json_class"
MSG_ENDPOINT_OR_DEPLOYMENT_NAME_REQUIRED_AZURE_OPENAI = "Either endpoint or deployment_name must be provided for Azure OpenAI"
MSG_REGION_REQUIRED_BEDROCK = "Region is required for Bedrock"
MSG_MODEL_ID_REQUIRED_BEDROCK = "Model ID is required for Bedrock"
MSG_PROJECT_ID_REQUIRED_GEMINI = "Project ID is required for Gemini"
MSG_PROVIDER_NOT_SUPPORTED = "Provider {provider} is not supported"
MSG_MODEL_DOES_NOT_SUPPORT_FUNCTION_CALLING = "Model {model_name} does not support function calling"
MSG_NO_HANDLER_REGISTERED_FOR_TOOL = "No handler registered for tool: {tool_name}"
MSG_INVALID_JSON_OUTPUT = "Invalid JSON output: {e}"

# Tool integration logging
LOG_LLM_TOOL_CONVERSION = "Converting tool spec to provider format"
LOG_LLM_TOOL_CALL_STARTED = "Tool call started"
LOG_LLM_TOOL_CALL_COMPLETED = "Tool call completed"
LOG_LLM_TOOL_CALL_FAILED = "Tool call failed"

# Tool integration error messages
MSG_UNSUPPORTED_PARAMETER_TYPE = "Unsupported parameter type: {param_type}"
MSG_TOOL_CONVERSION_FAILED = "Failed to convert tool spec: {error}"
MSG_TOOL_EXECUTION_FAILED = "Tool execution failed: {error}"
MSG_TOOL_NOT_FOUND = "Tool not found: {tool_name}"

# Generic exception messages
EXC_LLM_NOT_IMPLEMENTED = "LLM implementation not available"
EXC_STREAMING_NOT_IMPLEMENTED = "Streaming not implemented for this provider"
EXC_EMBEDDING_NOT_IMPLEMENTED = "Embedding not implemented for this provider"
EXC_MULTIMODAL_NOT_IMPLEMENTED = "Multimodal input not implemented for this provider"

# HTTP status codes for reference
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_GATEWAY_TIMEOUT = 504

# Other constants

# Model constants
AZURE_OPENAI_MODEL = "AzureOpenAIModel"
BEDROCK_MODEL = "BedrockModel"
GEMINI_MODEL = "GeminiModel"
MODEL_CAPABILITIES = "MODEL_CAPABILITIES"
MODEL_PARAMETER_DEFAULTS = "MODEL_PARAMETER_DEFAULTS"

# Message roles
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_FUNCTION = "function"

# Provider constants
AZURE_OPENAI_DEFAULT_API_VERSION = "2023-12-01-preview"
BEDROCK_DEFAULT_REGION = "us-east-1"
BEDROCK_DEFAULT_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
GEMINI_DEFAULT_API_VERSION = "v1"
GEMINI_DEFAULT_LOCATION = "us-central1"
VERSION_1_0_0 = "1.0.0"
DEV = "dev"
CONTENT = "content"
USAGE = "usage"
SUCCESS = "success"
ERROR = "error"
IS_FINAL = "is_final"
PING = "ping"
ROLE = "role"
ROLE_USER = "user"
CONTENT = "content"
MAX_TOKENS_LIMIT = "max_tokens_limit"
MAX_CONTEXT_LENGTH = "max_context_length"
SUPPORTS_VISION = "supports_vision"
SUPPORTS_FUNCTION_CALLING = "supports_function_calling"
INPUTS = "inputs"
OUTPUTS = "outputs"
JSON_OUTPUT = "json_output"
TEMPERATURE_RANGE = "temperature_range"
MODEL_VALIDATE = "model_validate"
PARSE_OBJ = "parse_obj"
