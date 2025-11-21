"""
Base LLM Implementation.

This module provides the abstract base class for all LLM implementations.
All LLMs implement just 2 core methods: get_answer and stream_answer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncIterator, Optional
from ..spec.llm_types import ModelMetadata
from ..spec.llm_result import LLMResponse, LLMStreamChunk, LLMUsage
from ..spec.llm_context import LLMContext
from ..exceptions import InputValidationError, TokenLimitError
from ..runtimes.base_connector import BaseConnector
from ..constants import CHARS_PER_TOKEN_ESTIMATE, TOKENS_PER_MESSAGE_OVERHEAD


class BaseLLM(ABC):
    """
    Abstract base class for all LLM implementations.
    
    All LLMs must implement 2 core methods:
    1. get_answer() - Complete response (non-streaming)
    2. stream_answer() - Streaming response
    
    The base class provides:
    - Metadata storage and access
    - Parameter validation and merging
    - Token estimation
    - Cost calculation
    - Capability queries
    
    Attributes:
        metadata: Model metadata with capabilities and limits
        connector: Provider connector for API communication
    """
    
    def __init__(self, metadata: ModelMetadata, connector: 'BaseConnector'):
        """
        Initialize base LLM.
        
        Args:
            metadata: Model metadata
            connector: Provider connector
        """
        self.metadata = metadata
        self.connector = connector
    
    @abstractmethod
    async def get_answer(
        self,
        messages: List[Dict[str, Any]],
        ctx: LLMContext,
        **kwargs: Any
    ) -> LLMResponse:
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
            TokenLimitError: If token limits exceeded
            
        Example:
            messages = [{"role": "user", "content": "Hello!"}]
            response = await llm.get_answer(messages, ctx, temperature=0.7)
            print(response.content)
        """
        pass
    
    @abstractmethod
    async def stream_answer(
        self,
        messages: List[Dict[str, Any]],
        ctx: LLMContext,
        **kwargs: Any
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Get a streaming response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            ctx: LLM context with request metadata
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Yields:
            LLMStreamChunk objects as content is generated
            
        Raises:
            InputValidationError: If input is invalid
            TokenLimitError: If token limits exceeded
            
        Example:
            messages = [{"role": "user", "content": "Tell a story"}]
            async for chunk in llm.stream_answer(messages, ctx):
                print(chunk.content, end='', flush=True)
        """
        pass
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_supported_capabilities(self) -> Dict[str, Any]:
        """
        Get capabilities supported by this LLM.
        
        Returns:
            Dictionary with capability information
        """
        provider = self.metadata.provider
        provider_str = provider if isinstance(provider, str) else provider.value
        
        return {
            "provider": provider_str,
            "model_name": self.metadata.model_name,
            "supported_input_types": [
                t if isinstance(t, str) else t.value 
                for t in self.metadata.supported_input_types
            ],
            "supported_output_types": [
                t if isinstance(t, str) else t.value 
                for t in self.metadata.supported_output_types
            ],
            "supports_streaming": self.metadata.supports_streaming,
            "supports_function_calling": self.metadata.supports_function_calling,
            "supports_vision": self.metadata.supports_vision,
            "supports_json_mode": self.metadata.supports_json_mode,
            "max_context_length": self.metadata.max_context_length,
            "max_output_tokens": self.metadata.max_output_tokens,
        }
    
    def _merge_parameters(self, user_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user parameters with model defaults.
        
        Args:
            user_params: User-provided parameters
            
        Returns:
            Merged parameters
        """
        merged = self.metadata.default_parameters.copy()
        merged.update({k: v for k, v in user_params.items() if v is not None})
        return merged
    
    def _apply_parameter_mappings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map standard parameter names to provider-specific names.
        
        Args:
            params: Parameters with standard names
            
        Returns:
            Parameters with provider-specific names
        """
        mapped = {}
        for key, value in params.items():
            mapped_key = self.metadata.get_parameter_mapping(key)
            mapped[mapped_key] = value
        return mapped
    
    def _validate_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Validate message format and content.
        
        Args:
            messages: Messages to validate
            
        Raises:
            InputValidationError: If messages are invalid
        """
        if not messages:
            raise InputValidationError(
                "Messages list cannot be empty",
                model_name=self.metadata.model_name
            )
        
        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise InputValidationError(
                    f"Message {i} must be a dictionary",
                    model_name=self.metadata.model_name
                )
            
            if "role" not in msg:
                raise InputValidationError(
                    f"Message {i} missing 'role' field",
                    model_name=self.metadata.model_name
                )
            
            if "content" not in msg:
                raise InputValidationError(
                    f"Message {i} missing 'content' field",
                    model_name=self.metadata.model_name
                )
    
    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate token count for messages.
        
        Uses simple heuristic: ~4 chars per token + message overhead.
        
        Args:
            messages: Messages to estimate
            
        Returns:
            Estimated token count
        """
        total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
        estimated_tokens = (total_chars // CHARS_PER_TOKEN_ESTIMATE) + (len(messages) * TOKENS_PER_MESSAGE_OVERHEAD)
        return estimated_tokens
    
    def _validate_token_limits(
        self,
        messages: List[Dict[str, Any]],
        max_output_tokens: Optional[int] = None
    ) -> None:
        """
        Validate that token limits won't be exceeded.
        
        Args:
            messages: Input messages
            max_output_tokens: Requested max output tokens
            
        Raises:
            TokenLimitError: If limits would be exceeded
        """
        estimated_input = self._estimate_tokens(messages)
        requested_output = max_output_tokens or self.metadata.max_output_tokens
        
        if estimated_input > self.metadata.max_context_length:
            raise TokenLimitError(
                f"Input tokens ({estimated_input}) exceed max context length ({self.metadata.max_context_length})",
                model_name=self.metadata.model_name,
                token_count=estimated_input,
                token_limit=self.metadata.max_context_length
            )
        
        total_estimated = estimated_input + requested_output
        if total_estimated > self.metadata.max_context_length:
            raise TokenLimitError(
                f"Total tokens ({total_estimated}) would exceed max context length ({self.metadata.max_context_length})",
                model_name=self.metadata.model_name,
                token_count=total_estimated,
                token_limit=self.metadata.max_context_length
            )
    
    def _calculate_cost(self, usage: LLMUsage) -> Optional[float]:
        """
        Calculate cost based on usage.
        
        Args:
            usage: Usage statistics
            
        Returns:
            Estimated cost in USD, or None if pricing unavailable
        """
        return self.metadata.estimate_cost(
            usage.prompt_tokens,
            usage.completion_tokens
        )

