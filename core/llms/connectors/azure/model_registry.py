"""
Azure OpenAI Model Registry.

Handles registration of all Azure OpenAI models with their complete metadata.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.llms.model_registry import ModelRegistry

from core.llms.model_registry import ModelMetadata, ModelFamily
from core.llms.enums import InputMediaType, OutputMediaType, LLMProvider
from core.llms.constants import (
    AZURE_OPENAI_GPT_4O,
    AZURE_OPENAI_GPT_4O_MINI,
    AZURE_OPENAI_GPT_4_TURBO,
    AZURE_OPENAI_GPT_4,
    AZURE_OPENAI_GPT_35_TURBO,
    AZURE_OPENAI_GPT_35_TURBO_16K,
)


def register_azure_models(registry: 'ModelRegistry') -> None:
    """Register all Azure OpenAI models with the global registry"""
    
    # GPT-4o models
    registry.register_model(ModelMetadata(
        model_name=AZURE_OPENAI_GPT_4O,
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_4O,
        display_name="GPT-4o",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=16384,
        max_input_tokens=128000,
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
            "uses_deployment_name": True,
            "requires_api_version": True,
            "supports_response_format": True,
        },
        cost_per_1k_input_tokens=0.005,
        cost_per_1k_output_tokens=0.015,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=AZURE_OPENAI_GPT_4O_MINI,
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_4O,
        display_name="GPT-4o Mini",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.IMAGE, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=16384,
        max_input_tokens=128000,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_version": True,
            "supports_response_format": True,
        },
        cost_per_1k_input_tokens=0.00015,
        cost_per_1k_output_tokens=0.0006,
    ))
    
    # GPT-4 models
    registry.register_model(ModelMetadata(
        model_name=AZURE_OPENAI_GPT_4_TURBO,
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_4,
        display_name="GPT-4 Turbo",
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_json_mode=True,
        max_context_length=128000,
        max_output_tokens=4096,
        max_input_tokens=128000,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_version": True,
            "supports_response_format": True,
        },
        cost_per_1k_input_tokens=0.01,
        cost_per_1k_output_tokens=0.03,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=AZURE_OPENAI_GPT_4,
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_4,
        display_name="GPT-4",
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_json_mode=True,
        max_context_length=8192,
        max_output_tokens=4096,
        max_input_tokens=8192,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_version": True,
            "supports_response_format": True,
        },
        cost_per_1k_input_tokens=0.03,
        cost_per_1k_output_tokens=0.06,
    ))
    
    # GPT-3.5 models
    registry.register_model(ModelMetadata(
        model_name=AZURE_OPENAI_GPT_35_TURBO,
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_35,
        display_name="GPT-3.5 Turbo",
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_json_mode=True,
        max_context_length=16385,
        max_output_tokens=4096,
        max_input_tokens=16385,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_version": True,
            "supports_response_format": True,
        },
        cost_per_1k_input_tokens=0.0005,
        cost_per_1k_output_tokens=0.0015,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=AZURE_OPENAI_GPT_35_TURBO_16K,
        provider=LLMProvider.AZURE_OPENAI,
        model_family=ModelFamily.AZURE_GPT_35,
        display_name="GPT-3.5 Turbo 16K",
        supported_input_types={InputMediaType.TEXT},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_json_mode=False,  # Older variant, limited JSON support
        max_context_length=16385,
        max_output_tokens=4096,
        max_input_tokens=16385,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "frequency_penalty": "frequency_penalty",
            "presence_penalty": "presence_penalty",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        },
        api_requirements={
            "uses_deployment_name": True,
            "requires_api_version": True,
            "supports_response_format": False,  # No response_format support
        },
        cost_per_1k_input_tokens=0.003,
        cost_per_1k_output_tokens=0.004,
        is_deprecated=True,
        deprecation_date="2024-09-13",
        replacement_model=AZURE_OPENAI_GPT_35_TURBO,
    ))

