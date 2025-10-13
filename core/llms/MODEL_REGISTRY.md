# LLM Model Registry System

## Overview

The Model Registry provides a comprehensive, hierarchical system for managing models across different LLM providers. It handles model-specific capabilities, parameter mappings, API requirements, and validation.

## Architecture

```
┌─────────────────────────────────────┐
│       Model Registry                 │
│  (Global singleton instance)         │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
  ┌───▼───┐    ┌───▼────┐
  │ Model │    │  Model │
  │Family │    │Metadata│
  └───────┘    └────────┘
```

### Key Components

1. **ModelFamily**: Groups models with shared characteristics (e.g., GPT-4 family, Claude 3 family)
2. **ModelMetadata**: Complete specification for each model variant
3. **ModelRegistry**: Central registry managing all models

## Model Hierarchy

### Azure OpenAI
```
GPT-4o Family
├── gpt-4o (latest, multimodal, 128K context)
└── gpt-4o-mini (cost-optimized, multimodal)

GPT-4 Family  
├── gpt-4-turbo (128K context)
└── gpt-4 (8K context)

GPT-3.5 Family
├── gpt-3.5-turbo (latest, 16K)
└── gpt-3.5-turbo-16k (deprecated)
```

### Bedrock (Claude)
```
Claude 3.5 Family
└── claude-3.5-sonnet (latest)

Claude 3 Family
├── claude-3-opus (most capable)
├── claude-3-sonnet (balanced)
└── claude-3-haiku (fastest)
```

### Gemini
```
Gemini 1.5 Family
├── gemini-1.5-pro (2M context)
└── gemini-1.5-flash (1M context, faster)

Gemini Pro Family
├── gemini-pro
└── gemini-pro-vision
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
