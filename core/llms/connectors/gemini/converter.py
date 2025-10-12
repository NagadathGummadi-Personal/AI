"""
Gemini request converter.
"""

from typing import Dict, Any, List
from core.llms.models import get_model_capabilities, MODEL_PARAMETER_DEFAULTS
from core.llms.constants import (
    TEMPERATURE,
    MAX_TOKENS,
    TOP_P,
    STOP_SEQUENCES,
    STREAMING,
    GEMINI_SAFETY_HARM_CATEGORY_HARASSMENT,
    GEMINI_SAFETY_HARM_CATEGORY_HATE_SPEECH,
    GEMINI_SAFETY_HARM_CATEGORY_SEXUALLY_EXPLICIT,
    GEMINI_SAFETY_HARM_CATEGORY_DANGEROUS_CONTENT,
    GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE,
)


def convert_to_gemini_request(
    messages: List[Dict[str, Any]],
    model_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convert unified request format to Gemini specific format.

    Args:
        messages: Unified message format
        model_name: Gemini model name
        **kwargs: Additional parameters

    Returns:
        Gemini specific request parameters
    """
    capabilities = get_model_capabilities(model_name)
    if not capabilities:
        raise ValueError(f"Unsupported model: {model_name}")

    # Get model-specific defaults
    defaults = MODEL_PARAMETER_DEFAULTS.get(model_name, {})

    # Build generation config for Gemini
    generation_config = {}

    if capabilities.supports_temperature and (TEMPERATURE in kwargs or TEMPERATURE in defaults):
        generation_config["temperature"] = kwargs.get(TEMPERATURE, defaults.get(TEMPERATURE, 0.7))

    if capabilities.supports_max_tokens and (MAX_TOKENS in kwargs or MAX_TOKENS in defaults):
        # Gemini uses max_output_tokens instead of max_tokens
        max_output_tokens = kwargs.get(MAX_TOKENS, defaults.get(MAX_TOKENS, 8192))
        generation_config["max_output_tokens"] = max_output_tokens

    if capabilities.supports_top_p and (TOP_P in kwargs or TOP_P in defaults):
        generation_config["top_p"] = kwargs.get(TOP_P, defaults.get(TOP_P, 1.0))

    # Gemini doesn't support frequency_penalty or presence_penalty in the same way
    # These would need to be handled differently if needed

    if capabilities.supports_stop_sequences and STOP_SEQUENCES in kwargs:
        # Gemini uses stop_sequences in safety_settings or as a separate parameter
        generation_config["stop_sequences"] = kwargs[STOP_SEQUENCES]

    request_params = {
        "generation_config": generation_config,
    }

    # Handle safety settings (Gemini specific)
    safety_settings = [
        {
            "category": GEMINI_SAFETY_HARM_CATEGORY_HARASSMENT,
            "threshold": GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE
        },
        {
            "category": GEMINI_SAFETY_HARM_CATEGORY_HATE_SPEECH,
            "threshold": GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE
        },
        {
            "category": GEMINI_SAFETY_HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "threshold": GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE
        },
        {
            "category": GEMINI_SAFETY_HARM_CATEGORY_DANGEROUS_CONTENT,
            "threshold": GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE
        },
    ]
    request_params["safety_settings"] = safety_settings

    return request_params
