"""
Bedrock request converter.
"""

from typing import Dict, Any, List
from core.llms.models import get_model_capabilities, MODEL_PARAMETER_DEFAULTS
from core.llms.constants import (
    TEMPERATURE,
    MAX_TOKENS,
    TOP_P,
    STOP_SEQUENCES,
    JSON_MODE,
    STREAMING,
)


def convert_to_bedrock_request(
    messages: List[Dict[str, Any]],
    model_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convert unified request format to Bedrock specific format.

    Args:
        messages: Unified message format
        model_name: Bedrock model name
        **kwargs: Additional parameters

    Returns:
        Bedrock specific request parameters
    """
    capabilities = get_model_capabilities(model_name)
    if not capabilities:
        raise ValueError(f"Unsupported model: {model_name}")

    # Get model-specific defaults
    defaults = MODEL_PARAMETER_DEFAULTS.get(model_name, {})

    # Build request body for Bedrock
    request_body = {
        "messages": messages,
    }

    # Add parameters based on model capabilities
    if capabilities.supports_temperature and (TEMPERATURE in kwargs or TEMPERATURE in defaults):
        request_body["temperature"] = kwargs.get(TEMPERATURE, defaults.get(TEMPERATURE, 0.7))

    if capabilities.supports_max_tokens and (MAX_TOKENS in kwargs or MAX_TOKENS in defaults):
        request_body["max_tokens"] = kwargs.get(MAX_TOKENS, defaults.get(MAX_TOKENS, 4096))

    if capabilities.supports_top_p and (TOP_P in kwargs or TOP_P in defaults):
        request_body["top_p"] = kwargs.get(TOP_P, defaults.get(TOP_P, 1.0))

    if capabilities.supports_stop_sequences and STOP_SEQUENCES in kwargs:
        request_body["stop_sequences"] = kwargs[STOP_SEQUENCES]

    # Handle JSON mode for Claude models
    if JSON_MODE in kwargs and kwargs[JSON_MODE] and capabilities.supports_json_mode:
        # For Claude, we need to add a system message instructing JSON output
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += "\n\nRespond only with valid JSON. No other text."
        else:
            messages.insert(0, {
                "role": "system",
                "content": "Respond only with valid JSON. No other text."
            })

    return request_body
