"""
Azure OpenAI request converter.
"""

from typing import Dict, Any, List
from core.llms.models import get_model_capabilities, MODEL_PARAMETER_DEFAULTS
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

    Args:
        messages: Unified message format
        model_name: Azure OpenAI model name
        **kwargs: Additional parameters

    Returns:
        Azure OpenAI specific request parameters
    """
    capabilities = get_model_capabilities(model_name)
    if not capabilities:
        raise ValueError(f"Unsupported model: {model_name}")

    # Get model-specific defaults
    defaults = MODEL_PARAMETER_DEFAULTS.get(model_name, {})

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

    # Handle JSON mode
    if JSON_MODE in kwargs and kwargs[JSON_MODE] and capabilities.supports_json_mode:
        request_params["response_format"] = {"type": JSON_OBJECT_TYPE}

    # Handle streaming
    if STREAMING in kwargs:
        request_params["stream"] = kwargs[STREAMING]

    return request_params
