"""
Amazon Bedrock model definitions and capabilities.
"""

from enum import Enum
from typing import Dict, Any

from core.llms.enums import InputMediaType, OutputMediaType, LLMProvider
from core.llms.models import ModelCapabilities
from core.llms.constants import (
    BEDROCK_CLAUDE_3_OPUS,
    BEDROCK_CLAUDE_3_SONNET,
    BEDROCK_CLAUDE_3_HAIKU,
)


class BedrockModel(str, Enum):
    """Supported Bedrock models (Anthropic Claude only for now)"""
    CLAUDE_3_OPUS = BEDROCK_CLAUDE_3_OPUS
    CLAUDE_3_SONNET = BEDROCK_CLAUDE_3_SONNET
    CLAUDE_3_HAIKU = BEDROCK_CLAUDE_3_HAIKU


# Bedrock model capabilities
BEDROCK_MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    BedrockModel.CLAUDE_3_OPUS: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        supports_function_calling=True,
        max_context_length=200000,
        max_output_tokens=4096,
        provider=LLMProvider.BEDROCK,
    ),

    BedrockModel.CLAUDE_3_SONNET: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        supports_function_calling=True,
        max_context_length=200000,
        max_output_tokens=4096,
        provider=LLMProvider.BEDROCK,
    ),

    BedrockModel.CLAUDE_3_HAIKU: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        supports_function_calling=True,
        max_context_length=200000,
        max_output_tokens=4096,
        provider=LLMProvider.BEDROCK,
    ),
}


# Bedrock model parameter defaults
BEDROCK_MODEL_PARAMETER_DEFAULTS: Dict[str, Dict[str, Any]] = {
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
}


def get_bedrock_models() -> set[str]:
    """Get all supported Bedrock model names."""
    return set(BEDROCK_MODEL_CAPABILITIES.keys())


def is_bedrock_model(model_name: str) -> bool:
    """Check if a model name is a Bedrock model."""
    return model_name in BEDROCK_MODEL_CAPABILITIES
