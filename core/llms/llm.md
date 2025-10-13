# LLM System Technical Documentation

## Overview

The LLM (Large Language Model) system provides a unified and extensible interface across multiple LLM providers (Azure OpenAI, Amazon Bedrock, and Google Gemini) with comprehensive support for:

- **Multi-modal input/output**: Text, Image, Audio, Video, Document, Multimodal
- **Streaming and non-streaming responses**
- **JSON-structured responses and validation**
- **Function calling and tool integration**
- **Dynamic system prompt variables**
- **Comprehensive error handling and validation**
- **Model registry and metadata management**
- **Provider-specific optimizations and parameter mappings**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM System (core/llms/)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Interfaces    │  │  Configuration  │  │   Base Class    │  │
│  │   (ILLM)        │  │   (Configs)     │  │   (BaseLLM)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Model         │  │   Tool          │  │   Provider      │  │
│  │   Registry      │  │   Integration   │  │   Connectors    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Enums &       │  │   Constants &   │  │   Exceptions    │  │
│  │   Types         │  │   Defaults      │  │   & Errors      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Interfaces (`interfaces.py`)

#### ILLM Protocol
The core interface that all LLM implementations must implement:

```python
@runtime_checkable
class ILLM(Protocol):
    @abstractmethod
    async def get_answer(self, messages: List[Dict[str, Any]], **kwargs) -> LLMResponse:
        """Get a complete response from the LLM"""

    @abstractmethod
    async def get_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[LLMStreamChunk]:
        """Get a streaming response from the LLM"""

    @abstractmethod
    async def jump_start(self) -> bool:
        """Test connectivity to the LLM provider"""

    @abstractmethod
    def validate_input(self, input_type: InputMediaType, content: Any) -> bool:
        """Validate input for the given input type"""

    @abstractmethod
    def get_supported_capabilities(self) -> Dict[str, Any]:
        """Get information about supported capabilities"""
```

#### Response Models
```python
class LLMResponse:
    def __init__(self, content: Any, usage: Optional[Dict[str, Any]] = None):
        self.content = content  # Response content (str, dict, or Pydantic model)
        self.usage = usage or {}  # Usage statistics and metadata

class LLMStreamChunk:
    def __init__(self, content: str, is_final: bool = False):
        self.content = content    # Chunk content
        self.is_final = is_final  # Whether this is the final chunk
        self.usage = None         # Usage info (set on final chunk)
```

### 2. Base Class (`base_llm.py`)

The `BaseLLM` class provides the foundation for all LLM provider implementations:

#### Key Features
- **Input validation and processing**
- **System prompt merging with dynamic variable replacement**
- **JSON response processing and validation**
- **Usage tracking and metrics**
- **Tool registration and execution**
- **Error handling and retry logic**
- **Provider capability detection**

#### Dynamic Variable System
```python
# In BaseLLMConfig
dynamic_variables: Optional[Dict[str, Any]] = None

# In BaseLLM
def _replace_dynamic_variables(self, prompt: str) -> str:
    """Replace {{variable_name}} patterns in system prompts"""
    def replace_variable(match):
        var_name = match.group(1)
        return str(self.config.dynamic_variables.get(var_name, match.group(0)))

    pattern = r'\{\{(\w+)\}\}'
    return re.sub(pattern, replace_variable, prompt)
```

#### System Prompt Merging
```python
def _merge_prompt(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge system prompt with messages if configured"""
    if not self.config.prompt:
        return messages

    processed_prompt = self._replace_dynamic_variables(self.config.prompt)
    return [{ROLE: ROLE_SYSTEM, CONTENT: processed_prompt}, *messages]
```

### 3. Configuration System (`configs.py`)

#### BaseLLMConfig
Base configuration class with common parameters:

