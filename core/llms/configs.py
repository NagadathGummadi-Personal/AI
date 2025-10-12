"""
LLM configuration classes for the AI Agent SDK.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Type, Union

from pydantic import BaseModel

from .defaults import (
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_TOP_P,
    DEFAULT_LLM_FREQUENCY_PENALTY,
    DEFAULT_LLM_PRESENCE_PENALTY,
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_SUPPORTED_INPUT_TYPES,
    DEFAULT_SUPPORTED_OUTPUT_TYPES,
    DEFAULT_STREAMING_SUPPORTED,
    AZURE_OPENAI_DEFAULT_API_VERSION,
    BEDROCK_DEFAULT_REGION,
    GEMINI_DEFAULT_API_VERSION,
    GEMINI_DEFAULT_LOCATION,
)
from .enums import InputType, LLMProvider, OutputMediaType
from .exceptions import ConfigurationError


@dataclass
class BaseLLMConfig:
    """Base configuration for all LLM providers"""

    provider: LLMProvider
    model_name: str
    api_key: str
    temperature: float = DEFAULT_LLM_TEMPERATURE
    max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    top_p: float = DEFAULT_LLM_TOP_P
    frequency_penalty: float = DEFAULT_LLM_FREQUENCY_PENALTY
    presence_penalty: float = DEFAULT_LLM_PRESENCE_PENALTY
    stop_sequences: List[str] = field(default_factory=list)
    timeout: int = DEFAULT_LLM_TIMEOUT
    max_retries: int = DEFAULT_LLM_MAX_RETRIES

    # Input/output handling
    supported_input_types: Set[InputType] = field(default_factory=lambda: DEFAULT_SUPPORTED_INPUT_TYPES)
    supported_output_types: Set[OutputMediaType] = field(default_factory=lambda: DEFAULT_SUPPORTED_OUTPUT_TYPES)
    streaming_supported: bool = DEFAULT_STREAMING_SUPPORTED

    # Extended config
    prompt: Optional[str] = None
    json_output: bool = False
    json_schema: Optional[Dict[str, Any]] = None
    json_class: Optional[Union[Type[BaseModel], Type[Any]]] = None

    # Provider meta
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    region: Optional[str] = None

    def validate_config(self) -> None:
        """Validate the configuration parameters"""
        if not 0 <= self.temperature <= 2:
            raise ConfigurationError("Temperature must be between 0 and 2")
        if self.max_tokens <= 0:
            raise ConfigurationError("Max tokens must be positive")
        if not self.supported_input_types:
            raise ConfigurationError("At least one input type must be supported")
        if not self.supported_output_types:
            raise ConfigurationError("At least one output type must be supported")
        if self.json_output and not (self.json_schema or self.json_class):
            raise ConfigurationError("json_output=True requires json_schema or json_class")
        if not self.api_key:
            raise ConfigurationError(f"API key is required for provider {self.provider}")
        if not self.model_name:
            raise ConfigurationError("Model name is required")


@dataclass
class AzureOpenAIConfig(BaseLLMConfig):
    """Configuration for Azure OpenAI"""

    deployment_name: Optional[str] = None
    endpoint: Optional[str] = None

    def validate_config(self) -> None:
        """Validate Azure OpenAI specific configuration"""
        super().validate_config()
        if not self.endpoint and not self.deployment_name:
            raise ConfigurationError("Either endpoint or deployment_name must be provided for Azure OpenAI")


@dataclass
class BedrockConfig(BaseLLMConfig):
    """Configuration for Amazon Bedrock"""

    model_id: Optional[str] = None  # Alternative to model_name for Bedrock
    bedrock_runtime: Optional[str] = None

    def validate_config(self) -> None:
        """Validate Bedrock specific configuration"""
        super().validate_config()
        if not self.region:
            raise ConfigurationError("Region is required for Bedrock")


@dataclass
class GeminiConfig(BaseLLMConfig):
    """Configuration for Google Gemini"""

    project_id: Optional[str] = None
    location: str = GEMINI_DEFAULT_LOCATION

    def validate_config(self) -> None:
        """Validate Gemini specific configuration"""
        super().validate_config()
        if not self.project_id:
            raise ConfigurationError("Project ID is required for Gemini")


# Configuration registry for easy access
LLM_CONFIGS = {
    LLMProvider.AZURE_OPENAI: AzureOpenAIConfig,
    LLMProvider.BEDROCK: BedrockConfig,
    LLMProvider.GEMINI: GeminiConfig,
}


def create_llm_config(provider: LLMProvider, **kwargs) -> BaseLLMConfig:
    """
    Factory function to create provider-specific LLM configurations

    Args:
        provider: The LLM provider
        **kwargs: Configuration parameters

    Returns:
        Configured LLM instance

    Raises:
        ConfigurationError: If provider is not supported or configuration is invalid
    """
    config_class = LLM_CONFIGS.get(provider)
    if not config_class:
        raise ConfigurationError(f"Unsupported provider: {provider}")

    config = config_class(**kwargs)
    config.validate_config()
    return config
