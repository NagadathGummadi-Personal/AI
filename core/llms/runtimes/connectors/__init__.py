"""
Connectors for LLM Providers.

This module provides HTTP client implementations for different LLM providers.
Connectors handle low-level communication: authentication, requests, retries.
"""

from .openai_connector import OpenAIConnector
from .azure_connector import AzureConnector

__all__ = [
    "OpenAIConnector",
    "AzureConnector",
]

