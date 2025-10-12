"""
Base LLM implementation for the AI Agent SDK.
"""

import json
import time
from abc import ABC
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from pydantic import ValidationError

from .configs import BaseLLMConfig
from .constants import (
    LOG_LLM_JSON_PARSING_FAILED,
    LOG_LLM_JSON_PARSING_SUCCESS,
    LOG_LLM_JSON_PROCESSING,
    LOG_LLM_PROMPT_MERGING,
    LOG_LLM_VALIDATION_FAILED,
    LOG_LLM_VALIDATION_PASSED,
    LOG_LLM_VALIDATING,
    MSG_JSON_SCHEMA_REQUIRED,
    MSG_UNSUPPORTED_INPUT_TYPE,
    MSG_UNSUPPORTED_OUTPUT_TYPE,
    MSG_TEXT_INPUT_MUST_BE_STRING,
    MSG_IMAGE_INPUT_MUST_BE_STRING_OR_BYTES,
    ROLE_SYSTEM,
    TOKENS_IN,
    TOKENS_OUT,
    COST_USD,
    MODEL_NAME,
    PROVIDER,
    REQUEST_ID,
    TIMESTAMP,
    DURATION_MS,
    STREAMING,
)
from core.llms.enums import InputType
from .exceptions import InputValidationError, JSONParsingError
from .interfaces import ILLM, LLMResponse, LLMStreamChunk
from .models import get_model_capabilities


class BaseLLM(ABC):
    """
    Base class for all LLM implementations.

    Provides common functionality for input validation, prompt merging,
    JSON processing, response handling, and usage tracking.
    """

    def __init__(self, config: BaseLLMConfig):
        self.config = config
        self.config.validate_config()
        self.client = None
        self.model_capabilities = get_model_capabilities(config.model_name)

    async def get_answer(self, messages: List[Dict[str, Any]], **kwargs) -> LLMResponse:
        """
        Get a complete response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with content and usage information
        """
        start_time = time.time()
        merged = self._merge_prompt(messages)
        raw = await self._get_answer_impl(merged, **kwargs)
        response = await self._process_json_if_needed(raw)

        # Track usage if available
        duration_ms = int((time.time() - start_time) * 1000)
        usage = self._track_usage(raw, duration_ms, streaming=False)
        response.usage.update(usage)

        return response

    async def get_stream(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[LLMStreamChunk]:
        """
        Get a streaming response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters

        Yields:
            LLMStreamChunk objects with content and final flag
        """
        start_time = time.time()
        merged = self._merge_prompt(messages)

        # Collect all chunks for usage tracking
        accumulated_content = ""
        async for chunk in self._get_stream_impl(merged, **kwargs):
            accumulated_content += chunk.content
            yield chunk

        # Track usage after streaming is complete
        duration_ms = int((time.time() - start_time) * 1000)
        usage = self._track_usage(accumulated_content, duration_ms, streaming=True)

        # Create final chunk with usage info if needed
        final_chunk = LLMStreamChunk(accumulated_content, is_final=True)
        final_chunk.usage = usage  # Add usage to final chunk
        yield final_chunk

    async def _process_json_if_needed(self, raw_output: str) -> LLMResponse:
        """
        Process JSON output if configured.

        Args:
            raw_output: Raw text output from LLM

        Returns:
            LLMResponse with processed content
        """
        if not self.config.json_output:
            return LLMResponse(raw_output)

        try:
            # Try to parse as JSON
            data = json.loads(raw_output)

            if self.config.json_class:
                # Use Pydantic model or custom class for validation
                if hasattr(self.config.json_class, "model_validate"):
                    # Pydantic v2
                    obj = self.config.json_class.model_validate(data)
                elif hasattr(self.config.json_class, "parse_obj"):
                    # Pydantic v1
                    obj = self.config.json_class.parse_obj(data)
                else:
                    # Custom class
                    obj = self.config.json_class(**data)
                return LLMResponse(obj)

            return LLMResponse(data)

        except (json.JSONDecodeError, ValidationError) as e:
            raise JSONParsingError(f"Invalid JSON output: {e}")

    def _merge_prompt(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge system prompt with messages if configured.

        Args:
            messages: Original message list

        Returns:
            Messages with system prompt prepended if configured
        """
        if not self.config.prompt:
            return messages

        return [{"role": ROLE_SYSTEM, "content": self.config.prompt}] + messages

    def validate_input(self, input_type: InputType, content: Any) -> bool:
        """
        Validate input for the given input type.

        Args:
            input_type: Type of input to validate
            content: Content to validate

        Returns:
            True if valid

        Raises:
            InputValidationError: If input is invalid
        """
        if input_type not in self.config.supported_input_types:
            raise InputValidationError(MSG_UNSUPPORTED_INPUT_TYPE.format(input_type=input_type))

        # Basic validation - can be extended by subclasses
        if input_type == InputType.TEXT and not isinstance(content, str):
            raise InputValidationError(MSG_TEXT_INPUT_MUST_BE_STRING)
        elif input_type == InputType.IMAGE and not isinstance(content, (str, bytes)):
            raise InputValidationError(MSG_IMAGE_INPUT_MUST_BE_STRING_OR_BYTES)

        return True

    def get_supported_capabilities(self) -> Dict[str, Any]:
        """
        Get information about supported capabilities.

        Returns:
            Dictionary with provider info, supported inputs/outputs, streaming support
        """
        capabilities = self.model_capabilities
        return {
            "provider": self.config.provider.value,
            "model_name": self.config.model_name,
            "inputs": [i.value for i in capabilities.supported_input_types],
            "outputs": [o.value for o in capabilities.supported_output_types],
            "streaming": capabilities.supports_streaming,
            "json_output": self.config.json_output,
            "temperature_range": (0, 2),
            "max_tokens_limit": capabilities.max_output_tokens,
            "max_context_length": capabilities.max_context_length,
            "supports_vision": capabilities.supports_vision,
            "supports_function_calling": capabilities.supports_function_calling,
        }

    def _track_usage(self, content: str, duration_ms: int, streaming: bool = False) -> Dict[str, Any]:
        """
        Track usage metrics for LLM requests.

        Args:
            content: Response content
            duration_ms: Request duration in milliseconds
            streaming: Whether this was a streaming request

        Returns:
            Usage dictionary with tokens, cost, and metadata
        """
        usage = {
            TOKENS_IN: 0,  # Will be calculated by subclasses if needed
            TOKENS_OUT: len(content.split()),  # Rough token estimation
            COST_USD: 0.0,  # Will be calculated by subclasses
            MODEL_NAME: self.config.model_name,
            PROVIDER: self.config.provider.value,
            DURATION_MS: duration_ms,
            STREAMING: streaming,
        }

        return usage

    async def jump_start(self) -> bool:
        """
        Test connectivity to the LLM provider.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            await self.get_answer([{"role": "user", "content": "ping"}])
            return True
        except Exception:
            return False

    async def _get_answer_impl(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Implementation-specific method for getting LLM response.

        Must be implemented by subclasses.

        Args:
            messages: Messages to send to LLM
            **kwargs: Additional parameters

        Returns:
            Raw text response from LLM
        """
        raise NotImplementedError("Subclasses must implement _get_answer_impl")

    async def _get_stream_impl(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """
        Implementation-specific method for getting streaming LLM response.

        Must be implemented by subclasses.

        Args:
            messages: Messages to send to LLM
            **kwargs: Additional parameters

        Yields:
            Raw text chunks from LLM
        """
        raise NotImplementedError("Subclasses must implement _get_stream_impl")
