"""
Default values and configurations for LLM Subsystem.

This module provides default values, configuration helpers, and
standard defaults for LLM operations.
"""

from typing import Dict, Any, Optional
from .enum import LLMProvider, MessageRole
from .constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TOP_P,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    META_MODEL_NAME,
    META_PROVIDER,
)


# ============================================================================
# DEFAULT PARAMETERS
# ============================================================================

DEFAULT_LLM_PARAMETERS = {
    "temperature": DEFAULT_TEMPERATURE,
    "max_tokens": DEFAULT_MAX_TOKENS,
    "top_p": DEFAULT_TOP_P,
    "frequency_penalty": DEFAULT_FREQUENCY_PENALTY,
    "presence_penalty": DEFAULT_PRESENCE_PENALTY,
}


DEFAULT_CONNECTOR_CONFIG = {
    "timeout": DEFAULT_TIMEOUT_SECONDS,
    "max_retries": DEFAULT_MAX_RETRIES,
    "retry_delay": DEFAULT_RETRY_DELAY_SECONDS,
}


# ============================================================================
# OPENAI DEFAULTS
# ============================================================================

OPENAI_DEFAULT_PARAMETERS = {
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "n": 1,
}


OPENAI_CONNECTOR_DEFAULTS = {
    "api_version": None,  # Uses latest by default
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1,
}


# ============================================================================
# AZURE OPENAI DEFAULTS
# ============================================================================

AZURE_DEFAULT_PARAMETERS = {
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
}


AZURE_CONNECTOR_DEFAULTS = {
    "api_version": "2024-02-15-preview",  # Stable version
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1,
}


# ============================================================================
# MESSAGE TEMPLATES
# ============================================================================

def create_system_message(content: str) -> Dict[str, str]:
    """
    Create a standard system message.
    
    Args:
        content: System message content
        
    Returns:
        Formatted system message dict
        
    Example:
        system_msg = create_system_message("You are a helpful assistant.")
    """
    return {
        "role": MessageRole.SYSTEM.value,
        "content": content
    }


def create_user_message(content: str) -> Dict[str, str]:
    """
    Create a standard user message.
    
    Args:
        content: User message content
        
    Returns:
        Formatted user message dict
        
    Example:
        user_msg = create_user_message("Hello, how are you?")
    """
    return {
        "role": MessageRole.USER.value,
        "content": content
    }


def create_assistant_message(content: str) -> Dict[str, str]:
    """
    Create a standard assistant message.
    
    Args:
        content: Assistant message content
        
    Returns:
        Formatted assistant message dict
        
    Example:
        assistant_msg = create_assistant_message("I'm doing well, thank you!")
    """
    return {
        "role": MessageRole.ASSISTANT.value,
        "content": content
    }


# ============================================================================
# CONTEXT DATA GENERATORS
# ============================================================================

def DEFAULT_LLM_CONTEXT_DATA(model_name: str, provider: str, **kwargs) -> Dict[str, Any]:
    """
    Generate default context data for LLM logging and tracking.
    
    Args:
        model_name: Name of the model
        provider: Provider identifier
        **kwargs: Additional context fields
        
    Returns:
        Dictionary with context data
        
    Example:
        context = DEFAULT_LLM_CONTEXT_DATA(
            "gpt-4",
            "openai",
            request_id="req-123"
        )
    """
    context = {
        META_MODEL_NAME: model_name,
        META_PROVIDER: provider,
    }
    context.update(kwargs)
    return context


def LLM_REQUEST_CONTEXT(
    model_name: str,
    provider: str,
    message_count: int,
    estimated_tokens: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate context data for LLM request tracking.
    
    Args:
        model_name: Name of the model
        provider: Provider identifier
        message_count: Number of messages in request
        estimated_tokens: Estimated input tokens
        **kwargs: Additional context fields
        
    Returns:
        Dictionary with request context
        
    Example:
        context = LLM_REQUEST_CONTEXT(
            "gpt-4",
            "openai",
            message_count=3,
            estimated_tokens=150
        )
    """
    context = DEFAULT_LLM_CONTEXT_DATA(model_name, provider)
    context.update({
        "message_count": message_count,
        "estimated_tokens": estimated_tokens,
    })
    context.update(kwargs)
    return context


# ============================================================================
# PARAMETER HELPERS
# ============================================================================

def merge_parameters(
    user_params: Dict[str, Any],
    defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge user parameters with defaults.
    
    User parameters take precedence over defaults.
    
    Args:
        user_params: User-provided parameters
        defaults: Default parameters
        
    Returns:
        Merged parameters
        
    Example:
        params = merge_parameters(
            {"temperature": 0.5},
            DEFAULT_LLM_PARAMETERS
        )
    """
    merged = defaults.copy()
    merged.update({k: v for k, v in user_params.items() if v is not None})
    return merged


def filter_none_values(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from parameters dictionary.
    
    Args:
        params: Parameters dictionary
        
    Returns:
        Filtered parameters
        
    Example:
        params = filter_none_values({
            "temperature": 0.7,
            "max_tokens": None,
            "top_p": 1.0
        })
        # Returns: {"temperature": 0.7, "top_p": 1.0}
    """
    return {k: v for k, v in params.items() if v is not None}


# ============================================================================
# USAGE TEMPLATES
# ============================================================================

def create_empty_usage() -> Dict[str, Any]:
    """
    Create an empty usage dictionary.
    
    Returns:
        Empty usage dict with standard fields
        
    Example:
        usage = create_empty_usage()
    """
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }


def create_usage(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a usage dictionary.
    
    Args:
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total tokens (calculated if not provided)
        
    Returns:
        Usage dictionary
        
    Example:
        usage = create_usage(
            prompt_tokens=100,
            completion_tokens=50
        )
    """
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


# ============================================================================
# PROVIDER-SPECIFIC DEFAULTS
# ============================================================================

PROVIDER_DEFAULTS = {
    LLMProvider.OPENAI: {
        "parameters": OPENAI_DEFAULT_PARAMETERS,
        "connector": OPENAI_CONNECTOR_DEFAULTS,
    },
    LLMProvider.AZURE: {
        "parameters": AZURE_DEFAULT_PARAMETERS,
        "connector": AZURE_CONNECTOR_DEFAULTS,
    },
}


def get_provider_defaults(provider: LLMProvider, category: str = "parameters") -> Dict[str, Any]:
    """
    Get default values for a specific provider.
    
    Args:
        provider: Provider identifier
        category: Category of defaults ("parameters" or "connector")
        
    Returns:
        Provider-specific defaults
        
    Example:
        defaults = get_provider_defaults(LLMProvider.AZURE, "parameters")
    """
    provider_config = PROVIDER_DEFAULTS.get(provider, {})
    return provider_config.get(category, {}).copy()


# ============================================================================
# VALIDATION DEFAULTS
# ============================================================================

DEFAULT_PARAMETER_RANGES = {
    "temperature": (0.0, 2.0),
    "top_p": (0.0, 1.0),
    "frequency_penalty": (-2.0, 2.0),
    "presence_penalty": (-2.0, 2.0),
    "max_tokens": (1, 32000),
}


def get_parameter_range(parameter: str) -> tuple[float, float]:
    """
    Get the valid range for a parameter.
    
    Args:
        parameter: Parameter name
        
    Returns:
        Tuple of (min, max) values
        
    Example:
        min_val, max_val = get_parameter_range("temperature")
    """
    return DEFAULT_PARAMETER_RANGES.get(parameter, (None, None))

