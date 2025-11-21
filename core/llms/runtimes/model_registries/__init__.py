"""
Model Registries.

This module contains model registration functions for different providers.
Each provider registers its models with the global ModelRegistry.
"""

from .openai_models import register_openai_models
from .azure_models import register_azure_models

__all__ = [
    "register_openai_models",
    "register_azure_models",
]

