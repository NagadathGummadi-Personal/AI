"""
LLM interfaces for the AI Agent SDK.
"""

from abc import abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol, runtime_checkable

from .enums import InputMediaType


class LLMResponse:
    """Response object from LLM operations"""

    def __init__(self, content: Any, usage: Optional[Dict[str, Any]] = None):
        self.content = content
        self.usage = usage or {}


class LLMStreamChunk:
    """Streaming chunk from LLM operations"""

    def __init__(self, content: str, is_final: bool = False):
        self.content = content
        self.is_final = is_final
        self.usage: Optional[Dict[str, Any]] = None


@runtime_checkable
class ILLM(Protocol):
    """Interface for LLM implementations"""

    @abstractmethod
    async def get_answer(self, messages: List[Dict[str, Any]], **kwargs) -> LLMResponse:
        """
        Get a complete response from the LLM

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with content and usage information
        """
        ...

    @abstractmethod
    async def get_stream(
        self, messages: List[Dict[str, Any]], **kwargs
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Get a streaming response from the LLM

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters

        Yields:
            LLMStreamChunk objects with content and final flag
        """
        ...

    @abstractmethod
    async def jump_start(self) -> bool:
        """
        Test connectivity to the LLM provider

        Returns:
            True if connection is successful, False otherwise
        """
        ...

    @abstractmethod
    def validate_input(self, input_type: InputMediaType, content: Any) -> bool:
        """
        Validate input for the given input type

        Args:
            input_type: Type of input to validate
            content: Content to validate

        Returns:
            True if valid, False otherwise

        Raises:
            InputValidationError: If input is invalid
        """
        ...

    @abstractmethod
    def get_supported_capabilities(self) -> Dict[str, Any]:
        """
        Get information about supported capabilities

        Returns:
            Dictionary with provider info, supported inputs/outputs, streaming support
        """
        ...


# !TODO: Remove this interface
@runtime_checkable
class ILLMConnector(Protocol):
    """Interface for LLM provider connectors"""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the provider"""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the provider"""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active"""
        ...