```python
@dataclass
class BaseLLMConfig:
    # Provider and model
    provider: LLMProvider
    model_name: str
    api_key: str

    # Generation parameters
    temperature: float = DEFAULT_LLM_TEMPERATURE
    max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    top_p: float = DEFAULT_LLM_TOP_P
    frequency_penalty: float = DEFAULT_LLM_FREQUENCY_PENALTY
    presence_penalty: float = DEFAULT_LLM_PRESENCE_PENALTY
    stop_sequences: List[str] = field(default_factory=list)

    # Timing and retry
    timeout: int = DEFAULT_LLM_TIMEOUT
    max_retries: int = DEFAULT_LLM_MAX_RETRIES

    # Input/output handling
    supported_input_types: Set[InputMediaType] = field(default_factory=lambda: DEFAULT_SUPPORTED_INPUT_TYPES)
    supported_output_types: Set[OutputMediaType] = field(default_factory=lambda: DEFAULT_SUPPORTED_OUTPUT_TYPES)
    streaming_supported: bool = DEFAULT_STREAMING_SUPPORTED

    # Extended config
    prompt: Optional[str] = None
    dynamic_variables: Optional[Dict[str, Any]] = None  # NEW: Dynamic variable support
    json_output: bool = False
    json_schema: Optional[Dict[str, Any]] = None
    json_class: Optional[Union[Type[BaseModel], Type[Any]]] = None

    # Provider-specific settings
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    region: Optional[str] = None
```

#### Provider-Specific Configurations
- **AzureOpenAIConfig**: Azure OpenAI specific settings (endpoint, deployment_name)
- **BedrockConfig**: AWS Bedrock settings (region, model_id)
- **GeminiConfig**: Google Gemini settings (project_id, location)

### 4. Enums and Types (`enums.py`)

#### InputMediaType
```python
class InputMediaType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    MULTIMODAL = "multimodal"
```

#### OutputMediaType
```python
class OutputMediaType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    JSON = "json"
    MULTIMODAL = "multimodal"
```

#### LLMProvider
```python
class LLMProvider(str, Enum):
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    GEMINI = "gemini"
```

#### MessageRole
```python
class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
```

### 5. Constants and Defaults (`constants.py`, `defaults.py`)

#### Key Constants
```python
# Message roles
ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_FUNCTION = "function"

# Content types
CONTENT = "content"
ROLE = "role"

# Usage tracking
TOKENS_IN = "tokens_in"
TOKENS_OUT = "tokens_out"
COST_USD = "cost_usd"
DURATION_MS = "duration_ms"
STREAMING = "streaming"

# Provider identifiers
PROVIDER_AZURE_OPENAI = "azure_openai"
PROVIDER_BEDROCK = "bedrock"
PROVIDER_GEMINI = "gemini"
```

#### Error Messages
```python
MSG_UNSUPPORTED_INPUT_TYPE = "Unsupported input type: {input_type}"
MSG_TEXT_INPUT_MUST_BE_STRING = "Text input must be a string"
MSG_IMAGE_INPUT_MUST_BE_STRING_OR_BYTES = "Image input must be a string (URL/path) or bytes"
MSG_INVALID_JSON_OUTPUT = "Invalid JSON output: {e}"
MSG_MODEL_DOES_NOT_SUPPORT_FUNCTION_CALLING = "Model {model_name} does not support function calling"
MSG_TOOL_EXECUTION_FAILED = "Tool execution failed: {error}"
```

### 6. Exception Hierarchy (`exceptions.py`)

```python
class LLMError(Exception):
    """Base exception for all LLM-related errors"""

class InputValidationError(LLMError):
    """Raised when LLM input validation fails"""

class ProviderError(LLMError):
    """Raised when there's an error with the LLM provider"""

class ConfigurationError(LLMError):
    """Raised when LLM configuration is invalid"""

class RateLimitError(LLMError):
    """Raised when rate limit is exceeded"""

class JSONParsingError(LLMError):
    """Raised when JSON response parsing fails"""

class TimeoutError(LLMError):
    """Raised when LLM request times out"""

class AuthenticationError(LLMError):
    """Raised when authentication with LLM provider fails"""

class QuotaExceededError(LLMError):
    """Raised when API quota is exceeded"""

class ServiceUnavailableError(LLMError):
    """Raised when LLM service is unavailable"""

class InvalidResponseError(LLMError):
    """Raised when LLM returns an invalid response"""
```

