"""
Azure OpenAI Model Registry.

This module registers Azure OpenAI models with the global model registry.
"""

from typing import TYPE_CHECKING

from ...enum import LLMProvider, ModelFamily, InputMediaType, OutputMediaType, LLMType
from ...spec.llm_types import ModelMetadata
from ...constants import (
    # Parameter names
    PARAM_MAX_TOKENS,
    PARAM_MAX_COMPLETION_TOKENS,
    PARAM_TEMPERATURE,
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
    MODEL_NAME_AZURE_GPT_4O,
    MODEL_NAME_AZURE_GPT_4_TURBO,
    MODEL_NAME_AZURE_GPT_35_TURBO,
    # Display names
    DISPLAY_NAME_AZURE_GPT_4O,
    DISPLAY_NAME_AZURE_GPT_4_TURBO,
    DISPLAY_NAME_AZURE_GPT_35_TURBO,
)

if TYPE_CHECKING:
    from ..model_registry import ModelRegistry


def register_azure_models(registry: 'ModelRegistry') -> None:
    """
    Register Azure OpenAI models with the model registry.
    
    Note: Azure uses the same models as OpenAI but with Azure-specific deployment.
    Model names should match your Azure deployment names.
    
    Args:
        registry: ModelRegistry instance to register models with
    """
    
    # Azure GPT-4o
    registry.register_model(ModelMetadata(
        model_name=MODEL_NAME_AZURE_GPT_4O,
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4,
        display_name=DISPLAY_NAME_AZURE_GPT_4O,
        llm_type=LLMType.CHAT,
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=4096,
        max_input_tokens=124000,
        parameter_mappings={
            PARAM_MAX_TOKENS: PARAM_MAX_COMPLETION_TOKENS,
            PARAM_TEMPERATURE: PARAM_TEMPERATURE,
            PARAM_TOP_P: PARAM_TOP_P,
            PARAM_FREQUENCY_PENALTY: PARAM_FREQUENCY_PENALTY,
            PARAM_PRESENCE_PENALTY: PARAM_PRESENCE_PENALTY,
            PARAM_STOP: PARAM_STOP,
        },
        default_parameters={
            # Note: GPT-5 only supports default temperature (1.0), don't set it
            PARAM_MAX_TOKENS: 4096,
            PARAM_TOP_P: 1.0,
            PARAM_FREQUENCY_PENALTY: 0.0,
            PARAM_PRESENCE_PENALTY: 0.0,
        },
        api_requirements={
            API_REQ_USES_DEPLOYMENT_NAME: True,
            API_REQ_REQUIRES_API_KEY: True,
            API_REQ_REQUIRES_ENDPOINT: True,
            API_REQ_REQUIRES_API_VERSION: True,
            API_REQ_SUPPORTS_STREAMING: True,
        },
        cost_per_1k_input_tokens=0.005,
        cost_per_1k_output_tokens=0.015,
        is_deprecated=False,
    ))
    
    # Azure GPT-4 Turbo
    registry.register_model(ModelMetadata(
        model_name=MODEL_NAME_AZURE_GPT_4_TURBO,
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4,
        display_name=DISPLAY_NAME_AZURE_GPT_4_TURBO,
        llm_type=LLMType.CHAT,
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=4096,
        max_input_tokens=124000,
        parameter_mappings={
            PARAM_MAX_TOKENS: PARAM_MAX_COMPLETION_TOKENS,
            PARAM_TEMPERATURE: PARAM_TEMPERATURE,
            PARAM_TOP_P: PARAM_TOP_P,
            PARAM_FREQUENCY_PENALTY: PARAM_FREQUENCY_PENALTY,
            PARAM_PRESENCE_PENALTY: PARAM_PRESENCE_PENALTY,
            PARAM_STOP: PARAM_STOP,
        },
        default_parameters={
            # Note: GPT-5 only supports default temperature (1.0), don't set it
            PARAM_MAX_TOKENS: 4096,
            PARAM_TOP_P: 1.0,
            PARAM_FREQUENCY_PENALTY: 0.0,
            PARAM_PRESENCE_PENALTY: 0.0,
        },
        api_requirements={
            API_REQ_USES_DEPLOYMENT_NAME: True,
            API_REQ_REQUIRES_API_KEY: True,
            API_REQ_REQUIRES_ENDPOINT: True,
            API_REQ_REQUIRES_API_VERSION: True,
            API_REQ_SUPPORTS_STREAMING: True,
        },
        cost_per_1k_input_tokens=0.01,
        cost_per_1k_output_tokens=0.03,
        is_deprecated=False,
    ))
    
    # Azure GPT-3.5 Turbo
    registry.register_model(ModelMetadata(
        model_name=MODEL_NAME_AZURE_GPT_35_TURBO,
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4,  # Using AZURE_GPT_4 family for now
        display_name=DISPLAY_NAME_AZURE_GPT_35_TURBO,
        llm_type=LLMType.CHAT,
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=False,
        supports_json_mode=True,
        max_context_length=16385,
        max_output_tokens=4096,
        max_input_tokens=12000,
        parameter_mappings={
            PARAM_MAX_TOKENS: PARAM_MAX_COMPLETION_TOKENS,
            PARAM_TEMPERATURE: PARAM_TEMPERATURE,
            PARAM_TOP_P: PARAM_TOP_P,
            PARAM_FREQUENCY_PENALTY: PARAM_FREQUENCY_PENALTY,
            PARAM_PRESENCE_PENALTY: PARAM_PRESENCE_PENALTY,
            PARAM_STOP: PARAM_STOP,
        },
        default_parameters={
            # Note: GPT-5 only supports default temperature (1.0), don't set it
            PARAM_MAX_TOKENS: 4096,
            PARAM_TOP_P: 1.0,
            PARAM_FREQUENCY_PENALTY: 0.0,
            PARAM_PRESENCE_PENALTY: 0.0,
        },
        api_requirements={
            API_REQ_USES_DEPLOYMENT_NAME: True,
            API_REQ_REQUIRES_API_KEY: True,
            API_REQ_REQUIRES_ENDPOINT: True,
            API_REQ_REQUIRES_API_VERSION: True,
            API_REQ_SUPPORTS_STREAMING: True,
        },
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
        is_deprecated=False,
    ))

