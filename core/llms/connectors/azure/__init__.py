"""
Azure OpenAI connectors for different model types.
"""

from .azure_llm import AzureLLM
from .converter import convert_to_azure_openai_request
from .tool_converter import AzureOpenAIToolConverter
from .models import (
    AzureOpenAIModel,
    AZURE_MODEL_CAPABILITIES,
    AZURE_MODEL_PARAMETER_DEFAULTS,
)
from .model_registry import register_azure_models

__all__ = [
    "AzureLLM",
    "convert_to_azure_openai_request", 
    "AzureOpenAIToolConverter",
    "AzureOpenAIModel",
    "AZURE_MODEL_CAPABILITIES",
    "AZURE_MODEL_PARAMETER_DEFAULTS",
    "register_azure_models",
]
