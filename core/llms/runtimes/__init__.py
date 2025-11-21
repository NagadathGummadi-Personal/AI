"""
Runtimes for LLM Subsystem.

This module provides runtime components for LLM execution including
base classes, connectors, implementations, and the model registry.
"""

from .base_llm import BaseLLM
from .base_connector import BaseConnector
from .model_registry import ModelRegistry, get_model_registry, reset_registry
from .llm_factory import LLMFactory

# Connectors (HTTP clients)
from .connectors import (
    OpenAIConnector,
    AzureConnector,
)

# Implementations (LLM logic)
from .implementations import (
    OpenAILLM,
    AzureLLM,
)

__all__ = [
    # Base classes
    "BaseLLM",
    "BaseConnector",
    # Registry
    "ModelRegistry",
    "get_model_registry",
    "reset_registry",
    # Factory
    "LLMFactory",
    # Connectors
    "OpenAIConnector",
    "AzureConnector",
    # Implementations
    "OpenAILLM",
    "AzureLLM",
]

