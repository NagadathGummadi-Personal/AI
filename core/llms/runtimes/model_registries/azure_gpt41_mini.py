"""
Azure GPT-4.1 Mini Model Registration.

This module registers Azure GPT-4.1 Mini model with the global model registry.
"""

from typing import TYPE_CHECKING

from ...enum import LLMProvider, ModelFamily, InputMediaType, OutputMediaType, LLMType
from ...spec.llm_types import ModelMetadata

if TYPE_CHECKING:
    from ..model_registry import ModelRegistry


def register_azure_gpt41_mini(registry: 'ModelRegistry') -> None:
    """
    Register Azure GPT-4.1 Mini model.
    
    Args:
        registry: ModelRegistry instance to register models with
    """
    
    # Azure GPT-4.1 Mini
    registry.register_model(ModelMetadata(
        model_name="azure-gpt-4.1-mini",
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4_1_MINI,
        display_name="Azure GPT-4.1 Mini",
        llm_type=LLMType.CHAT,
        # Can handle text, image, or text+image together (multimodal)
        # Does NOT support audio or video
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        # Can output text, JSON, image, and audio
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON, OutputMediaType.AUDIO, OutputMediaType.IMAGE},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=16384,
        max_input_tokens=124000,
        parameter_mappings={
            "max_tokens": "max_completion_tokens",  # GPT-4.1 uses new parameter name
            # Note: GPT-4.1 Mini only supports default temperature (1.0)
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            # Note: GPT-4.1 Mini only supports default temperature (1.0), don't set it
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        parameter_ranges={
            # GPT-4.1 Mini restrictions
            "temperature": (1.0, 1.0),  # Only default (1.0) supported
            "top_p": (0.0, 1.0),
            "frequency_penalty": (-2.0, 2.0),
            "presence_penalty": (-2.0, 2.0),
            "max_tokens": (1, 16384),
        },
        supported_parameters={
            # GPT-4.1 Mini only supports these parameters
            "max_tokens", "top_p", "frequency_penalty", "presence_penalty", "stop"
            # Note: temperature is NOT in supported list (uses default only)
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_key": True,
            "requires_endpoint": True,
            "requires_api_version": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.00015,  # Lower cost for mini model
        cost_per_1k_output_tokens=0.0006,
        is_deprecated=False,
    ))

