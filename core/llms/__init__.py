"""
LLM Specification System (v1.0.0)

This module provides a unified and extensible interface across LLM providers
(Azure OpenAI, Amazon Bedrock, and Gemini) with support for sync/async + streaming,
multi-modal input/output validation, JSON-structured responses, and seamless
integration with the existing tools architecture.

Core components:
- InputMediaType: Enumeration for input types (Text, Image, Audio, Video, Document, Multimodal)
- OutputMediaType: Enumeration for output types (Text, Audio, Image, JSON, Embedding)
- LLMProvider: Enumeration for providers (Azure OpenAI, Bedrock, Gemini)
- LLMType: Enumeration for LLM types (Chat, Completion, Embedding, Multimodal)
- BaseLLMConfig: Base configuration class for all providers
- AzureOpenAIConfig: Configuration for Azure OpenAI
- BedrockConfig: Configuration for Amazon Bedrock
- GeminiConfig: Configuration for Google Gemini
- LLMResponse: Response object with content and usage
- LLMStreamChunk: Streaming chunk object
- ILLM: Interface for LLM implementations
- BaseLLM: Base class for LLM providers
- AzureLLM: Azure OpenAI implementation
- BedrockLLM: Amazon Bedrock implementation
- GeminiLLM: Google Gemini implementation
- LLMFactory: Factory for creating LLM instances
- Exception classes for error handling
"""

from typing import List, Optional

# Enums and types
from .enums import (
    InputMediaType,
    OutputMediaType,
    LLMProvider,
    LLMType,
    MessageRole,
)

# Configuration classes
from .configs import (
    BaseLLMConfig,
    AzureOpenAIConfig,
    BedrockConfig,
    GeminiConfig,
    create_llm_config,
)

# Response models
from .interfaces import (
    LLMResponse,
    LLMStreamChunk,
)

# Base classes and interfaces
from .base_llm import BaseLLM
from .interfaces import ILLM

# Provider implementations
from .connectors.azure.azure_llm import AzureLLM
from .connectors.bedrock.bedrock_llm import BedrockLLM
from .connectors.gemini.gemini_llm import GeminiLLM

# Model enums (re-exported for backward compatibility)
from .connectors.azure.models import AzureOpenAIModel
from .connectors.bedrock.models import BedrockModel
from .connectors.gemini.models import GeminiModel

# Model registry and metadata
from .model_registry import (
    ModelRegistry,
    ModelMetadata,
    ModelFamily,
    get_model_registry,
    get_model_metadata,
    validate_model_parameters,
)

# Exception classes
from .exceptions import (
    LLMError,
    InputValidationError,
    ProviderError,
    ConfigurationError,
    RateLimitError,
    JSONParsingError,
    TimeoutError,
    AuthenticationError,
    QuotaExceededError,
    ServiceUnavailableError,
    InvalidResponseError,
)

# Factory class
class LLMFactory:
    """
    Factory for creating LLM instances based on configuration.

    Provides a unified interface for creating different LLM provider instances
    with proper configuration validation and error handling.
    """

    _providers = {
        LLMProvider.AZURE_OPENAI: AzureLLM,
        LLMProvider.BEDROCK: BedrockLLM,
        LLMProvider.GEMINI: GeminiLLM,
    }

    @classmethod
    def create_llm(cls, config: BaseLLMConfig) -> BaseLLM:
        """
        Create an LLM instance for the specified provider.

        Args:
            config: Configuration object for the LLM provider

        Returns:
            Configured LLM instance

        Raises:
            ConfigurationError: If provider is not supported or configuration is invalid
        """
        if config.provider not in cls._providers:
            raise ConfigurationError(f"Unsupported provider: {config.provider}")

        llm_class = cls._providers[config.provider]
        return llm_class(config)

    @classmethod
    def get_supported_providers(cls) -> List[LLMProvider]:
        """
        Get list of supported LLM providers.

        Returns:
            List of supported provider enums
        """
        return list(cls._providers.keys())

    @classmethod
    def get_provider_class(cls, provider: LLMProvider) -> type:
        """
        Get the LLM class for a specific provider.

        Args:
            provider: The LLM provider

        Returns:
            LLM implementation class

        Raises:
            ConfigurationError: If provider is not supported
        """
        if provider not in cls._providers:
            raise ConfigurationError(f"Unsupported provider: {provider}")

        return cls._providers[provider]


