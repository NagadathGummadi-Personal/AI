from enum import Enum

from .constants import (
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_AUDIO,
    CONTENT_TYPE_VIDEO,
    CONTENT_TYPE_DOCUMENT,
    CONTENT_TYPE_MULTIMODAL,
    MEDIA_TYPE_TEXT,
    MEDIA_TYPE_AUDIO,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_JSON,
    MEDIA_TYPE_EMBEDDING,
    PROVIDER_AZURE_OPENAI,
    PROVIDER_BEDROCK,
    PROVIDER_GEMINI,
    LLM_TYPE_CHAT,
    LLM_TYPE_COMPLETION,
    LLM_TYPE_EMBEDDING,
    LLM_TYPE_MULTIMODAL,
)


class InputType(str, Enum):
    """Enumeration for LLM input types"""
    TEXT = CONTENT_TYPE_TEXT
    IMAGE = CONTENT_TYPE_IMAGE
    AUDIO = CONTENT_TYPE_AUDIO
    VIDEO = CONTENT_TYPE_VIDEO
    DOCUMENT = CONTENT_TYPE_DOCUMENT
    MULTIMODAL = CONTENT_TYPE_MULTIMODAL


class OutputMediaType(str, Enum):
    """Enumeration for LLM output media types"""
    TEXT = MEDIA_TYPE_TEXT
    AUDIO = MEDIA_TYPE_AUDIO
    IMAGE = MEDIA_TYPE_IMAGE
    JSON = MEDIA_TYPE_JSON
    EMBEDDING = MEDIA_TYPE_EMBEDDING


class LLMProvider(str, Enum):
    """Enumeration for LLM providers"""
    AZURE_OPENAI = PROVIDER_AZURE_OPENAI
    BEDROCK = PROVIDER_BEDROCK
    GEMINI = PROVIDER_GEMINI


class LLMType(str, Enum):
    """Enumeration for LLM types"""
    CHAT = LLM_TYPE_CHAT
    COMPLETION = LLM_TYPE_COMPLETION
    EMBEDDING = LLM_TYPE_EMBEDDING
    MULTIMODAL = LLM_TYPE_MULTIMODAL


class MessageRole(str, Enum):
    """Enumeration for message roles in chat conversations"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
