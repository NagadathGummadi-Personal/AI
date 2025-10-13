"""
Azure OpenAI request converter.

Handles model-specific parameter mappings and API requirements.
"""

from typing import Dict, Any, List
from core.llms.models import get_model_capabilities
from core.llms.model_registry import get_model_metadata
from core.llms.constants import (
    TEMPERATURE,
    MAX_TOKENS,
    TOP_P,
    FREQUENCY_PENALTY,
    PRESENCE_PENALTY,
    STOP_SEQUENCES,
    JSON_MODE,
    STREAMING,
    JSON_OBJECT_TYPE,
)


def convert_to_azure_openai_request(
    messages: List[Dict[str, Any]],
    model_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convert unified request format to Azure OpenAI specific format.
    
    Uses model registry for model-specific parameter mappings and API requirements.

    Args:
        messages: Unified message format
        model_name: Azure OpenAI model name
        **kwargs: Additional parameters

    Returns:
        Azure OpenAI specific request parameters
    """
    # Get model capabilities (for backward compatibility)
    capabilities = get_model_capabilities(model_name)
    if not capabilities:
        raise ValueError(f"Unsupported model: {model_name}")
    
    # Get comprehensive model metadata
    metadata = get_model_metadata(model_name)
    if not metadata:
        # Fallback to basic capabilities if metadata not available
        metadata = None
    
    # Get model-specific defaults
    defaults = metadata.default_parameters if metadata else {}

    # Build request parameters based on model capabilities
    request_params = {
        "model": model_name,
        "messages": messages,
    }

    # Add parameters only if supported by the model
    if capabilities.supports_temperature and (TEMPERATURE in kwargs or TEMPERATURE in defaults):
        request_params["temperature"] = kwargs.get(TEMPERATURE, defaults.get(TEMPERATURE, 0.7))

    if capabilities.supports_max_tokens and (MAX_TOKENS in kwargs or MAX_TOKENS in defaults):
        request_params["max_tokens"] = kwargs.get(MAX_TOKENS, defaults.get(MAX_TOKENS, 4096))

    if capabilities.supports_top_p and (TOP_P in kwargs or TOP_P in defaults):
        request_params["top_p"] = kwargs.get(TOP_P, defaults.get(TOP_P, 1.0))

    if capabilities.supports_frequency_penalty and (FREQUENCY_PENALTY in kwargs or FREQUENCY_PENALTY in defaults):
        request_params["frequency_penalty"] = kwargs.get(FREQUENCY_PENALTY, defaults.get(FREQUENCY_PENALTY, 0.0))

    if capabilities.supports_presence_penalty and (PRESENCE_PENALTY in kwargs or PRESENCE_PENALTY in defaults):
        request_params["presence_penalty"] = kwargs.get(PRESENCE_PENALTY, defaults.get(PRESENCE_PENALTY, 0.0))

    if capabilities.supports_stop_sequences and STOP_SEQUENCES in kwargs:
        request_params["stop"] = kwargs[STOP_SEQUENCES]

    # Handle JSON mode (check both capabilities and API requirements)
    if JSON_MODE in kwargs and kwargs[JSON_MODE] and capabilities.supports_json_mode:
        # Check if model supports response_format API parameter
        supports_response_format = True
        if metadata and metadata.api_requirements:
            supports_response_format = metadata.api_requirements.get("supports_response_format", True)
        
        if supports_response_format:
            request_params["response_format"] = {"type": JSON_OBJECT_TYPE}

    # Handle streaming
    if STREAMING in kwargs:
        request_params["stream"] = kwargs[STREAMING]
    
    # Validate parameters for model-specific constraints
    if metadata:
        # Use model-specific parameter mappings if available
        mapped_params = {}
        for key, value in request_params.items():
            if key in metadata.parameter_mappings:
                mapped_key = metadata.parameter_mappings[key]
                mapped_params[mapped_key] = value
            else:
                mapped_params[key] = value
        
        # Note: In this case Azure OpenAI uses standard parameter names,
        # but this pattern allows for provider-specific mappings
        request_params = mapped_params

    return request_params
