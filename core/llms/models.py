"""
Model definitions and capabilities for LLM providers.

This module provides the base ModelCapabilities class and helper functions.
Provider-specific model definitions are located in their respective connector subfolders:
- Azure OpenAI: connectors/azure/models.py
- Bedrock: connectors/bedrock/models.py
- Gemini: connectors/gemini/models.py
"""

from typing import Dict, Set, Any, Optional
from dataclasses import dataclass

from .enums import InputMediaType, OutputMediaType, LLMProvider
from .constants import (
    AZURE_OPENAI_MODEL,
    BEDROCK_MODEL,
    GEMINI_MODEL,
    MODEL_CAPABILITIES,
    MODEL_PARAMETER_DEFAULTS,
)


@dataclass
class ModelCapabilities:
    """Capabilities for a specific model"""

    # Input/output types supported
    supported_input_types: Set[InputMediaType]
    supported_output_types: Set[OutputMediaType]

    # Parameter support
    supports_temperature: bool = True
    supports_max_tokens: bool = True
    supports_top_p: bool = True
    supports_frequency_penalty: bool = True
    supports_presence_penalty: bool = True
    supports_stop_sequences: bool = True
    supports_json_mode: bool = False
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False

    # Model-specific limits
    max_context_length: int = 128000
    max_output_tokens: int = 4096

    # Provider-specific metadata
    provider: LLMProvider = None


def _get_all_model_capabilities() -> Dict[str, ModelCapabilities]:
    """Lazy loading of all model capabilities from provider modules."""
    all_capabilities = {}
    
    # Load Azure OpenAI models
    try:
        from .connectors.azure.models import AZURE_MODEL_CAPABILITIES
        all_capabilities.update(AZURE_MODEL_CAPABILITIES)
    except ImportError:
        pass
    
    # Load Bedrock models
    try:
        from .connectors.bedrock.models import BEDROCK_MODEL_CAPABILITIES
        all_capabilities.update(BEDROCK_MODEL_CAPABILITIES)
    except ImportError:
        pass
    
    # Load Gemini models
    try:
        from .connectors.gemini.models import GEMINI_MODEL_CAPABILITIES
        all_capabilities.update(GEMINI_MODEL_CAPABILITIES)
    except ImportError:
        pass
    
    return all_capabilities


def _get_all_model_parameter_defaults() -> Dict[str, Dict[str, Any]]:
    """Lazy loading of all model parameter defaults from provider modules."""
    all_defaults = {}
    
    # Load Azure OpenAI defaults
    try:
        from .connectors.azure.models import AZURE_MODEL_PARAMETER_DEFAULTS
        all_defaults.update(AZURE_MODEL_PARAMETER_DEFAULTS)
    except ImportError:
        pass
    
    # Load Bedrock defaults
    try:
        from .connectors.bedrock.models import BEDROCK_MODEL_PARAMETER_DEFAULTS
        all_defaults.update(BEDROCK_MODEL_PARAMETER_DEFAULTS)
    except ImportError:
        pass
    
    # Load Gemini defaults
    try:
        from .connectors.gemini.models import GEMINI_MODEL_PARAMETER_DEFAULTS
        all_defaults.update(GEMINI_MODEL_PARAMETER_DEFAULTS)
    except ImportError:
        pass
    
    return all_defaults


def get_model_capabilities(model_name: str) -> Optional[ModelCapabilities]:
    """Get capabilities for a specific model"""
    all_capabilities = _get_all_model_capabilities()
    return all_capabilities.get(model_name)




# Re-export model enums and capabilities for backward compatibility
def __getattr__(name):
    """Lazy import of model enums and capabilities for backward compatibility."""
    

    if name == AZURE_OPENAI_MODEL:
        from .connectors.azure.models import AzureOpenAIModel
        return AzureOpenAIModel
    elif name == BEDROCK_MODEL:
        from .connectors.bedrock.models import BedrockModel
        return BedrockModel
    elif name == GEMINI_MODEL:
        from .connectors.gemini.models import GeminiModel
        return GeminiModel
    elif name == MODEL_CAPABILITIES:
        # For backward compatibility
        return _get_all_model_capabilities()
    elif name == MODEL_PARAMETER_DEFAULTS:
        # For backward compatibility
        return _get_all_model_parameter_defaults()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Import model enums at module level for better IDE support and type checking
# These will be None if the provider modules are not available, but __getattr__ handles the fallback
try:
    from .connectors.azure.models import AzureOpenAIModel
except ImportError:
    AzureOpenAIModel = None

try:
    from .connectors.bedrock.models import BedrockModel
except ImportError:
    BedrockModel = None

try:
    from .connectors.gemini.models import GeminiModel
except ImportError:
    GeminiModel = None

# Model capabilities and defaults
MODEL_CAPABILITIES = _get_all_model_capabilities()
MODEL_PARAMETER_DEFAULTS = _get_all_model_parameter_defaults()