"""
Enumerations for LLM Subsystem.

This module defines all enumerations used throughout the LLM subsystem including
providers, model families, media types, roles, and capabilities.
"""

from enum import Enum


class LLMProvider(str, Enum):
    """
    LLM Provider identifiers.
    
    Represents the service provider hosting the LLM.
    """
    AZURE = "azure"
    OPENAI = "openai"
    # BEDROCK = "bedrock"
    # GEMINI = "gemini"
    # ANTHROPIC = "anthropic"


class ModelFamily(str, Enum):
    """
    Model family groupings.
    
    Groups related models together (e.g., all GPT-4 variants).
    """
    # OpenAI families
    GPT_4 = "gpt-4"
    GPT_4_1_MINI = "gpt-4.1-mini"
    
    # Azure OpenAI (same models but deployed on Azure)
    AZURE_GPT_4 = "azure-gpt-4"
    AZURE_GPT_4_1_MINI = "azure-gpt-4.1-mini"
    
    # CLAUDE_3 = "claude-3"
    # CLAUDE_35 = "claude-3.5"
    # GEMINI_PRO = "gemini-pro"
    # GEMINI_ULTRA = "gemini-ultra"


class InputMediaType(str, Enum):
    """
    Supported input media types.
    
    Defines what types of content can be sent to the LLM.
    
    Note: MULTIMODAL indicates the model can handle multiple types in a single
    request. The exact combination is specified in ModelMetadata.supported_input_types
    (e.g., {TEXT, IMAGE} for text+vision, {TEXT, AUDIO} for text+audio, etc.)
    """
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"  # Can mix multiple types - see supported_input_types for specifics


class OutputMediaType(str, Enum):
    """
    Supported output media types.
    
    Defines what types of content the LLM can generate.
    """
    TEXT = 'text'
    JSON = 'json'  # Structured JSON output
    AUDIO = 'audio'
    IMAGE = 'image'
    VIDEO = 'video'
    MULTIMODAL = 'multimodal'


class MessageRole(str, Enum):
    """
    Message role identifiers for conversation context.
    
    Standard roles used in chat-based LLM interactions.
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class LLMCapability(str, Enum):
    """
    LLM capability flags.
    
    Represents specific features or capabilities that a model supports.
    """
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    JSON_MODE = "json_mode"
    TOOL_USE = "tool_use"
    SYSTEM_MESSAGE = "system_message"
    MULTI_TURN = "multi_turn"
    CONTEXT_CACHING = "context_caching"


class LLMType(str, Enum):
    """
    LLM type classification.
    
    Categorizes models by their primary use case or architecture.
    """
    CHAT = "chat"
    COMPLETION = "completion"
    INSTRUCTION = "instruction"
    EMBEDDING = "embedding"
    CODE = "code"


class StreamEventType(str, Enum):
    """
    Stream event types for streaming responses.
    
    Used to classify different types of events in a streaming response.
    """
    START = "start"
    CONTENT = "content"
    FUNCTION_CALL = "function_call"
    TOOL_USE = "tool_use"
    END = "end"
    ERROR = "error"
    METADATA = "metadata"


class FinishReason(str, Enum):
    """
    Reasons why LLM generation stopped.
    
    Standard finish reasons returned by LLM providers.
    """
    STOP = "stop"  # Natural completion
    LENGTH = "length"  # Max tokens reached
    CONTENT_FILTER = "content_filter"  # Filtered by safety
    FUNCTION_CALL = "function_call"  # Function/tool call generated
    ERROR = "error"  # Error occurred
    TIMEOUT = "timeout"  # Request timed out


# Helper function to get all values
def get_all_providers() -> list[str]:
    """Get list of all provider identifiers."""
    return [p.value for p in LLMProvider]


def get_all_model_families() -> list[str]:
    """Get list of all model family identifiers."""
    return [f.value for f in ModelFamily]


def get_all_input_types() -> list[str]:
    """Get list of all input media types."""
    return [t.value for t in InputMediaType]


def get_all_output_types() -> list[str]:
    """Get list of all output media types."""
    return [t.value for t in OutputMediaType]

