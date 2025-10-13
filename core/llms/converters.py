"""
Unified request converters for different LLM providers and models.
"""

from typing import Dict, Any, List

# Import converters from provider-specific modules
from .connectors.azure.converter import convert_to_azure_openai_request
from .connectors.bedrock.converter import convert_to_bedrock_request
from .connectors.gemini.converter import convert_to_gemini_request
from .models import get_model_capabilities


# Unified converter function
def convert_request(
    messages: List[Dict[str, Any]], model_name: str, provider_type: str = None, **kwargs
) -> Dict[str, Any]:
    """
    Convert unified request format to provider-specific format.

    Args:
        messages: Unified message format
        model_name: Model name
        provider_type: Provider type (auto-detected if not provided)
        **kwargs: Additional parameters

    Returns:
        Provider-specific request parameters
    """
    capabilities = get_model_capabilities(model_name)
    if not capabilities:
        raise ValueError(f"Unsupported model: {model_name}")

    provider = capabilities.provider

    if provider.value == "azure_openai":
        return convert_to_azure_openai_request(messages, model_name, **kwargs)
    elif provider.value == "bedrock":
        return convert_to_bedrock_request(messages, model_name, **kwargs)
    elif provider.value == "gemini":
        return convert_to_gemini_request(messages, model_name, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# Re-export converter functions for direct access
__all__ = [
    "convert_request",
    "convert_to_azure_openai_request",
    "convert_to_bedrock_request",
    "convert_to_gemini_request",
]