### 7. Model Registry (`model_registry.py`)

#### ModelMetadata
Comprehensive model specification:

```python
@dataclass
class ModelMetadata:
    # Basic identification
    model_name: str
    provider: LLMProvider
    model_family: ModelFamily
    display_name: str

    # Capabilities
    supported_input_types: Set[InputMediaType]
    supported_output_types: Set[OutputMediaType]
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False

    # Limits
    max_context_length: int = 128000
    max_output_tokens: int = 4096
    max_input_tokens: int = 128000

    # Parameter mappings (provider-specific parameter names)
    parameter_mappings: Dict[str, str] = field(default_factory=dict)

    # API requirements and quirks
    api_requirements: Dict[str, Any] = field(default_factory=dict)

    # Pricing information
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None

    # Deprecation tracking
    is_deprecated: bool = False
    deprecation_date: Optional[str] = None
    replacement_model: Optional[str] = None
```

#### Model Registry
```python
class ModelRegistry:
    """Central registry managing all models"""

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._families: Dict[ModelFamily, List[str]] = {}

    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a new model"""

    def get_model(self, model_name: str) -> Optional[ModelMetadata]:
        """Get metadata for a specific model"""

    def get_family_models(self, family: ModelFamily) -> List[str]:
        """Get all models in a family"""

    def get_provider_models(self, provider: LLMProvider) -> List[str]:
        """Get all models for a provider"""
```

### 8. Tool Integration (`tool_integration.py`)

#### Tool Converter System
```python
class ToolConverter:
    """Base class for converting tools between formats"""

    @abstractmethod
    def convert_tool_spec(self, tool_spec) -> Dict[str, Any]:
        """Convert tool spec to provider format"""

    @abstractmethod
    def convert_tool_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """Convert tool result to provider format"""

class ToolConverterFactory:
    """Factory for creating provider-specific tool converters"""

    _converters = {
        LLMProvider.AZURE_OPENAI: AzureOpenAIToolConverter,
        LLMProvider.BEDROCK: BedrockToolConverter,
        LLMProvider.GEMINI: GeminiToolConverter,
    }

    @classmethod
    def get_converter(cls, provider: LLMProvider) -> ToolConverter:
        """Get converter for specific provider"""
```

#### Provider-Specific Formats

