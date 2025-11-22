"""
Azure GPT-4.1 Mini Model Registration.

This module registers Azure GPT-4.1 Mini model with the global model registry.
"""

from typing import TYPE_CHECKING

from ...enum import LLMProvider, ModelFamily, InputMediaType, OutputMediaType, LLMType
from ...spec.llm_types import ModelMetadata
from ...constants import (
    # Parameter names
    PARAM_MAX_TOKENS,
    PARAM_MAX_COMPLETION_TOKENS,
    PARAM_TOP_P,
    PARAM_FREQUENCY_PENALTY,
    PARAM_PRESENCE_PENALTY,
    PARAM_STOP,
    # API requirements
    API_REQ_USES_DEPLOYMENT_NAME,
    API_REQ_REQUIRES_API_KEY,
    API_REQ_REQUIRES_ENDPOINT,
    API_REQ_REQUIRES_API_VERSION,
    API_REQ_SUPPORTS_STREAMING,
    # Model names
    MODEL_NAME_AZURE_GPT_41_MINI,
    # Display names
    DISPLAY_NAME_AZURE_GPT_41_MINI,
)

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
        model_name=MODEL_NAME_AZURE_GPT_41_MINI,
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4_1_MINI,
        display_name=DISPLAY_NAME_AZURE_GPT_41_MINI,
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
            PARAM_MAX_TOKENS: PARAM_MAX_COMPLETION_TOKENS,
            PARAM_TOP_P: PARAM_TOP_P,
            PARAM_FREQUENCY_PENALTY: PARAM_FREQUENCY_PENALTY,
            PARAM_PRESENCE_PENALTY: PARAM_PRESENCE_PENALTY,
            PARAM_STOP: PARAM_STOP,
        },
        default_parameters={
            # Note: GPT-4.1 Mini only supports default temperature (1.0), don't set it
            PARAM_MAX_TOKENS: 4096,
            PARAM_TOP_P: 1.0,
            PARAM_FREQUENCY_PENALTY: 0.0,
            PARAM_PRESENCE_PENALTY: 0.0,
        },
        parameter_ranges={
            # GPT-4.1 Mini restrictions
            PARAM_MAX_TOKENS: (1, 16384),
            PARAM_TOP_P: (0.0, 1.0),
            PARAM_FREQUENCY_PENALTY: (-2.0, 2.0),
            PARAM_PRESENCE_PENALTY: (-2.0, 2.0),
        },
        supported_parameters={
            # GPT-4.1 Mini only supports these parameters
            PARAM_MAX_TOKENS, PARAM_TOP_P, PARAM_FREQUENCY_PENALTY, PARAM_PRESENCE_PENALTY, PARAM_STOP
            # Note: temperature is NOT in supported list (uses default only)
        },
        api_requirements={
            API_REQ_USES_DEPLOYMENT_NAME: True,
            API_REQ_REQUIRES_API_KEY: True,
            API_REQ_REQUIRES_ENDPOINT: True,
            API_REQ_REQUIRES_API_VERSION: True,
            API_REQ_SUPPORTS_STREAMING: True,
        },
        cost_per_1k_input_tokens=0.00015,  # Lower cost for mini model
        cost_per_1k_output_tokens=0.0006,
        is_deprecated=False,
    ))

