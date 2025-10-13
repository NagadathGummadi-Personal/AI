"""
Google Gemini model definitions and capabilities.
"""

from enum import Enum
from typing import Dict, Any

from core.llms.enums import InputMediaType, OutputMediaType, LLMProvider
from core.llms.models import ModelCapabilities
from core.llms.constants import (
    GEMINI_PRO,
    GEMINI_PRO_VISION,
    GEMINI_1_5_PRO,
    GEMINI_1_5_FLASH,
)


class GeminiModel(str, Enum):
    """Supported Gemini models"""
    GEMINI_PRO = GEMINI_PRO
    GEMINI_PRO_VISION = GEMINI_PRO_VISION
    GEMINI_1_5_PRO = GEMINI_1_5_PRO
    GEMINI_1_5_FLASH = GEMINI_1_5_FLASH


# Gemini model capabilities
GEMINI_MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    GeminiModel.GEMINI_PRO: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_json_mode=True,
        max_context_length=32768,
        max_output_tokens=8192,
        provider=LLMProvider.GEMINI,
    ),

    GeminiModel.GEMINI_PRO_VISION: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=16384,
        max_output_tokens=4096,
        provider=LLMProvider.GEMINI,
    ),

    GeminiModel.GEMINI_1_5_PRO: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=2097152,
        max_output_tokens=8192,
        provider=LLMProvider.GEMINI,
    ),

    GeminiModel.GEMINI_1_5_FLASH: ModelCapabilities(
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_json_mode=True,
        supports_vision=True,
        max_context_length=1048576,
        max_output_tokens=8192,
        provider=LLMProvider.GEMINI,
    ),
}


# Gemini model parameter defaults
GEMINI_MODEL_PARAMETER_DEFAULTS: Dict[str, Dict[str, Any]] = {
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


def get_gemini_models() -> set[str]:
    """Get all supported Gemini model names."""
    return set(GEMINI_MODEL_CAPABILITIES.keys())


def is_gemini_model(model_name: str) -> bool:
    """Check if a model name is a Gemini model."""
    return model_name in GEMINI_MODEL_CAPABILITIES
