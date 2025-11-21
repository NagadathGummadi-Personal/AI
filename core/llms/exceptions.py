"""
Exceptions for LLM Subsystem.

This module defines all exception types used throughout the LLM subsystem,
providing a clear hierarchy for error handling and reporting.
"""

from typing import Optional, Dict, Any


class LLMError(Exception):
    """
    Base exception for all LLM-related errors.
    
    All LLM subsystem exceptions inherit from this base class,
    making it easy to catch all LLM-related errors.
    
    Attributes:
        message: Error message
        provider: Optional provider identifier
        model_name: Optional model name
        details: Optional additional error details
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.provider = provider
        self.model_name = model_name
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.model_name:
            parts.append(f"Model: {self.model_name}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class InputValidationError(LLMError):
    """
    Raised when input validation fails.
    
    This includes invalid message formats, unsupported media types,
    or malformed input data.
    
    Example:
        raise InputValidationError(
            "Unsupported input type: audio",
            model_name="gpt-4",
            details={"input_type": "audio", "supported": ["text", "image"]}
        )
    """
    pass


class ProviderError(LLMError):
    """
    Raised when a provider-specific error occurs.
    
    This is a general error for provider-level issues that don't
    fit into more specific categories.
    
    Example:
        raise ProviderError(
            "Provider returned unexpected response format",
            provider="azure",
            details={"response_format": "xml"}
        )
    """
    pass


class ConfigurationError(LLMError):
    """
    Raised when configuration is invalid or incomplete.
    
    This includes missing API keys, invalid endpoints, or
    misconfigured connector settings.
    
    Example:
        raise ConfigurationError(
            "Missing API key",
            provider="openai",
            details={"env_var": "OPENAI_API_KEY"}
        )
    """
    pass


class AuthenticationError(LLMError):
    """
    Raised when authentication fails.
    
    This indicates invalid credentials, expired tokens, or
    unauthorized access attempts.
    
    Example:
        raise AuthenticationError(
            "Invalid API key",
            provider="azure",
            details={"status_code": 401}
        )
    """
    pass


class RateLimitError(LLMError):
    """
    Raised when rate limits are exceeded.
    
    Providers typically return this when request quotas or
    rate limits have been reached.
    
    Attributes:
        retry_after: Optional seconds to wait before retrying
    
    Example:
        raise RateLimitError(
            "Rate limit exceeded",
            provider="openai",
            details={"retry_after": 60, "limit": "60 requests/minute"}
        )
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, provider, model_name, details)
        self.retry_after = retry_after


class TimeoutError(LLMError):
    """
    Raised when a request times out.
    
    This indicates the request took longer than the configured
    timeout period.
    
    Example:
        raise TimeoutError(
            "Request timed out after 30 seconds",
            provider="azure",
            details={"timeout_seconds": 30}
        )
    """
    pass


class QuotaExceededError(LLMError):
    """
    Raised when usage quotas are exceeded.
    
    This indicates monthly/daily quotas or token limits have
    been reached.
    
    Example:
        raise QuotaExceededError(
            "Monthly token quota exceeded",
            provider="openai",
            model_name="gpt-4",
            details={"quota": 1000000, "used": 1000001}
        )
    """
    pass


class ServiceUnavailableError(LLMError):
    """
    Raised when the service is unavailable.
    
    This indicates the provider's service is down or experiencing
    issues.
    
    Example:
        raise ServiceUnavailableError(
            "Azure OpenAI service is unavailable",
            provider="azure",
            details={"status_code": 503}
        )
    """
    pass


class JSONParsingError(LLMError):
    """
    Raised when JSON parsing fails.
    
    This occurs when the LLM returns invalid JSON in JSON mode
    or when response parsing fails.
    
    Example:
        raise JSONParsingError(
            "Failed to parse LLM response as JSON",
            model_name="gpt-4",
            details={"raw_response": "not valid json{"}
        )
    """
    pass


class InvalidResponseError(LLMError):
    """
    Raised when the provider returns an invalid response.
    
    This indicates unexpected response format or missing required
    fields in the provider's response.
    
    Example:
        raise InvalidResponseError(
            "Response missing 'choices' field",
            provider="openai",
            details={"response_keys": ["id", "object"]}
        )
    """
    pass


class TokenLimitError(LLMError):
    """
    Raised when token limits are exceeded.
    
    This occurs when the input or output exceeds the model's
    maximum token limits.
    
    Attributes:
        token_count: Actual token count
        token_limit: Maximum allowed tokens
    
    Example:
        raise TokenLimitError(
            "Input exceeds maximum context length",
            model_name="gpt-4",
            details={"tokens": 10000, "limit": 8192}
        )
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        token_count: Optional[int] = None,
        token_limit: Optional[int] = None
    ):
        super().__init__(message, provider, model_name, details)
        self.token_count = token_count
        self.token_limit = token_limit


class ModelNotFoundError(LLMError):
    """
    Raised when a requested model is not found.
    
    This occurs when looking up a model in the registry that
    doesn't exist or hasn't been registered.
    
    Example:
        raise ModelNotFoundError(
            "Model not found in registry",
            model_name="unknown-model",
            details={"available_models": ["gpt-4", "gpt-3.5-turbo"]}
        )
    """
    pass


class StreamingError(LLMError):
    """
    Raised when streaming encounters an error.
    
    This includes connection interruptions, malformed stream chunks,
    or streaming-specific protocol errors.
    
    Example:
        raise StreamingError(
            "Stream connection interrupted",
            provider="openai",
            details={"chunks_received": 45}
        )
    """
    pass


class ContentFilterError(LLMError):
    """
    Raised when content is filtered by safety systems.
    
    This occurs when input or output is blocked by content
    moderation or safety filters.
    
    Attributes:
        filter_type: Type of content filter triggered
    
    Example:
        raise ContentFilterError(
            "Content filtered due to policy violation",
            provider="azure",
            details={"filter_type": "hate", "severity": "high"}
        )
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        filter_type: Optional[str] = None
    ):
        super().__init__(message, provider, model_name, details)
        self.filter_type = filter_type


# Utility functions for exception handling

def is_retriable_error(error: Exception) -> bool:
    """
    Determine if an error is retriable.
    
    Args:
        error: Exception to check
        
    Returns:
        True if the error should be retried
    
    Example:
        try:
            result = await llm.get_answer(messages)
        except LLMError as e:
            if is_retriable_error(e):
                # Retry logic
                pass
    """
    retriable_types = (
        RateLimitError,
        TimeoutError,
        ServiceUnavailableError,
        StreamingError,
    )
    return isinstance(error, retriable_types)


def get_error_category(error: Exception) -> str:
    """
    Get the category of an error for logging/metrics.
    
    Args:
        error: Exception to categorize
        
    Returns:
        Error category string
    
    Example:
        category = get_error_category(error)
        metrics.incr(f"llm.errors.{category}")
    """
    if isinstance(error, AuthenticationError):
        return "authentication"
    elif isinstance(error, RateLimitError):
        return "rate_limit"
    elif isinstance(error, TimeoutError):
        return "timeout"
    elif isinstance(error, QuotaExceededError):
        return "quota"
    elif isinstance(error, ServiceUnavailableError):
        return "service_unavailable"
    elif isinstance(error, InputValidationError):
        return "validation"
    elif isinstance(error, TokenLimitError):
        return "token_limit"
    elif isinstance(error, ContentFilterError):
        return "content_filter"
    elif isinstance(error, StreamingError):
        return "streaming"
    elif isinstance(error, LLMError):
        return "llm_error"
    else:
        return "unknown"

