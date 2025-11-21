"""
LLM Result Models.

This module defines the data models for LLM responses, including
complete responses and streaming chunks.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from ..enum import FinishReason


class LLMUsage(BaseModel):
    """
    Usage statistics for an LLM request.
    
    Tracks token consumption and timing information.
    
    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens used (prompt + completion)
        duration_ms: Request duration in milliseconds
        cost_usd: Estimated cost in USD (optional)
    """
    
    prompt_tokens: int = Field(default=0, ge=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(default=0, ge=0, description="Number of tokens in the completion")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens used")
    duration_ms: Optional[int] = Field(default=None, ge=0, description="Request duration in milliseconds")
    cost_usd: Optional[float] = Field(default=None, ge=0, description="Estimated cost in USD")
    
    def model_post_init(self, __context: Any) -> None:
        """Calculate total_tokens if not provided."""
        if self.total_tokens == 0 and (self.prompt_tokens > 0 or self.completion_tokens > 0):
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class LLMResponse(BaseModel):
    """
    Complete response from an LLM (non-streaming).
    
    Contains the generated content, metadata, and usage statistics.
    
    Attributes:
        content: The generated content (usually text)
        role: Role of the response (usually 'assistant')
        finish_reason: Why generation stopped
        usage: Token usage and timing statistics
        metadata: Additional response metadata
        function_call: Function call data if applicable
        tool_calls: Tool calls if applicable
    
    Example:
        response = LLMResponse(
            content="The answer is 42",
            role="assistant",
            finish_reason=FinishReason.STOP,
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5)
        )
    """
    
    content: Any = Field(description="Generated content")
    role: str = Field(default="assistant", description="Response role")
    finish_reason: Optional[FinishReason] = Field(default=None, description="Why generation stopped")
    usage: Optional[LLMUsage] = Field(default=None, description="Token usage statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    function_call: Optional[Dict[str, Any]] = Field(default=None, description="Function call data")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Tool calls")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Hello! How can I help you today?",
                    "role": "assistant",
                    "finish_reason": "stop",
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 8,
                        "total_tokens": 18
                    }
                }
            ]
        }
    }
    
    def get_text_content(self) -> str:
        """
        Get content as text string.
        
        Returns:
            Text content, converting if necessary
        """
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, dict) and 'text' in self.content:
            return self.content['text']
        return str(self.content)
    
    def has_function_call(self) -> bool:
        """Check if response contains a function call."""
        return self.function_call is not None
    
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class LLMStreamChunk(BaseModel):
    """
    A chunk from a streaming LLM response.
    
    Represents a fragment of content as it's being generated.
    
    Attributes:
        content: Content fragment (usually partial text)
        role: Role of the content (usually 'assistant')
        is_final: Whether this is the last chunk
        finish_reason: Why generation stopped (only on final chunk)
        usage: Usage statistics (usually only on final chunk)
        metadata: Additional chunk metadata
        delta: Raw delta object from provider
    
    Example:
        chunk = LLMStreamChunk(
            content="Hello",
            role="assistant",
            is_final=False
        )
    """
    
    content: str = Field(default="", description="Content fragment")
    role: Optional[str] = Field(default="assistant", description="Content role")
    is_final: bool = Field(default=False, description="Whether this is the last chunk")
    finish_reason: Optional[FinishReason] = Field(default=None, description="Why generation stopped")
    usage: Optional[LLMUsage] = Field(default=None, description="Usage statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    delta: Optional[Dict[str, Any]] = Field(default=None, description="Raw delta from provider")
    
    def is_empty(self) -> bool:
        """Check if chunk has no content."""
        return len(self.content) == 0
    
    def has_usage(self) -> bool:
        """Check if chunk includes usage statistics."""
        return self.usage is not None


class LLMError(BaseModel):
    """
    Error information from an LLM request.
    
    Used to structure error responses in a consistent way.
    
    Attributes:
        error_type: Type/category of error
        message: Error message
        code: Provider-specific error code
        details: Additional error details
    """
    
    error_type: str = Field(description="Error type/category")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(default=None, description="Provider error code")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")


# Helper functions for creating responses

def create_response(
    content: Any,
    usage: Optional[LLMUsage] = None,
    finish_reason: Optional[FinishReason] = None,
    **kwargs
) -> LLMResponse:
    """
    Helper to create an LLMResponse.
    
    Args:
        content: Generated content
        usage: Optional usage statistics
        finish_reason: Optional finish reason
        **kwargs: Additional fields
        
    Returns:
        LLMResponse instance
    """
    return LLMResponse(
        content=content,
        usage=usage,
        finish_reason=finish_reason,
        **kwargs
    )


def create_chunk(
    content: str,
    is_final: bool = False,
    usage: Optional[LLMUsage] = None,
    **kwargs
) -> LLMStreamChunk:
    """
    Helper to create an LLMStreamChunk.
    
    Args:
        content: Content fragment
        is_final: Whether this is the final chunk
        usage: Optional usage statistics
        **kwargs: Additional fields
        
    Returns:
        LLMStreamChunk instance
    """
    return LLMStreamChunk(
        content=content,
        is_final=is_final,
        usage=usage,
        **kwargs
    )


def create_usage(
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: Optional[int] = None,
    cost_usd: Optional[float] = None
) -> LLMUsage:
    """
    Helper to create LLMUsage.
    
    Args:
        prompt_tokens: Prompt tokens used
        completion_tokens: Completion tokens used
        duration_ms: Optional duration
        cost_usd: Optional cost
        
    Returns:
        LLMUsage instance
    """
    return LLMUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        duration_ms=duration_ms,
        cost_usd=cost_usd
    )

