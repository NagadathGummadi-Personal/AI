"""
Model definitions and capabilities for LLM providers.
"""

from enum import Enum
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass

from .enums import InputType, OutputMediaType, LLMProvider
from .constants import (
    # Azure OpenAI model constants
    AZURE_OPENAI_GPT_4O,
    AZURE_OPENAI_GPT_4O_MINI,
    AZURE_OPENAI_GPT_4_TURBO,
    AZURE_OPENAI_GPT_4,
    AZURE_OPENAI_GPT_3_5_TURBO,

    # Bedrock model constants
    BEDROCK_CLAUDE_3_OPUS,
    BEDROCK_CLAUDE_3_SONNET,
    BEDROCK_CLAUDE_3_HAIKU,

    # Gemini model constants
    GEMINI_PRO,
    GEMINI_PRO_VISION,
    GEMINI_1_5_PRO,
    GEMINI_1_5_FLASH,
)


class AzureOpenAIModel(str, Enum):
    """Supported Azure OpenAI models"""
    GPT_4O = AZURE_OPENAI_GPT_4O
    GPT_4O_MINI = AZURE_OPENAI_GPT_4O_MINI
    GPT_4_TURBO = AZURE_OPENAI_GPT_4_TURBO
    GPT_4 = AZURE_OPENAI_GPT_4
    GPT_3_5_TURBO = AZURE_OPENAI_GPT_3_5_TURBO


class BedrockModel(str, Enum):
    """Supported Bedrock models (Anthropic Claude only for now)"""
    CLAUDE_3_OPUS = BEDROCK_CLAUDE_3_OPUS
    CLAUDE_3_SONNET = BEDROCK_CLAUDE_3_SONNET
    CLAUDE_3_HAIKU = BEDROCK_CLAUDE_3_HAIKU


class GeminiModel(str, Enum):
    """Supported Gemini models"""
    GEMINI_PRO = GEMINI_PRO
    GEMINI_PRO_VISION = GEMINI_PRO_VISION
    GEMINI_1_5_PRO = GEMINI_1_5_PRO
    GEMINI_1_5_FLASH = GEMINI_1_5_FLASH


@dataclass
class ModelCapabilities:
    """Capabilities for a specific model"""

    # Input/output types supported
    supported_input_types: Set[InputType]
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
    provider: LLMProvider = LLMProvider.AZURE_OPENAI


# Model capabilities mapping
MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    # Azure OpenAI models
    AzureOpenAIModel.GPT_4O: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        supports_vision=True,
        max_context_length=128000,
        max_output_tokens=16384,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_4O_MINI: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=128000,
        max_output_tokens=16384,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_4_TURBO: ModelCapabilities(
        supported_input_types={InputType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        max_context_length=128000,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_4: ModelCapabilities(
        supported_input_types={InputType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        max_context_length=8192,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_3_5_TURBO: ModelCapabilities(
        supported_input_types={InputType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        max_context_length=16385,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    # Bedrock Claude models
    BedrockModel.CLAUDE_3_OPUS: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        supports_function_calling=True,
        max_context_length=200000,
        max_output_tokens=4096,
        provider=LLMProvider.BEDROCK,
    ),

    BedrockModel.CLAUDE_3_SONNET: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        supports_function_calling=True,
        max_context_length=200000,
        max_output_tokens=4096,
        provider=LLMProvider.BEDROCK,
    ),

    BedrockModel.CLAUDE_3_HAIKU: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        supports_function_calling=True,
        max_context_length=200000,
        max_output_tokens=4096,
        provider=LLMProvider.BEDROCK,
    ),

    # Gemini models
    GeminiModel.GEMINI_PRO: ModelCapabilities(
        supported_input_types={InputType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        max_context_length=32768,
        max_output_tokens=8192,
        provider=LLMProvider.GEMINI,
    ),

    GeminiModel.GEMINI_PRO_VISION: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=16384,
        max_output_tokens=4096,
        provider=LLMProvider.GEMINI,
    ),

    GeminiModel.GEMINI_1_5_PRO: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=2097152,
        max_output_tokens=8192,
        provider=LLMProvider.GEMINI,
    ),

    GeminiModel.GEMINI_1_5_FLASH: ModelCapabilities(
        supported_input_types={InputType.TEXT, InputType.IMAGE, InputType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=1048576,
        max_output_tokens=8192,
        provider=LLMProvider.GEMINI,
    ),
}


def get_model_capabilities(model_name: str) -> Optional[ModelCapabilities]:
    """Get capabilities for a specific model"""
    return MODEL_CAPABILITIES.get(model_name)


def get_provider_models(provider: LLMProvider) -> Set[str]:
    """Get all supported models for a provider"""
    models = set()
    for model_name, capabilities in MODEL_CAPABILITIES.items():
        if capabilities.provider == provider:
            models.add(model_name)
    return models


def validate_model_for_provider(model_name: str, provider: LLMProvider) -> bool:
    """Validate that a model is supported by a provider"""
    capabilities = get_model_capabilities(model_name)
    return capabilities is not None and capabilities.provider == provider


# Model-specific parameter defaults
MODEL_PARAMETER_DEFAULTS: Dict[str, Dict[str, Any]] = {
    # Azure OpenAI defaults
    AzureOpenAIModel.GPT_4O: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },

    AzureOpenAIModel.GPT_4O_MINI: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },

    AzureOpenAIModel.GPT_4_TURBO: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },

    AzureOpenAIModel.GPT_4: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },

    AzureOpenAIModel.GPT_3_5_TURBO: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },

    # Bedrock Claude defaults
    BedrockModel.CLAUDE_3_OPUS: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
    },

    BedrockModel.CLAUDE_3_SONNET: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
    },

    BedrockModel.CLAUDE_3_HAIKU: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
    },

    # Gemini defaults
    GeminiModel.GEMINI_PRO: {
        "temperature": 0.7,
        "max_output_tokens": 8192,
        "top_p": 1.0,
    },

    GeminiModel.GEMINI_PRO_VISION: {
        "temperature": 0.7,
        "max_output_tokens": 4096,
        "top_p": 1.0,
    },

    GeminiModel.GEMINI_1_5_PRO: {
        "temperature": 0.7,
        "max_output_tokens": 8192,
        "top_p": 1.0,
    },

    GeminiModel.GEMINI_1_5_FLASH: {
        "temperature": 0.7,
        "max_output_tokens": 8192,
        "top_p": 1.0,
    },
}
