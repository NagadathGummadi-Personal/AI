"""
Amazon Bedrock Model Registry.

Handles registration of all Bedrock models with their complete metadata.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.llms.model_registry import ModelRegistry

from core.llms.model_registry import ModelMetadata, ModelFamily
from core.llms.enums import InputMediaType, OutputMediaType, LLMProvider
from core.llms.constants import (
    BEDROCK_CLAUDE_3_OPUS,
    BEDROCK_CLAUDE_3_SONNET,
    BEDROCK_CLAUDE_3_HAIKU,
    BEDROCK_CLAUDE_35_SONNET,
)


def register_bedrock_models(registry: 'ModelRegistry') -> None:
    """Register all Bedrock models with the global registry"""
    
    # Claude 3.5 models
    registry.register_model(ModelMetadata(
        model_name=BEDROCK_CLAUDE_35_SONNET,
        provider=LLMProvider.BEDROCK,
        model_family=ModelFamily.BEDROCK_CLAUDE_35,
        display_name="Claude 3.5 Sonnet",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=200000,
        max_output_tokens=8192,
        max_input_tokens=200000,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_region": True,
            "body_format": "anthropic",
        },
        cost_per_1k_input_tokens=0.003,
        cost_per_1k_output_tokens=0.015,
    ))
    
    # Claude 3 models
    registry.register_model(ModelMetadata(
        model_name=BEDROCK_CLAUDE_3_OPUS,
        provider=LLMProvider.BEDROCK,
        model_family=ModelFamily.BEDROCK_CLAUDE_3,
        display_name="Claude 3 Opus",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=200000,
        max_output_tokens=4096,
        max_input_tokens=200000,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_region": True,
            "body_format": "anthropic",
        },
        cost_per_1k_input_tokens=0.015,
        cost_per_1k_output_tokens=0.075,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=BEDROCK_CLAUDE_3_SONNET,
        provider=LLMProvider.BEDROCK,
        model_family=ModelFamily.BEDROCK_CLAUDE_3,
        display_name="Claude 3 Sonnet",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=200000,
        max_output_tokens=4096,
        max_input_tokens=200000,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_region": True,
            "body_format": "anthropic",
        },
        cost_per_1k_input_tokens=0.003,
        cost_per_1k_output_tokens=0.015,
    ))
    
    registry.register_model(ModelMetadata(
        model_name=BEDROCK_CLAUDE_3_HAIKU,
        provider=LLMProvider.BEDROCK,
        model_family=ModelFamily.BEDROCK_CLAUDE_3,
        display_name="Claude 3 Haiku",
        supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE, InputMediaType.MULTIMODAL},
        supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_json_mode=True,
        max_context_length=200000,
        max_output_tokens=4096,
        max_input_tokens=200000,
        parameter_mappings={
            "max_tokens": "max_tokens",
            "temperature": "temperature",
            "top_p": "top_p",
            "stop": "stop_sequences",
        },
        default_parameters={
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 1.0,
        },
        api_requirements={
            "uses_model_id": True,
            "requires_region": True,
            "body_format": "anthropic",
        },
        cost_per_1k_input_tokens=0.00025,
        cost_per_1k_output_tokens=0.00125,
    ))

