"""
Model Registry for LLM providers.

This module provides the base model management system.
Provider-specific registries are located in their respective connector subfolders:
- Azure OpenAI: connectors/azure/model_registry.py
- Bedrock: connectors/bedrock/model_registry.py
- Gemini: connectors/gemini/model_registry.py

This module provides:
- ModelMetadata: Complete specification for each model
- ModelFamily: Groups models with shared characteristics
- ModelRegistry: Central registry managing all models
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Any, Optional, List, Callable
from enum import Enum

from .enums import InputMediaType, OutputMediaType, LLMProvider


class ModelFamily(str, Enum):
    """Model families that share common characteristics"""
    # Azure OpenAI
    AZURE_GPT_4O = "azure_gpt_4o"
    AZURE_GPT_4 = "azure_gpt_4"
    AZURE_GPT_35 = "azure_gpt_35"
    
    # Bedrock
    BEDROCK_CLAUDE_3 = "bedrock_claude_3"
    BEDROCK_CLAUDE_35 = "bedrock_claude_35"
    
    # Gemini
    GEMINI_PRO = "gemini_pro"
    GEMINI_1_5 = "gemini_1_5"


@dataclass
class ModelMetadata:
    """Complete metadata for a specific model"""
    
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
    
    # Parameter support
    supports_temperature: bool = True
    supports_top_p: bool = True
    supports_frequency_penalty: bool = True
    supports_presence_penalty: bool = True
    supports_stop_sequences: bool = True
    
    # API-specific parameter mappings
    # Maps standard parameter names to model-specific API parameter names
    parameter_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Default parameters for this specific model
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Model-specific API quirks or requirements
    api_requirements: Dict[str, Any] = field(default_factory=dict)
    
    # Optional: Model-specific converter function
    converter_fn: Optional[Callable] = None
    
    # Pricing (optional, for cost tracking)
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None
    
    # Deprecation info
    is_deprecated: bool = False
    deprecation_date: Optional[str] = None
    replacement_model: Optional[str] = None


class ModelRegistry:
    """Registry for all supported models and their metadata"""
    
    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}
        self._families: Dict[ModelFamily, List[str]] = {}
    
    def register_model(self, metadata: ModelMetadata) -> None:
        """Register a model with its metadata"""
        self._models[metadata.model_name] = metadata
        
        # Add to family index
        if metadata.model_family not in self._families:
            self._families[metadata.model_family] = []
        self._families[metadata.model_family].append(metadata.model_name)
    
    def get_model(self, model_name: str) -> Optional[ModelMetadata]:
        """Get metadata for a specific model"""
        return self._models.get(model_name)
    
    def get_family_models(self, family: ModelFamily) -> List[str]:
        """Get all models in a specific family"""
        return self._families.get(family, [])
    
    def get_provider_models(self, provider: LLMProvider) -> List[str]:
        """Get all models for a specific provider"""
        return [
            name for name, meta in self._models.items()
            if meta.provider == provider
        ]
    
    def is_model_supported(self, model_name: str) -> bool:
        """Check if a model is supported"""
        return model_name in self._models
    
    def get_parameter_mapping(self, model_name: str, param_name: str) -> str:
        """Get the API-specific parameter name for a model"""
        metadata = self.get_model(model_name)
        if metadata and param_name in metadata.parameter_mappings:
            return metadata.parameter_mappings[param_name]
        return param_name  # Return original if no mapping exists
    
    def get_model_defaults(self, model_name: str) -> Dict[str, Any]:
        """Get default parameters for a model"""
        metadata = self.get_model(model_name)
        return metadata.default_parameters if metadata else {}
    
    def validate_parameters_for_model(self, model_name: str, parameters: Dict[str, Any]) -> List[str]:
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
        
        if "frequency_penalty" in parameters and not metadata.supports_frequency_penalty:
            issues.append(f"Model {model_name} does not support frequency_penalty parameter")
        
        if "presence_penalty" in parameters and not metadata.supports_presence_penalty:
            issues.append(f"Model {model_name} does not support presence_penalty parameter")
        
        # Check token limits
        if "max_tokens" in parameters:
            if parameters["max_tokens"] > metadata.max_output_tokens:
                issues.append(
                    f"max_tokens {parameters['max_tokens']} exceeds model limit "
                    f"{metadata.max_output_tokens}"
                )
        
        return issues
    
    def get_all_models(self) -> Dict[str, ModelMetadata]:
        """Get all registered models"""
        return self._models.copy()


# Global registry instance
_global_registry = None


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ModelRegistry()
        _initialize_registry(_global_registry)
    return _global_registry


def _initialize_registry(registry: ModelRegistry) -> None:
    """Initialize registry with all supported models from provider-specific registries"""
    # Lazy load model registrations from provider modules
    try:
        from .connectors.azure.model_registry import register_azure_models
        register_azure_models(registry)
    except ImportError:
        pass
    
    try:
        from .connectors.bedrock.model_registry import register_bedrock_models
        register_bedrock_models(registry)
    except ImportError:
        pass
    
    try:
        from .connectors.gemini.model_registry import register_gemini_models
        register_gemini_models(registry)
    except ImportError:
        pass


# Convenience functions
def get_model_metadata(model_name: str) -> Optional[ModelMetadata]:
    """Get metadata for a specific model"""
    return get_model_registry().get_model(model_name)


def validate_model_parameters(model_name: str, parameters: Dict[str, Any]) -> List[str]:
    """Validate parameters for a specific model"""
    return get_model_registry().validate_parameters_for_model(model_name, parameters)