**Azure OpenAI Format:**
```json
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

**Bedrock (Claude) Format:**
```json
{
    "name": "tool_name",
    "description": "Tool description",
    "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

**Gemini Format:**
```json
{
    "name": "tool_name",
    "description": "Tool description",
    "parameters": {
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

### 9. Provider Connectors

#### Azure OpenAI (`connectors/azure/`)
- **AzureLLM**: Main implementation class
- **azure_llm.py**: Core Azure OpenAI integration
- **converter.py**: Request/response conversion
- **model_registry.py**: Azure model definitions
- **models.py**: Azure model enums
- **tool_converter.py**: Azure-specific tool conversion

#### Bedrock (`connectors/bedrock/`)
- **BedrockLLM**: Main implementation class
- **bedrock_llm.py**: Core Bedrock integration
- **converter.py**: Request/response conversion
- **model_registry.py**: Bedrock model definitions
- **models.py**: Bedrock model enums
- **tool_converter.py**: Bedrock-specific tool conversion

#### Gemini (`connectors/gemini/`)
- **GeminiLLM**: Main implementation class
- **gemini_llm.py**: Core Gemini integration
- **converter.py**: Request/response conversion
- **model_registry.py**: Gemini model definitions
- **models.py**: Gemini model enums
- **tool_converter.py**: Gemini-specific tool conversion

### 10. Usage Examples

#### Basic Usage
```python
from core.llms import LLMFactory, AzureOpenAIConfig, LLMProvider

# Create configuration
config = AzureOpenAIConfig(
    provider=LLMProvider.AZURE_OPENAI,
    model_name="gpt-4o",
    api_key="your-api-key",
    endpoint="https://your-endpoint.openai.azure.com/",
    deployment_name="your-deployment",
    prompt="You are a helpful AI assistant.",
    dynamic_variables={"context": "customer support"}
)

# Create LLM instance
llm = LLMFactory.create_llm(config)

# Use the LLM
messages = [{"role": "user", "content": "Hello!"}]
response = await llm.get_answer(messages)
print(response.content)
```

#### With Dynamic Variables
```python
config = AzureOpenAIConfig(
    provider=LLMProvider.AZURE_OPENAI,
    model_name="gpt-4o",
    api_key="your-api-key",
    endpoint="https://your-endpoint.openai.azure.com/",
    deployment_name="your-deployment",
    prompt="Hello {{name}}, you are {{role}}. Current context: {{context}}.",
    dynamic_variables={
        "name": "Alice",
        "role": "software engineer",
        "context": "debugging session"
    }
)

# Variables are automatically replaced in system prompt
llm = LLMFactory.create_llm(config)
```

#### With Tools
```python
from core.tools.spec.tool_types import FunctionToolSpec

# Define a tool
weather_tool = FunctionToolSpec(
    id="weather_v1",
    tool_name="get_weather",
    description="Get current weather for a city",
    parameters=[...]
)

# Register tools
llm.register_tools([weather_tool], {"get_weather": get_weather_handler})

# Use with tool calling
messages = [{"role": "user", "content": "What's the weather in Paris?"}]
response = await llm.get_answer(messages)
# LLM will automatically call the weather tool if needed
```

#### Streaming
```python
messages = [{"role": "user", "content": "Tell me a story"}]
async for chunk in llm.get_stream(messages):
    print(chunk.content, end="", flush=True)
    if chunk.is_final:
        print(f"\nUsage: {chunk.usage}")
```

#### JSON Mode
```python
config = AzureOpenAIConfig(
    provider=LLMProvider.AZURE_OPENAI,
    model_name="gpt-4o",
    api_key="your-api-key",
    json_output=True,
    json_schema={"type": "object", "properties": {...}}
)

llm = LLMFactory.create_llm(config)
response = await llm.get_answer(messages)
# Response will be validated against the JSON schema
```

## Error Handling

The system provides comprehensive error handling:

```python
try:
    response = await llm.get_answer(messages)
except InputValidationError as e:
    print(f"Invalid input: {e}")
except ProviderError as e:
    print(f"Provider error: {e}")
except RateLimitError as e:
    print(f"Rate limited: {e}")
except JSONParsingError as e:
    print(f"JSON parsing failed: {e}")
except TimeoutError as e:
    print(f"Request timed out: {e}")
```

## Best Practices

1. **Configuration**: Always use typed configurations and validate before use
2. **Error Handling**: Wrap LLM calls in appropriate try-catch blocks
3. **Resource Management**: Use async context managers where available
4. **Tool Integration**: Register tools before making requests that might use them
5. **Streaming**: Use streaming for long responses to improve user experience
6. **JSON Mode**: Use JSON mode with schemas for structured outputs
7. **Dynamic Variables**: Use dynamic variables for context-dependent system prompts

## Future Enhancements

- [ ] Multi-region support and failover
- [ ] Advanced caching strategies
- [ ] Batch processing capabilities
- [ ] Custom model fine-tuning integration
- [ ] Enhanced telemetry and monitoring
- [ ] Advanced prompt engineering utilities
- [ ] Conversation memory and context management
- [ ] Advanced tool orchestration
- [ ] Model performance benchmarking
- [ ] Cost optimization features

## Integration Points

The LLM system integrates with:
- **Core Tools**: For function calling and tool execution
- **Core Logging**: For request/response logging and monitoring
- **Core Utils**: For circuit breaking and retry logic
- **External APIs**: Direct integration with provider APIs

## Testing

The system includes comprehensive testing:
- Unit tests for all core components
- Integration tests for provider connectors
- Tool integration tests
- Configuration validation tests
- Error handling tests

See `test_llm.py` for usage examples and test patterns.
