"""
OpenAI Model Registry.

This module registers OpenAI models with the global model registry.
"""

from typing import TYPE_CHECKING

from ...enum import LLMProvider, ModelFamily, InputMediaType, OutputMediaType, LLMType
from ...spec.llm_types import ModelMetadata

if TYPE_CHECKING:
    from ..model_registry import ModelRegistry


def register_openai_models(registry: 'ModelRegistry') -> None:
    """
    Register OpenAI models with the model registry.
    
    Args:
        registry: ModelRegistry instance to register models with
    """
    
    # GPT-4o (Latest GPT-4 optimized model - similar to GPT-4.1)
    registry.register_model(ModelMetadata(
        model_name="gpt-4o",
        provider=LLMProvider.OPENAI,
        model_family=ModelFamily.GPT_4,
        display_name="GPT-4o",
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
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_api_key": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.005,  # $5 per 1M tokens
        cost_per_1k_output_tokens=0.015,  # $15 per 1M tokens
        is_deprecated=False,
    ))
    
    # GPT-4 Turbo
    registry.register_model(ModelMetadata(
        model_name="gpt-4-turbo",
        provider=LLMProvider.OPENAI,
        model_family=ModelFamily.GPT_4,
        display_name="GPT-4 Turbo",
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
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_api_key": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.01,
        cost_per_1k_output_tokens=0.03,
        is_deprecated=False,
    ))
    
    # GPT-3.5 Turbo (for comparison/lower cost option)
    registry.register_model(ModelMetadata(
        model_name="gpt-3.5-turbo",
        provider=LLMProvider.OPENAI,
        model_family=ModelFamily.GPT_4,  # Using GPT_4 family for now
        display_name="GPT-3.5 Turbo",
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
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_api_key": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
        is_deprecated=False,
    ))

