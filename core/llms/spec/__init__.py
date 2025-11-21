"""
Specifications for LLM Subsystem.

This module exports all specification types including metadata,
results, and context objects.
"""

from .llm_types import ModelMetadata, create_model_metadata
from .llm_result import (
    LLMResponse,
    LLMStreamChunk,
    LLMUsage,
    LLMError,
    create_response,
    create_chunk,
    create_usage,
)
from .llm_context import (
    LLMContext,
    create_context,
    create_test_context,
)

__all__ = [
    # Types
    "ModelMetadata",
    "create_model_metadata",
    # Results
    "LLMResponse",
    "LLMStreamChunk",
    "LLMUsage",
    "LLMError",
    "create_response",
    "create_chunk",
    "create_usage",
    # Context
    "LLMContext",
    "create_context",
    "create_test_context",
]