# Convenience functions for quick setup
def create_azure_llm(
    api_key: str,
    model_name: str,
    deployment_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    **kwargs
) -> AzureLLM:
    """
    Create an Azure OpenAI LLM instance with minimal configuration.

    Args:
        api_key: Azure OpenAI API key
        model_name: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        deployment_name: Deployment name (optional)
        endpoint: Azure endpoint URL (optional)
        **kwargs: Additional configuration parameters

    Returns:
        Configured AzureLLM instance
    """
    config = AzureOpenAIConfig(
        api_key=api_key,
        model_name=model_name,
        deployment_name=deployment_name,
        endpoint=endpoint,
        **kwargs
    )
    return LLMFactory.create_llm(config)


def create_bedrock_llm(
    api_key: str,
    model_name: str,
    region: str = "us-east-1",
    **kwargs
) -> BedrockLLM:
    """
    Create an Amazon Bedrock LLM instance with minimal configuration.

    Args:
        api_key: AWS API key (or 'bedrock' for IAM roles)
        model_name: Model name (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
        region: AWS region (default: 'us-east-1')
        **kwargs: Additional configuration parameters

    Returns:
        Configured BedrockLLM instance
    """
    config = BedrockConfig(
        api_key=api_key,
        model_name=model_name,
        region=region,
        **kwargs
    )
    return LLMFactory.create_llm(config)


def create_gemini_llm(
    api_key: str,
    model_name: str,
    project_id: Optional[str] = None,
    **kwargs
) -> GeminiLLM:
    """
    Create a Google Gemini LLM instance with minimal configuration.

    Args:
        api_key: Google AI API key
        model_name: Model name (e.g., 'gemini-pro', 'gemini-pro-vision')
        project_id: Google Cloud project ID (optional)
        **kwargs: Additional configuration parameters

    Returns:
        Configured GeminiLLM instance
    """
    config = GeminiConfig(
        api_key=api_key,
        model_name=model_name,
        project_id=project_id,
        **kwargs
    )
    return LLMFactory.create_llm(config)


# Tool integration support
from .tool_integration import (
    ToolConverter,
    ToolConverterFactory,
    convert_tools_for_provider,
    convert_tool_result_for_provider,
)
from .connectors.azure.tool_converter import AzureOpenAIToolConverter
from .connectors.bedrock.tool_converter import BedrockToolConverter
from .connectors.gemini.tool_converter import GeminiToolConverter

# Export all public API components
__all__ = [
    # Enums and types
    "InputMediaType",
    "OutputMediaType",
    "LLMProvider",
    "LLMType",
    "MessageRole",

    # Configuration classes
    "BaseLLMConfig",
    "AzureOpenAIConfig",
    "BedrockConfig",
    "GeminiConfig",
    "create_llm_config",

    # Response models
    "LLMResponse",
    "LLMStreamChunk",

    # Interfaces and base classes
    "ILLM",
    "BaseLLM",

    # Provider implementations
    "AzureLLM",
    "BedrockLLM",
    "GeminiLLM",
    
    # Model enums
    "AzureOpenAIModel",
    "BedrockModel",
    "GeminiModel",
    
    # Model registry and metadata
    "ModelRegistry",
    "ModelMetadata",
    "ModelFamily",
    "get_model_registry",
    "get_model_metadata",
    "validate_model_parameters",

    # Factory and convenience functions
    "LLMFactory",
    "create_azure_llm",
    "create_bedrock_llm",
    "create_gemini_llm",

    # Tool integration
    "ToolConverter",
    "AzureOpenAIToolConverter",
    "BedrockToolConverter",
    "GeminiToolConverter",
    "ToolConverterFactory",
    "convert_tools_for_provider",
    "convert_tool_result_for_provider",

    # Exception classes
    "LLMError",
    "InputValidationError",
    "ProviderError",
    "ConfigurationError",
    "RateLimitError",
    "JSONParsingError",
    "TimeoutError",
    "AuthenticationError",
    "QuotaExceededError",
    "ServiceUnavailableError",
    "InvalidResponseError",
]
