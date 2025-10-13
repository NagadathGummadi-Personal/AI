# LLM Model Registry System

## Overview

The Model Registry provides a comprehensive, hierarchical system for managing models across different LLM providers (Azure OpenAI, Amazon Bedrock, Google Gemini). It handles model-specific capabilities, parameter mappings, API requirements, validation, cost tracking, and deprecation management.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Model Registry System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Model         │  │   Model         │  │   Model         │  │
│  │   Registry      │  │   Metadata      │  │   Family        │  │
│  │   (Singleton)   │  │   (Complete     │  │   (Grouping)    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Provider-Specific Registries                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │  │
│  │  │   Azure      │  │   Bedrock    │  │   Gemini     │       │  │
│  │  │  OpenAI      │  │  (Claude)    │  │  Models      │       │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **ModelRegistry**: Central singleton registry managing all models
2. **ModelMetadata**: Complete specification for each model variant
3. **ModelFamily**: Groups models with shared characteristics
4. **Provider-Specific Registries**: Azure, Bedrock, and Gemini model definitions

## Model Hierarchy

### Azure OpenAI
```
GPT-4o Family (ModelFamily.AZURE_GPT_4O)
├── gpt-4o (latest, multimodal, 128K context, function calling)
└── gpt-4o-mini (cost-optimized, multimodal, function calling)

GPT-4 Family (ModelFamily.AZURE_GPT_4)
├── gpt-4-turbo (128K context, function calling)
└── gpt-4 (8K context, function calling)

GPT-3.5 Family (ModelFamily.AZURE_GPT_35)
├── gpt-3.5-turbo (latest, 16K context, function calling)
└── gpt-3.5-turbo-16k (deprecated, 16K context)
```

### Bedrock (Claude)
```
Claude 3.5 Family (ModelFamily.BEDROCK_CLAUDE_35)
└── claude-3.5-sonnet (latest, 200K context, function calling)

Claude 3 Family (ModelFamily.BEDROCK_CLAUDE_3)
├── claude-3-opus (most capable, 200K context, function calling)
├── claude-3-sonnet (balanced, 200K context, function calling)
└── claude-3-haiku (fastest, 200K context, function calling)
```

### Gemini
```
Gemini 1.5 Family (ModelFamily.GEMINI_1_5)
├── gemini-1.5-pro (2M context, multimodal, function calling)
└── gemini-1.5-flash (1M context, multimodal, faster, function calling)

Gemini Pro Family (ModelFamily.GEMINI_PRO)
├── gemini-pro (text-only, function calling)
└── gemini-pro-vision (multimodal, function calling)
```

## Technical Implementation

### ModelMetadata Class

Complete model specification with comprehensive metadata:

```python
@dataclass
class ModelMetadata:
    # Basic identification
    model_name: str                    # Internal model identifier
    provider: LLMProvider              # Provider enum (AZURE_OPENAI, BEDROCK, GEMINI)
    model_family: ModelFamily          # Family grouping
    display_name: str                  # Human-readable name

    # Input/Output capabilities
    supported_input_types: Set[InputMediaType] = field(default_factory=set)
    supported_output_types: Set[OutputMediaType] = field(default_factory=set)
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False

    # Token limits
    max_context_length: int = 128000   # Maximum input tokens
    max_output_tokens: int = 4096      # Maximum output tokens
    max_input_tokens: int = 128000     # Maximum input tokens (may differ from context)

    # Parameter support flags
    supports_temperature: bool = True
    supports_top_p: bool = True
    supports_frequency_penalty: bool = True
    supports_presence_penalty: bool = True
    supports_stop_sequences: bool = True

    # Provider-specific parameter mappings
    parameter_mappings: Dict[str, str] = field(default_factory=dict)
    # Example: {"max_tokens": "max_output_tokens"} for Gemini

    # Default parameters for this model
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    # Example: {"temperature": 0.7, "max_tokens": 4096}

    # API requirements and quirks
    api_requirements: Dict[str, Any] = field(default_factory=dict)
    # Example: {"uses_deployment_name": True, "supports_response_format": True}

    # Optional converter function for custom request formatting
    converter_fn: Optional[Callable] = None

    # Cost tracking (for billing and optimization)
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None

    # Deprecation management
    is_deprecated: bool = False
    deprecation_date: Optional[str] = None
    replacement_model: Optional[str] = None
```

### ModelRegistry Class

Central registry implementation with comprehensive model management:

```python
class ModelRegistry:
    """Central registry managing all models and their metadata"""

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}      # model_name -> metadata
        self._families: Dict[ModelFamily, List[str]] = {} # family -> model_names

    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a new model with validation"""
        self._models[metadata.model_name] = metadata

        # Update family index
        if metadata.model_family not in self._families:
            self._families[metadata.model_family] = []
        self._families[metadata.model_family].append(metadata.model_name)

    def get_model(self, model_name: str) -> Optional[ModelMetadata]:
        """Retrieve metadata for a specific model"""

    def get_family_models(self, family: ModelFamily) -> List[str]:
        """Get all model names in a specific family"""

    def get_provider_models(self, provider: LLMProvider) -> List[str]:
        """Get all model names for a specific provider"""

    def is_model_supported(self, model_name: str) -> bool:
        """Check if a model is registered"""

    def get_parameter_mapping(self, model_name: str, param_name: str) -> str:
        """Get provider-specific parameter name"""
        metadata = self.get_model(model_name)
        return metadata.parameter_mappings.get(param_name, param_name)

    def get_model_defaults(self, model_name: str) -> Dict[str, Any]:
        """Get model-specific default parameters"""

    def validate_parameters_for_model(
        self, model_name: str, parameters: Dict[str, Any]
    ) -> List[str]:
        """Validate parameters against model capabilities and limits"""
```

### Parameter Validation System

Comprehensive parameter validation with detailed error reporting:

```python
def validate_parameters_for_model(
    self, model_name: str, parameters: Dict[str, Any]
) -> List[str]:
    """Validate parameters for a specific model, return list of issues"""
    issues = []
    metadata = self.get_model(model_name)

    if not metadata:
        issues.append(f"Model {model_name} not found in registry")
        return issues

    # Check unsupported parameters
    if "temperature" in parameters and not metadata.supports_temperature:
        issues.append(f"Model {model_name} does not support temperature parameter")

    if "top_p" in parameters and not metadata.supports_top_p:
        issues.append(f"Model {model_name} does not support top_p parameter")

    # Check token limits
    if "max_tokens" in parameters:
        if parameters["max_tokens"] > metadata.max_output_tokens:
            issues.append(
                f"max_tokens {parameters['max_tokens']} exceeds model limit "
                f"{metadata.max_output_tokens}"
            )

    # Check context limits (if applicable)
    # ... additional validations

    return issues
```

### Model Families

Hierarchical model organization for related models:

```python
class ModelFamily(str, Enum):
    """Model families that share common characteristics"""

    # Azure OpenAI Families
    AZURE_GPT_4O = "azure_gpt_4o"      # Latest GPT-4o models
    AZURE_GPT_4 = "azure_gpt_4"        # GPT-4 models
    AZURE_GPT_4_1 = "azure_gpt_4_1"    # GPT-4.1 models
    AZURE_GPT_4_1_MINI = "azure_gpt_4_1_mini"  # GPT-4.1 Mini
    AZURE_GPT_35 = "azure_gpt_35"      # GPT-3.5 models

    # Bedrock (Claude) Families
    BEDROCK_CLAUDE_3 = "bedrock_claude_3"      # Claude 3.x models
    BEDROCK_CLAUDE_35 = "bedrock_claude_35"    # Claude 3.5.x models

    # Gemini Families
    GEMINI_PRO = "gemini_pro"          # Gemini Pro models
    GEMINI_1_5 = "gemini_1_5"          # Gemini 1.5 models
```

### Provider-Specific Registries

Each provider maintains its own model registry with provider-specific logic:

#### Azure OpenAI (`connectors/azure/model_registry.py`)
```python
def register_azure_models(registry: ModelRegistry) -> None:
    """Register all Azure OpenAI models"""

    # GPT-4o models
    registry.register_model(ModelMetadata(
        model_name="gpt-4o",
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_4O,
        display_name="GPT-4o",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=16384,
        parameter_mappings={"max_tokens": "max_tokens"},
        api_requirements={"uses_deployment_name": True},
        cost_per_1k_input_tokens=0.005,
        cost_per_1k_output_tokens=0.015,
    ))

    # GPT-4o-mini
    registry.register_model(ModelMetadata(
        model_name="gpt-4o-mini",
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_4O,
        display_name="GPT-4o Mini",
        # ... similar configuration but optimized for cost
    ))
```

#### Bedrock (`connectors/bedrock/model_registry.py`)
```python
def register_bedrock_models(registry: ModelRegistry) -> None:
    """Register all Bedrock models (Claude)"""

    registry.register_model(ModelMetadata(
        model_name="claude-3-5-sonnet",
        provider=LLMProvider.BEDROCK,
        model_family=ModelFamily.BEDROCK_CLAUDE_35,
        display_name="Claude 3.5 Sonnet",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=200000,
        max_output_tokens=4096,
        parameter_mappings={"max_tokens": "max_tokens"},
        api_requirements={"requires_region": True},
        cost_per_1k_input_tokens=0.003,
        cost_per_1k_output_tokens=0.015,
    ))
```

#### Gemini (`connectors/gemini/model_registry.py`)
```python
def register_gemini_models(registry: ModelRegistry) -> None:
    """Register all Gemini models"""

    registry.register_model(ModelMetadata(
        model_name="gemini-1.5-pro",
        provider=LLMProvider.GEMINI,
        model_family=ModelFamily.GEMINI_1_5,
        display_name="Gemini 1.5 Pro",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.VIDEO},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=2097152,  # 2M tokens
        max_output_tokens=8192,
        parameter_mappings={"max_tokens": "max_output_tokens"},
        api_requirements={"requires_project_id": True},
        cost_per_1k_input_tokens=0.00125,
        cost_per_1k_output_tokens=0.005,
    ))
```

### Parameter Mapping System

Handles provider-specific parameter name differences:

```python
# Example parameter mappings
AZURE_MAPPINGS = {
    "max_tokens": "max_tokens",
    "temperature": "temperature",
    "top_p": "top_p",
}

BEDROCK_MAPPINGS = {
    "max_tokens": "max_tokens",
    "temperature": "temperature",
    "top_p": "top_p",
}

GEMINI_MAPPINGS = {
    "max_tokens": "max_output_tokens",  # Different parameter name
    "temperature": "temperature",
    "top_p": "top_p",
}
```

### Cost Tracking

Built-in cost calculation for billing and optimization:

```python
def calculate_request_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Calculate cost for a specific request"""
    metadata = get_model_metadata(model_name)
    if not metadata:
        return 0.0

    input_cost = (input_tokens / 1000) * (metadata.cost_per_1k_input_tokens or 0)
    output_cost = (output_tokens / 1000) * (metadata.cost_per_1k_output_tokens or 0)

    return input_cost + output_cost

# Usage
cost = calculate_request_cost("gpt-4o", input_tokens=1000, output_tokens=500)
print(f"Estimated cost: ${cost:.4f}")
```

### Deprecation Management

Track deprecated models and provide migration guidance:

```python
# Example deprecated model
registry.register_model(ModelMetadata(
    model_name="gpt-3.5-turbo-16k",
    provider=LLMProvider.AZURE_OPENAI,
    model_family=ModelFamily.AZURE_GPT_35,
    display_name="GPT-3.5 Turbo 16K (Deprecated)",
    # ... capabilities
    is_deprecated=True,
    deprecation_date="2024-06-01",
    replacement_model="gpt-3.5-turbo",  # Suggest replacement
))
```

### API Requirements

Handle provider-specific API quirks and requirements:

```python
# Azure OpenAI requirements
AZURE_REQUIREMENTS = {
    "uses_deployment_name": True,      # Requires deployment name
    "supports_response_format": True,  # Supports JSON mode
    "requires_api_version": True,      # Needs API version
}

# Bedrock requirements
BEDROCK_REQUIREMENTS = {
    "requires_region": True,           # Needs AWS region
    "supports_batch_api": True,        # Supports batch processing
}

# Gemini requirements
GEMINI_REQUIREMENTS = {
    "requires_project_id": True,       # Needs Google Cloud project
    "supports_system_instruction": True, # Supports system messages
}
```

### Integration with Converters

Automatic parameter mapping in request conversion:

```python
def convert_request_for_model(
    messages: List[Dict],
    model_name: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Convert request using model registry metadata"""
    metadata = get_model_metadata(model_name)

    # Map parameters to provider-specific names
    converted_params = {}
    for param, value in parameters.items():
        api_param = metadata.parameter_mappings.get(param, param)
        converted_params[api_param] = value

    # Handle API requirements
    if metadata.api_requirements.get("supports_response_format"):
        converted_params["response_format"] = {"type": "json_object"}

    return converted_params
```

## Advanced Features

### Model Validation System

The registry provides comprehensive model and parameter validation:

```python
# Validate model exists and parameters are compatible
issues = validate_model_parameters("gpt-4o", {
    "temperature": 0.7,
    "max_tokens": 20000,  # This will fail - exceeds 16384 limit
    "frequency_penalty": 0.5
})

for issue in issues:
    print(f"⚠️ {issue}")
# Output: max_tokens 20000 exceeds model limit 16384
```

### Cost Optimization

Use model metadata for cost-aware model selection:

```python
def select_cost_effective_model(task: str, max_tokens: int) -> str:
    """Select the most cost-effective model for a task"""
    registry = get_model_registry()

    # Get all available models
    all_models = registry.get_all_models()

    # Filter by capability and token requirements
    candidates = []
    for model_name, metadata in all_models.items():
        if (metadata.supports_function_calling and
            metadata.max_output_tokens >= max_tokens and
            not metadata.is_deprecated):

            # Calculate relative cost (lower is better)
            cost_score = (metadata.cost_per_1k_input_tokens or 0) + \
                        (metadata.cost_per_1k_output_tokens or 0)
            candidates.append((model_name, cost_score))

    # Return cheapest option
    return min(candidates, key=lambda x: x[1])[0] if candidates else None

# Usage
best_model = select_cost_effective_model("complex_task", 8000)
print(f"Recommended model: {best_model}")
```

### Model Migration Support

Handle deprecated models with automatic migration:

```python
def migrate_to_supported_model(model_name: str) -> str:
    """Get replacement model for deprecated models"""
    metadata = get_model_metadata(model_name)

    if metadata and metadata.is_deprecated:
        replacement = metadata.replacement_model
        if replacement:
            print(f"⚠️ Model {model_name} is deprecated as of {metadata.deprecation_date}")
            print(f"Consider migrating to: {replacement}")
            return replacement

    return model_name

# Usage
updated_model = migrate_to_supported_model("gpt-3.5-turbo-16k")
```

## Usage

### 1. Get Model Metadata

```python
from core.llms import get_model_metadata

# Get comprehensive metadata for a model
metadata = get_model_metadata("gpt-4o")

print(f"Model: {metadata.display_name}")
print(f"Family: {metadata.model_family}")
print(f"Max tokens: {metadata.max_output_tokens}")
print(f"Supports vision: {metadata.supports_vision}")
print(f"Cost per 1K input: ${metadata.cost_per_1k_input_tokens}")
```

### 2. Validate Parameters

```python
from core.llms import validate_model_parameters

parameters = {
    "temperature": 0.7,
    "max_tokens": 20000,  # Exceeds limit
    "frequency_penalty": 0.5
}

issues = validate_model_parameters("gpt-3.5-turbo", parameters)
for issue in issues:
    print(f"⚠️ {issue}")
# Output: max_tokens 20000 exceeds model limit 4096
```

### 3. Check Model Capabilities

```python
from core.llms import get_model_metadata

metadata = get_model_metadata("gpt-3.5-turbo-16k")

if metadata.is_deprecated:
    print(f"⚠️ This model is deprecated as of {metadata.deprecation_date}")
    print(f"Replacement: {metadata.replacement_model}")

# Check specific capabilities
if metadata.supports_function_calling:
    print("✓ Function calling supported")
if metadata.supports_vision:
    print("✓ Vision supported")
```

### 4. Get Models by Family

```python
from core.llms import get_model_registry, ModelFamily

registry = get_model_registry()

# Get all GPT-4o models
gpt4o_models = registry.get_family_models(ModelFamily.AZURE_GPT_4O)
print(f"GPT-4o models: {gpt4o_models}")

# Get all Claude 3 models
claude3_models = registry.get_family_models(ModelFamily.BEDROCK_CLAUDE_3)
print(f"Claude 3 models: {claude3_models}")
```

### 5. Get Models by Provider

```python
from core.llms import get_model_registry, LLMProvider

registry = get_model_registry()

# Get all Azure OpenAI models
azure_models = registry.get_provider_models(LLMProvider.AZURE_OPENAI)
for model in azure_models:
    metadata = registry.get_model(model)
    print(f"{model}: {metadata.display_name}")
```

### 6. Parameter Mapping

The registry handles provider-specific parameter naming:

```python
from core.llms import get_model_metadata

metadata = get_model_metadata("gpt-4o")

# Get API-specific parameter name
api_param = metadata.parameter_mappings.get("max_tokens", "max_tokens")
# For Azure OpenAI: "max_tokens" -> "max_tokens" (same)
# For Gemini: "max_tokens" -> "max_output_tokens" (different!)

# Check API requirements
if metadata.api_requirements.get("uses_deployment_name"):
    print("This model requires a deployment name")
```

### 7. Cost Tracking

```python
from core.llms import get_model_metadata

def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for a request"""
    metadata = get_model_metadata(model_name)
    if not metadata:
        return 0.0
    
    input_cost = (input_tokens / 1000) * (metadata.cost_per_1k_input_tokens or 0)
    output_cost = (output_tokens / 1000) * (metadata.cost_per_1k_output_tokens or 0)
    
    return input_cost + output_cost

# Example
cost = calculate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
print(f"Estimated cost: ${cost:.4f}")
```

## Model-Specific Features

### API Requirements

Models can specify unique API requirements:

```python
{
    "uses_deployment_name": True,      # Azure-specific
    "requires_api_version": True,      # Azure-specific
    "supports_response_format": True,  # JSON mode support
    "max_batch_size": 20,              # Batch API limits
}
```

### Parameter Mappings

Different providers use different parameter names:

| Standard Param | Azure OpenAI | Bedrock | Gemini |
|---------------|--------------|---------|---------|
| max_tokens | max_tokens | max_tokens | max_output_tokens |
| temperature | temperature | temperature | temperature |
| top_p | top_p | top_p | top_p |
| stop | stop | stop_sequences | stop_sequences |

The registry automatically handles these mappings.

## Adding New Models

To add a new model:

1. Add model constant to `constants.py`
2. Add model to provider's `models.py`
3. Create `ModelMetadata` entry with complete specifications
4. Update `get_<provider>_model_metadata()` function

Example:

```python
ModelMetadata(
    model_name="new-model-name",
    provider=LLMProvider.AZURE_OPENAI,
    model_family=ModelFamily.AZURE_GPT_4O,
    display_name="New Model",
    supported_input_types={InputMediaType.TEXT},
    supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
    supports_streaming=True,
    supports_function_calling=True,
    max_context_length=128000,
    max_output_tokens=4096,
    parameter_mappings={
        "max_tokens": "max_tokens",
        # Add any provider-specific mappings
    },
    default_parameters={
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    api_requirements={
        # Add any special requirements
    },
    cost_per_1k_input_tokens=0.01,
    cost_per_1k_output_tokens=0.03,
)
```

## Benefits

1. **Type Safety**: Complete metadata validation
2. **Consistency**: Unified interface across providers
3. **Flexibility**: Easy to add new models or providers
4. **Validation**: Automatic parameter validation
5. **Cost Tracking**: Built-in pricing information
6. **Deprecation Management**: Track deprecated models
7. **API Compatibility**: Handle provider-specific quirks

## Integration with Converters

Converters automatically use the model registry:

```python
# In converter
metadata = get_model_metadata(model_name)

# Check API requirements
if metadata.api_requirements.get("supports_response_format"):
    request_params["response_format"] = {"type": "json_object"}

# Use parameter mappings
for param, value in params.items():
    api_param = metadata.parameter_mappings.get(param, param)
    request_params[api_param] = value
```

## Future Enhancements

- [ ] Model performance benchmarks
- [ ] Rate limit tracking per model
- [ ] Regional availability
- [ ] Model versioning and updates
- [ ] Custom model registration (for fine-tuned models)
