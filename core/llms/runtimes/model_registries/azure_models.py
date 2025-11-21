"""
Azure OpenAI Model Registry.

This module registers Azure OpenAI models with the global model registry.
"""

from typing import TYPE_CHECKING

from ...enum import LLMProvider, ModelFamily, InputMediaType, OutputMediaType, LLMType
from ...spec.llm_types import ModelMetadata

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
        model_name="azure-gpt-4o",
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4,
        display_name="Azure GPT-4o",
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
            "max_tokens": "max_completion_tokens",  # GPT-4o uses new parameter
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            # Note: GPT-5 only supports default temperature (1.0), don't set it
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_key": True,
            "requires_endpoint": True,
            "requires_api_version": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.005,
        cost_per_1k_output_tokens=0.015,
        is_deprecated=False,
    ))
    
    # Azure GPT-4 Turbo
    registry.register_model(ModelMetadata(
        model_name="azure-gpt-4-turbo",
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4,
        display_name="Azure GPT-4 Turbo",
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
            "max_tokens": "max_completion_tokens",  # GPT-4o uses new parameter
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            # Note: GPT-5 only supports default temperature (1.0), don't set it
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_key": True,
            "requires_endpoint": True,
            "requires_api_version": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.01,
        cost_per_1k_output_tokens=0.03,
        is_deprecated=False,
    ))
    
    # Azure GPT-3.5 Turbo
    registry.register_model(ModelMetadata(
        model_name="azure-gpt-3.5-turbo",
        provider=LLMProvider.AZURE,
        model_family=ModelFamily.AZURE_GPT_4,  # Using AZURE_GPT_4 family for now
        display_name="Azure GPT-3.5 Turbo",
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
            "max_tokens": "max_completion_tokens",  # GPT-4o uses new parameter
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
            "stop": "stop",
        },
        default_parameters={
            # Note: GPT-5 only supports default temperature (1.0), don't set it
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_key": True,
            "requires_endpoint": True,
            "requires_api_version": True,
            "supports_streaming": True,
        },
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
        is_deprecated=False,
    ))

