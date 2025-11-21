"""
LLM Subsystem for AI Core.

This module provides a unified interface for working with Large Language Models
from different providers (OpenAI, Azure, etc.).

Architecture:
=============
All LLMs implement ILLM interface with just 2 methods:
1. get_answer() - Complete response
2. stream_answer() - Streaming response

Usage:
======
    from core.llms import LLMFactory, LLMContext
    
    # Create LLM
    llm = LLMFactory.create_llm(
        "gpt-4o",
        connector_config={"api_key": "sk-..."}
    )
    
    # Get answer
    messages = [{"role": "user", "content": "Hello!"}]
    response = await llm.get_answer(messages, LLMContext(), temperature=0.7)
    print(response.content)
    
    # Stream answer
    async for chunk in llm.stream_answer(messages, LLMContext()):
        print(chunk.content, end='', flush=True)

Available Models:
=================
    from core.llms import LLMFactory
    
    models = LLMFactory.list_available_models()
    print(f"Available: {models}")
"""

# Core interfaces
from .interfaces import ILLM, IConnector, IModelRegistry

# Enums
from .enum import (
    LLMProvider,
    ModelFamily,
    InputMediaType,
    OutputMediaType,
    MessageRole,
    LLMCapability,
    LLMType,
    StreamEventType,
    FinishReason,
)

# Exceptions
from .exceptions import (
    LLMError,
    InputValidationError,
    ProviderError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    QuotaExceededError,
    ServiceUnavailableError,
    JSONParsingError,
    InvalidResponseError,
    TokenLimitError,
    ModelNotFoundError,
    StreamingError,
    ContentFilterError,
)

# Spec
from .spec import (
    ModelMetadata,
    LLMResponse,
    LLMStreamChunk,
    LLMUsage,
    LLMContext,
    create_model_metadata,
    create_response,
    create_chunk,
    create_usage,
    create_context,
    create_test_context,
)

# Runtimes
from .runtimes import (
    BaseLLM,
    BaseConnector,
    ModelRegistry,
    get_model_registry,
    reset_registry,
    LLMFactory,
    OpenAIConnector,
    OpenAILLM,
    AzureConnector,
    AzureLLM,
)

__all__ = [
    # Interfaces
    "ILLM",
    "IConnector",
    "IModelRegistry",
    # Enums
    "LLMProvider",
    "ModelFamily",
    "InputMediaType",
    "OutputMediaType",
    "MessageRole",
    "LLMCapability",
    "LLMType",
    "StreamEventType",
    "FinishReason",
    # Exceptions
    "LLMError",
    "InputValidationError",
    "ProviderError",
    "ConfigurationError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError",
    "QuotaExceededError",
    "ServiceUnavailableError",
    "JSONParsingError",
    "InvalidResponseError",
    "TokenLimitError",
    "ModelNotFoundError",
    "StreamingError",
    "ContentFilterError",
    # Spec
    "ModelMetadata",
    "LLMResponse",
    "LLMStreamChunk",
    "LLMUsage",
    "LLMContext",
    "create_model_metadata",
    "create_response",
    "create_chunk",
    "create_usage",
    "create_context",
    "create_test_context",
    # Runtimes
    "BaseLLM",
    "BaseConnector",
    "ModelRegistry",
    "get_model_registry",
    "reset_registry",
    "LLMFactory",
    "OpenAIConnector",
    "OpenAILLM",
    "AzureConnector",
    "AzureLLM",
]

