"""
Google Gemini Model Registry.

Handles registration of all Gemini models with their complete metadata.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.llms.model_registry import ModelRegistry

from core.llms.model_registry import ModelMetadata, ModelFamily
from core.llms.enums import InputMediaType, OutputMediaType, LLMProvider
from core.llms.constants import (
    GEMINI_PRO,
    GEMINI_PRO_VISION,
    GEMINI_1_5_PRO,
    GEMINI_1_5_FLASH,
    GEMINI_1_5_PRO_002,
    GEMINI_1_5_FLASH_002,
)


def register_gemini_models(registry: 'ModelRegistry') -> None:
    """Register all Gemini models with the global registry"""
    
    # Gemini 1.5 models
    registry.register_model(ModelMetadata(
        model_name=GEMINI_1_5_PRO,
        provider=LLMProvider.GEMINI,
        model_family=ModelFamily.GEMINI_1_5,
        display_name="Gemini 1.5 Pro",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=2097152,  # 2M context window
        max_output_tokens=8192,
        max_input_tokens=2097152,
        parameter_mappings={
            "max_tokens": "max_output_tokens",  # Gemini uses different parameter name
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_output_tokens": 8192,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_project_id": True,
            "requires_location": True,
            "api_format": "google_ai",
        },
        cost_per_1k_input_tokens=0.00125,
        cost_per_1k_output_tokens=0.00375,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=GEMINI_1_5_FLASH,
        provider=LLMProvider.GEMINI,
        model_family=ModelFamily.GEMINI_1_5,
        display_name="Gemini 1.5 Flash",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=1048576,  # 1M context window
        max_output_tokens=8192,
        max_input_tokens=1048576,
        parameter_mappings={
            "max_tokens": "max_output_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_output_tokens": 8192,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_project_id": True,
            "requires_location": True,
            "api_format": "google_ai",
        },
        cost_per_1k_input_tokens=0.000075,
        cost_per_1k_output_tokens=0.0003,
    ))
    
    # Gemini Pro models
    registry.register_model(ModelMetadata(
        model_name=GEMINI_PRO,
        provider=LLMProvider.GEMINI,
        model_family=ModelFamily.GEMINI_PRO,
        display_name="Gemini Pro",
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=False,
        supports_json_mode=True,
        max_context_length=32768,
        max_output_tokens=8192,
        max_input_tokens=32768,
        parameter_mappings={
            "max_tokens": "max_output_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_output_tokens": 8192,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_project_id": True,
            "requires_location": True,
            "api_format": "google_ai",
        },
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=GEMINI_PRO_VISION,
        provider=LLMProvider.GEMINI,
        model_family=ModelFamily.GEMINI_PRO,
        display_name="Gemini Pro Vision",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=False,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=16384,
        max_output_tokens=4096,
        max_input_tokens=16384,
        parameter_mappings={
            "max_tokens": "max_output_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_output_tokens": 4096,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_project_id": True,
            "requires_location": True,
            "api_format": "google_ai",
        },
        cost_per_1k_input_tokens=0.00025,
        cost_per_1k_output_tokens=0.0005,
    ))

