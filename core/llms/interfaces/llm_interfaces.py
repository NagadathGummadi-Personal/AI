"""
Interfaces for LLM Subsystem.

This module defines the core protocols (interfaces) that all LLM implementations
must follow, ensuring a consistent API across all providers.
"""

from __future__ import annotations
from typing import Any, AsyncIterator, Dict, List, Protocol, runtime_checkable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..spec.llm_result import LLMResponse, LLMStreamChunk
    from ..spec.llm_types import ModelMetadata
    from ..spec.llm_context import LLMContext

# Type aliases for clarity
Messages = List[Dict[str, Any]]
Parameters = Dict[str, Any]


@runtime_checkable
class ILLM(Protocol):
    """
    Core LLM interface - all LLMs implement just 2 methods.
    
    This protocol defines the minimal, consistent API that all LLM
    implementations (OpenAI, Azure, Bedrock, etc.) must implement.
    
    Required Methods:
    1. get_answer() - Complete response (non-streaming)
    2. stream_answer() - Streaming response
    """
    
    async def get_answer(
        self,
        messages: Messages,
        ctx: 'LLMContext',
        **kwargs: Any
    ) -> 'LLMResponse':
        """
        Get a complete response from the LLM (non-streaming).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            ctx: LLM context with request metadata
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with generated content and usage
            
        Raises:
            InputValidationError: If input is invalid
            ProviderError: If provider returns an error
            TokenLimitError: If token limits exceeded
            TimeoutError: If request times out
            
        Example:
            messages = [{"role": "user", "content": "What is 2+2?"}]
            response = await llm.get_answer(messages, ctx, temperature=0.7)
            print(response.content)
        """
        ...
    
    async def stream_answer(
        self,
        messages: Messages,
        ctx: 'LLMContext',
        **kwargs: Any
    ) -> AsyncIterator['LLMStreamChunk']:
        """
        Get a streaming response from the LLM.
        
        Yields chunks of content as they are generated.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            ctx: LLM context with request metadata
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Yields:
            LLMStreamChunk objects with content fragments
            
        Raises:
            InputValidationError: If input is invalid
            StreamingError: If streaming encounters an error
            TokenLimitError: If token limits exceeded
            
        Example:
            messages = [{"role": "user", "content": "Tell me a story"}]
            async for chunk in llm.stream_answer(messages, ctx):
                print(chunk.content, end='', flush=True)
                if chunk.is_final:
                    print(f"\nUsage: {chunk.usage}")
        """
        ...


@runtime_checkable
class IConnector(Protocol):
    """
    Connector interface for LLM provider communication.
    
    Connectors handle the low-level details of communicating with
    LLM providers (authentication, requests, retries, etc.).
    No explicit connection lifecycle needed for HTTP APIs.
    """
    
    async def request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make a request to the provider API.
        
        Args:
            endpoint: API endpoint to call
            payload: Request payload
            **kwargs: Additional request options
            
        Returns:
            Response dictionary
            
        Raises:
            ProviderError: If provider returns an error
            TimeoutError: If request times out
            RateLimitError: If rate limited
        """
        ...
    
    async def test_connection(self) -> bool:
        """
        Test connectivity and authentication (optional).
        
        Returns:
            True if connector is ready
            
        Raises:
            AuthenticationError: If credentials are invalid
            ServiceUnavailableError: If service is down
        """
        ...


@runtime_checkable
class IModelRegistry(Protocol):
    """
    Model registry interface for managing model metadata.
    
    The registry stores and provides access to metadata for all
    registered models.
    """
    
    def register_model(self, metadata: 'ModelMetadata') -> None:
        """
        Register a model with the registry.
        
        Args:
            metadata: Model metadata to register
            
        Raises:
            ValueError: If model is already registered
        """
        ...
    
    def get_model(self, model_name: str) -> Optional['ModelMetadata']:
        """
        Get metadata for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelMetadata if found, None otherwise
        """
        ...
    
    def get_all_models(self) -> Dict[str, 'ModelMetadata']:
        """
        Get all registered models.
        
        Returns:
            Dictionary mapping model names to metadata
        """
        ...
    
    def get_provider_models(self, provider: str) -> List[str]:
        """
        Get all models for a specific provider.
        
        Args:
            provider: Provider identifier
            
        Returns:
            List of model names
        """
        ...
    
    def get_family_models(self, family: str) -> List[str]:
        """
        Get all models in a specific family.
        
        Args:
            family: Model family identifier
            
        Returns:
            List of model names
        """
        ...

