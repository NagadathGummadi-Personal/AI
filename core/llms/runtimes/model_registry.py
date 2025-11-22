"""
Model Registry for LLM Subsystem.

This module provides a central registry for managing model metadata.
Similar to a factory but focused on metadata management.
"""

from typing import Dict, List, Optional
from ..spec.llm_types import ModelMetadata
from ..enum import LLMProvider, ModelFamily
from ..exceptions import ModelNotFoundError
from ..constants import LOG_REGISTERING_MODEL, LOG_MODEL_REGISTERED


class ModelRegistry:
    """
    Central registry for LLM model metadata.
    
    Manages registration, lookup, and querying of model metadata.
    Follows singleton pattern - use get_model_registry() to access.
    
    Example:
        registry = get_model_registry()
        
        # Register a model
        registry.register_model(metadata)
        
        # Look up a model
        metadata = registry.get_model("gpt-4o")
        
        # List models by provider
        openai_models = registry.get_provider_models(LLMProvider.OPENAI)
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._models: Dict[str, ModelMetadata] = {}
        self._initialized = False
    
    def register_model(self, metadata: ModelMetadata) -> None:
        """
        Register a model with the registry.
        
        Args:
            metadata: Model metadata to register
            
        Raises:
            ValueError: If model is already registered
            
        Example:
            metadata = ModelMetadata(
                model_name="gpt-4o",
                provider=LLMProvider.OPENAI,
                ...
            )
            registry.register_model(metadata)
        """
        if metadata.model_name in self._models:
            raise ValueError(
                f"Model already registered: {metadata.model_name}"
            )
        
        self._models[metadata.model_name] = metadata
    
    def get_model(self, model_name: str) -> Optional[ModelMetadata]:
        """
        Get metadata for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelMetadata if found, None otherwise
            
        Example:
            metadata = registry.get_model("gpt-4o")
            if metadata:
                print(f"Max tokens: {metadata.max_output_tokens}")
        """
        self._ensure_initialized()
        return self._models.get(model_name)
    
    def get_model_or_raise(self, model_name: str) -> ModelMetadata:
        """
        Get metadata for a model, raise if not found.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelMetadata
            
        Raises:
            ModelNotFoundError: If model not found
            
        Example:
            metadata = registry.get_model_or_raise("gpt-4o")
        """
        self._ensure_initialized()
        metadata = self._models.get(model_name)
        if not metadata:
            raise ModelNotFoundError(
                f"Model not found: {model_name}",
                model_name=model_name,
                details={"available_models": list(self._models.keys())}
            )
        return metadata
    
    def get_all_models(self) -> Dict[str, ModelMetadata]:
        """
        Get all registered models.
        
        Returns:
            Dictionary mapping model names to metadata
            
        Example:
            all_models = registry.get_all_models()
            for name, metadata in all_models.items():
                print(f"{name}: {metadata.display_name}")
        """
        self._ensure_initialized()
        return self._models.copy()
    
    def get_provider_models(self, provider: LLMProvider) -> List[str]:
        """
        Get all models for a specific provider.
        
        Args:
            provider: Provider identifier
            
        Returns:
            List of model names
            
        Example:
            openai_models = registry.get_provider_models(LLMProvider.OPENAI)
            print(f"OpenAI models: {openai_models}")
        """
        self._ensure_initialized()
        return [
            name for name, meta in self._models.items()
            if meta.provider == provider
        ]
    
    def get_family_models(self, family: ModelFamily) -> List[str]:
        """
        Get all models in a specific family.
        
        Args:
            family: Model family identifier
            
        Returns:
            List of model names
            
        Example:
            gpt4_models = registry.get_family_models(ModelFamily.GPT_4_TURBO)
        """
        self._ensure_initialized()
        return [
            name for name, meta in self._models.items()
            if meta.model_family == family
        ]
    
    def list_all_providers(self) -> List[LLMProvider]:
        """
        List all providers that have registered models.
        
        Returns:
            List of provider enums
        """
        self._ensure_initialized()
        providers = set(meta.provider for meta in self._models.values())
        return sorted(providers, key=lambda p: p if isinstance(p, str) else p.value)
    
    def list_all_families(self) -> List[ModelFamily]:
        """
        List all model families that have registered models.
        
        Returns:
            List of model family enums
        """
        self._ensure_initialized()
        families = set(meta.model_family for meta in self._models.values())
        return sorted(families, key=lambda f: f if isinstance(f, str) else f.value)
    
    def get_model_count(self) -> int:
        """
        Get total number of registered models.
        
        Returns:
            Count of registered models
        """
        self._ensure_initialized()
        return len(self._models)
    
    def _ensure_initialized(self) -> None:
        """
        Ensure registry is initialized with provider models.
        
        Lazily loads model registrations from provider modules.
        """
        if self._initialized:
            return
        
        # Register models from new providers structure
        try:
            from ..providers.azure.models.gpt41_mini import GPT41MiniMetadata
            from ..spec.llm_types import ModelMetadata
            from ..enum import LLMProvider, ModelFamily, InputMediaType, OutputMediaType, LLMType
            from ..constants import (
                PARAM_MAX_TOKENS, PARAM_MAX_COMPLETION_TOKENS,
                PARAM_TOP_P, PARAM_FREQUENCY_PENALTY, PARAM_PRESENCE_PENALTY, PARAM_STOP,
                API_REQ_USES_DEPLOYMENT_NAME, API_REQ_REQUIRES_API_KEY,
                API_REQ_REQUIRES_ENDPOINT, API_REQ_REQUIRES_API_VERSION,
                API_REQ_SUPPORTS_STREAMING,
            )
            
            # Register Azure GPT-4.1 Mini
            metadata = ModelMetadata(
                model_name=GPT41MiniMetadata.NAME,
                provider=LLMProvider.AZURE,
                model_family=ModelFamily.AZURE_GPT_4_1_MINI,
                display_name=GPT41MiniMetadata.DISPLAY_NAME,
                llm_type=LLMType.CHAT,
                supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
                supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON, OutputMediaType.AUDIO, OutputMediaType.IMAGE},
                supports_streaming=GPT41MiniMetadata.SUPPORTS_STREAMING,
                supports_function_calling=GPT41MiniMetadata.SUPPORTS_FUNCTION_CALLING,
                supports_vision=GPT41MiniMetadata.SUPPORTS_VISION,
                supports_json_mode=GPT41MiniMetadata.SUPPORTS_JSON_MODE,
                max_context_length=GPT41MiniMetadata.MAX_CONTEXT_LENGTH,
                max_output_tokens=GPT41MiniMetadata.MAX_TOKENS,
                max_input_tokens=GPT41MiniMetadata.MAX_INPUT_TOKENS,
                parameter_mappings=GPT41MiniMetadata.PARAMETER_MAPPINGS,
                default_parameters=GPT41MiniMetadata.DEFAULT_PARAMETERS,
                parameter_ranges=GPT41MiniMetadata.PARAMETER_RANGES,
                supported_parameters=GPT41MiniMetadata.SUPPORTED_PARAMS,
                api_requirements={
                    API_REQ_USES_DEPLOYMENT_NAME: True,
                    API_REQ_REQUIRES_API_KEY: True,
                    API_REQ_REQUIRES_ENDPOINT: True,
                    API_REQ_REQUIRES_API_VERSION: True,
                    API_REQ_SUPPORTS_STREAMING: True,
                },
                cost_per_1k_input_tokens=GPT41MiniMetadata.COST_PER_1K_INPUT,
                cost_per_1k_output_tokens=GPT41MiniMetadata.COST_PER_1K_OUTPUT,
                is_deprecated=False,
            )
            self.register_model(metadata)
        except ImportError:
            pass  # Azure GPT-4.1 Mini not available
        
        # TODO: Add OpenAI models when migrated
        # TODO: Add other Azure models when implemented
        
        self._initialized = True


# Singleton instance
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """
    Get the global model registry instance (singleton).
    
    Returns:
        Global ModelRegistry instance
        
    Example:
        registry = get_model_registry()
        metadata = registry.get_model("gpt-4o")
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_registry() -> None:
    """
    Reset the global registry (primarily for testing).
    
    Example:
        reset_registry()  # Clear all registrations
    """
    global _registry
    _registry = None

