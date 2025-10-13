"""
Azure OpenAI model definitions and capabilities.
"""

from enum import Enum
from typing import Dict, Any

from core.llms.enums import InputMediaType, OutputMediaType, LLMProvider
from core.llms.models import ModelCapabilities
from core.llms.constants import (
    AZURE_OPENAI_GPT_4O,
    AZURE_OPENAI_GPT_4O_MINI,
    AZURE_OPENAI_GPT_4_TURBO,
    AZURE_OPENAI_GPT_4,
    AZURE_OPENAI_GPT_35_TURBO,
    AZURE_OPENAI_GPT_35_TURBO_16K,
)


class AzureOpenAIModel(str, Enum):
    """Supported Azure OpenAI models"""
    GPT_4O = AZURE_OPENAI_GPT_4O
    GPT_4O_MINI = AZURE_OPENAI_GPT_4O_MINI
    GPT_4_TURBO = AZURE_OPENAI_GPT_4_TURBO
    GPT_4 = AZURE_OPENAI_GPT_4
    GPT_35_TURBO = AZURE_OPENAI_GPT_35_TURBO
    GPT_35_TURBO_16K = AZURE_OPENAI_GPT_35_TURBO_16K


# Azure OpenAI model capabilities
AZURE_MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    AzureOpenAIModel.GPT_4O: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        supports_vision=True,
        max_context_length=128000,
        max_output_tokens=16384,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_4O_MINI: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=128000,
        max_output_tokens=16384,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_4_TURBO: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        max_context_length=128000,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_4: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        max_context_length=8192,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),

    AzureOpenAIModel.GPT_35_TURBO: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_function_calling=True,
        max_context_length=16385,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),
    
    AzureOpenAIModel.GPT_35_TURBO_16K: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=False,
        supports_function_calling=True,
        max_context_length=16385,
        max_output_tokens=4096,
        provider=LLMProvider.AZURE_OPENAI,
    ),
}


# Azure OpenAI model parameter defaults
AZURE_MODEL_PARAMETER_DEFAULTS: Dict[str, Dict[str, Any]] = {
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

    AzureOpenAIModel.GPT_35_TURBO: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },
    
    AzureOpenAIModel.GPT_35_TURBO_16K: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    },
}


def get_azure_models() -> set[str]:
    """Get all supported Azure OpenAI model names."""
    return set(AZURE_MODEL_CAPABILITIES.keys())


def is_azure_model(model_name: str) -> bool:
    """Check if a model name is an Azure OpenAI model."""
    return model_name in AZURE_MODEL_CAPABILITIES
