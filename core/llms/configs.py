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
    GEMINI_DEFAULT_LOCATION,
    MSG_INVALID_TEMPERATURE_RANGE_AZURE_OPENAI,
    MSG_INVALID_TEMPERATURE_RANGE_BEDROCK,
    MSG_INVALID_TEMPERATURE_RANGE_GEMINI,
    MSG_INVALID_MAX_TOKENS_POSITIVE,
    MSG_AT_LEAST_ONE_INPUT_TYPE_SUPPORTED,
    MSG_AT_LEAST_ONE_OUTPUT_TYPE_SUPPORTED,
    MSG_JSON_OUTPUT_REQUIRES_JSON_SCHEMA_OR_JSON_CLASS,
    MSG_MISSING_API_KEY,
    MSG_MISSING_MODEL_NAME,
    MSG_ENDPOINT_OR_DEPLOYMENT_NAME_REQUIRED_AZURE_OPENAI,
    MSG_REGION_REQUIRED_BEDROCK,
    MSG_MODEL_ID_REQUIRED_BEDROCK,
    MSG_PROJECT_ID_REQUIRED_GEMINI,
    MSG_PROVIDER_NOT_SUPPORTED,
)
from .enums import InputMediaType, LLMProvider, OutputMediaType
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
    supported_input_types: Set[InputMediaType] = field(
        default_factory=lambda: DEFAULT_SUPPORTED_INPUT_TYPES
    )
    supported_output_types: Set[OutputMediaType] = field(
        default_factory=lambda: DEFAULT_SUPPORTED_OUTPUT_TYPES
    )
    streaming_supported: bool = DEFAULT_STREAMING_SUPPORTED

    # Extended config
    prompt: Optional[str] = None
    dynamic_variables: Optional[Dict[str, Any]] = None
    json_output: bool = False
    json_schema: Optional[Dict[str, Any]] = None
    json_class: Optional[Union[Type[BaseModel], Type[Any]]] = None

    # Provider meta
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    region: Optional[str] = None

    def validate_config(self) -> None:
        """Validate the configuration parameters"""
        # Validate temperature
        if self.provider == LLMProvider.AZURE_OPENAI:
            if not 0 <= self.temperature <= 2:
                raise ConfigurationError(MSG_INVALID_TEMPERATURE_RANGE_AZURE_OPENAI)
        elif self.provider == LLMProvider.BEDROCK:
            if not 0 <= self.temperature <= 1:
                raise ConfigurationError(MSG_INVALID_TEMPERATURE_RANGE_BEDROCK)
        elif self.provider == LLMProvider.GEMINI:
            if not 0 <= self.temperature <= 2:
                raise ConfigurationError(MSG_INVALID_TEMPERATURE_RANGE_GEMINI)
        else:
            raise ConfigurationError(f"Unsupported provider: {self.provider}")

        # Validate max tokens - Basic validation
        if self.max_tokens <= 0:
            raise ConfigurationError(MSG_INVALID_MAX_TOKENS_POSITIVE)
        # Validate supported input types
        if not self.supported_input_types:
            raise ConfigurationError(MSG_AT_LEAST_ONE_INPUT_TYPE_SUPPORTED)
        # Validate supported output types
        if not self.supported_output_types:
            raise ConfigurationError(MSG_AT_LEAST_ONE_OUTPUT_TYPE_SUPPORTED)
        # Validate json output
        if self.json_output and not (self.json_schema or self.json_class):
            raise ConfigurationError(MSG_JSON_OUTPUT_REQUIRES_JSON_SCHEMA_OR_JSON_CLASS)
        # Validate api key
        if not self.api_key:
            raise ConfigurationError(
                MSG_MISSING_API_KEY.format(provider=self.provider.value)
            )
        if not self.model_name:
            raise ConfigurationError(MSG_MISSING_MODEL_NAME)


@dataclass
class AzureOpenAIConfig(BaseLLMConfig):
    """Configuration for Azure OpenAI"""

    deployment_name: Optional[str] = None
    endpoint: Optional[str] = None

    def validate_config(self) -> None:
        """Validate Azure OpenAI specific configuration"""
        super().validate_config()
        if not self.endpoint and not self.deployment_name:
            raise ConfigurationError(
                MSG_ENDPOINT_OR_DEPLOYMENT_NAME_REQUIRED_AZURE_OPENAI
            )


@dataclass
class BedrockConfig(BaseLLMConfig):
    """Configuration for Amazon Bedrock"""

    model_id: Optional[str] = None  # Alternative to model_name for Bedrock
    bedrock_runtime: Optional[str] = None

    def validate_config(self) -> None:
        """Validate Bedrock specific configuration"""
        super().validate_config()
        if not self.region:
            raise ConfigurationError(MSG_REGION_REQUIRED_BEDROCK)
        if not self.model_id:
            raise ConfigurationError(MSG_MODEL_ID_REQUIRED_BEDROCK)


@dataclass
class GeminiConfig(BaseLLMConfig):
    """Configuration for Google Gemini"""

    project_id: Optional[str] = None
    location: str = GEMINI_DEFAULT_LOCATION

    def validate_config(self) -> None:
        """Validate Gemini specific configuration"""
        super().validate_config()
        if not self.project_id:
            raise ConfigurationError(MSG_PROJECT_ID_REQUIRED_GEMINI)


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
        raise ConfigurationError(MSG_PROVIDER_NOT_SUPPORTED.format(provider=provider))

    config = config_class(**kwargs)
    config.validate_config()
    return config
