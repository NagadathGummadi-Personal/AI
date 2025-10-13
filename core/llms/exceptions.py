"""
LLM-specific exception classes for the AI Agent SDK.
"""


class LLMError(Exception):
    """Base exception for all LLM-related errors"""

    pass


class InputValidationError(LLMError):
    """Raised when LLM input validation fails"""

    pass


class ProviderError(LLMError):
    """Raised when there's an error with the LLM provider"""

    pass


class ConfigurationError(LLMError):
    """Raised when LLM configuration is invalid"""

    pass


class RateLimitError(LLMError):
    """Raised when rate limit is exceeded"""

    pass


class JSONParsingError(LLMError):
    """Raised when JSON response parsing fails"""

    pass


class TimeoutError(LLMError):
    """Raised when LLM request times out"""

    pass


class AuthenticationError(LLMError):
    """Raised when authentication with LLM provider fails"""

    pass


class QuotaExceededError(LLMError):
    """Raised when API quota is exceeded"""

    pass


class ServiceUnavailableError(LLMError):
    """Raised when LLM service is unavailable"""

    pass


class InvalidResponseError(LLMError):
    """Raised when LLM returns an invalid response"""

    pass
