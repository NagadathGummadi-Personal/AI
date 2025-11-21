"""
LLM Factory for creating LLM instances.

This module provides a unified factory for creating LLM instances
based on model metadata and provider configuration.
"""

from typing import Dict, Any, Optional, List
from .base_llm import BaseLLM
from .model_registry import get_model_registry
from .connectors.openai_connector import OpenAIConnector
from .connectors.azure_connector import AzureConnector
from .implementations.openai_llm import OpenAILLM
from .implementations.azure_llm import AzureLLM
from ..spec.llm_types import ModelMetadata
from ..enum import LLMProvider
from ..exceptions import ModelNotFoundError, ConfigurationError


class LLMFactory:
    """
    Unified factory for creating LLM instances.
    
    Automatically selects the appropriate connector and LLM implementation
    based on the model metadata and provider configuration.
    
    Usage:
        # Create LLM by model name
        llm = LLMFactory.create_llm("gpt-4o", connector_config={"api_key": "sk-..."})
        
        # Create LLM from metadata
        metadata = registry.get_model("azure-gpt-4o")
        llm = LLMFactory.create_llm_from_metadata(metadata, connector_config={...})
    """
    
    @classmethod
    def create_llm(
        cls,
        model_name: str,
        connector_config: Dict[str, Any],
    ) -> BaseLLM:
        """
        Create an LLM instance by model name.
        
        Args:
            model_name: Name of the model (e.g., "gpt-4o", "azure-gpt-4o")
            connector_config: Configuration for the connector (api_key, endpoint, etc.)
            
        Returns:
            Configured LLM instance implementing ILLM
            
        Raises:
            ModelNotFoundError: If model is not registered
            ConfigurationError: If configuration is invalid
            
        Example:
            # OpenAI
            llm = LLMFactory.create_llm(
                "gpt-4o",
                connector_config={"api_key": "sk-..."}
            )
            
            # Azure
            llm = LLMFactory.create_llm(
                "azure-gpt-4o",
                connector_config={
                    "api_key": "...",
                    "endpoint": "https://my-resource.openai.azure.com",
                    "deployment_name": "gpt-4"
                }
            )
        """
        # Get model metadata from registry
        registry = get_model_registry()
        metadata = registry.get_model_or_raise(model_name)
        
        # Create LLM from metadata
        return cls.create_llm_from_metadata(metadata, connector_config)
    
    @classmethod
    def create_llm_from_metadata(
        cls,
        metadata: ModelMetadata,
        connector_config: Dict[str, Any],
    ) -> BaseLLM:
        """
        Create an LLM instance from model metadata.
        
        Args:
            metadata: Model metadata
            connector_config: Configuration for the connector
            
        Returns:
            Configured LLM instance
            
        Raises:
            ConfigurationError: If provider is not supported or config is invalid
            
        Example:
            metadata = ModelMetadata(...)
            llm = LLMFactory.create_llm_from_metadata(
                metadata,
                connector_config={"api_key": "..."}
            )
        """
        provider = metadata.provider
        
        if provider == LLMProvider.OPENAI:
            connector = OpenAIConnector(connector_config)
            return OpenAILLM(metadata, connector)
        
        elif provider == LLMProvider.AZURE:
            connector = AzureConnector(connector_config)
            return AzureLLM(metadata, connector)
        
        else:
            raise ConfigurationError(
                f"Unsupported provider: {provider}",
                provider=provider.value if hasattr(provider, 'value') else str(provider),
                details={"supported_providers": ["openai", "azure"]}
            )
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """
        List all available models.
        
        Returns:
            List of model names
            
        Example:
            models = LLMFactory.list_available_models()
            print(f"Available models: {models}")
        """
        registry = get_model_registry()
        return list(registry.get_all_models().keys())
    
    @classmethod
    def list_provider_models(cls, provider: LLMProvider) -> List[str]:
        """
        List all models for a specific provider.
        
        Args:
            provider: Provider to filter by
            
        Returns:
            List of model names
            
        Example:
            openai_models = LLMFactory.list_provider_models(LLMProvider.OPENAI)
        """
        registry = get_model_registry()
        return registry.get_provider_models(provider)
    
    @classmethod
    def get_model_metadata(cls, model_name: str) -> ModelMetadata:
        """
        Get metadata for a model without creating an LLM instance.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelMetadata
            
        Raises:
            ModelNotFoundError: If model not found
            
        Example:
            metadata = LLMFactory.get_model_metadata("gpt-4o")
            print(f"Max tokens: {metadata.max_output_tokens}")
        """
        registry = get_model_registry()
        return registry.get_model_or_raise(model_name)

