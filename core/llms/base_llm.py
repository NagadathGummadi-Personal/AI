"""
Base LLM implementation for the AI Agent SDK.
"""

import asyncio
import json
import time
from abc import ABC
from typing import Any, AsyncIterator, Dict, List, Optional, Callable

from pydantic import ValidationError

from .configs import BaseLLMConfig

from .constants import (
    MSG_UNSUPPORTED_INPUT_TYPE,
    MSG_TEXT_INPUT_MUST_BE_STRING,
    MSG_IMAGE_INPUT_MUST_BE_STRING_OR_BYTES,
    MSG_TOOL_NOT_FOUND,
    MSG_TOOL_EXECUTION_FAILED,
    ROLE_SYSTEM,
    TOKENS_IN,
    TOKENS_OUT,
    COST_USD,
    MODEL_NAME,
    PROVIDER,
    DURATION_MS,
    STREAMING,
    MSG_INVALID_JSON_OUTPUT,
    ROLE,
    CONTENT,
    MAX_TOKENS_LIMIT,
    MAX_CONTEXT_LENGTH,
    SUPPORTS_VISION,
    SUPPORTS_FUNCTION_CALLING,
    INPUTS,
    OUTPUTS,
    JSON_OUTPUT,
    TEMPERATURE_RANGE,
    MODEL_VALIDATE,
    PARSE_OBJ,
    PING,
    ROLE_USER,
    MSG_MODEL_DOES_NOT_SUPPORT_FUNCTION_CALLING,
    MSG_NO_HANDLER_REGISTERED_FOR_TOOL,
    EXC_ANSWER_NOT_IMPLEMENTED,
    EXC_STREAMING_NOT_IMPLEMENTED,
    PROVIDER_AZURE_OPENAI,
    PROVIDER_BEDROCK,
    PROVIDER_GEMINI,
)
from core.llms.enums import InputMediaType
from .exceptions import InputValidationError, JSONParsingError, ProviderError
from .interfaces import LLMResponse, LLMStreamChunk
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

        # Tool handling
        self._available_tools: Dict[str, Any] = {}
        self._tool_handlers: Dict[str, Callable] = {}

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

    async def get_stream(
        self, messages: List[Dict[str, Any]], **kwargs
    ) -> AsyncIterator[LLMStreamChunk]:
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
                if hasattr(self.config.json_class, MODEL_VALIDATE):
                    # Pydantic v2
                    obj = self.config.json_class.model_validate(data)
                elif hasattr(self.config.json_class, PARSE_OBJ):
                    # Pydantic v1
                    obj = self.config.json_class.parse_obj(data)
                else:
                    # Custom class
                    obj = self.config.json_class(**data)
                return LLMResponse(obj)

            return LLMResponse(data)

        except (json.JSONDecodeError, ValidationError) as e:
            raise JSONParsingError(MSG_INVALID_JSON_OUTPUT.format(e=e))

    def _replace_dynamic_variables(self, prompt: str) -> str:
        """
        Replace dynamic variables in the prompt.

        Args:
            prompt: The prompt string with potential {{variable_name}} patterns

        Returns:
            The prompt with variables replaced or unchanged if no matches found
        """
        import re

        if not self.config.dynamic_variables:
            return prompt

        def replace_variable(match):
            var_name = match.group(1)  # Extract variable name from {{variable_name}}
            return str(
                self.config.dynamic_variables.get(var_name, match.group(0))
            )  # Use original if not found

        # Pattern to match {{variable_name}} format
        pattern = r"\{\{(\w+)\}\}"
        return re.sub(pattern, replace_variable, prompt)

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

        # Replace dynamic variables in the prompt
        processed_prompt = self._replace_dynamic_variables(self.config.prompt)
        return [{ROLE: ROLE_SYSTEM, CONTENT: processed_prompt}, *messages]

    def validate_input(self, input_type: InputMediaType, content: Any) -> bool:
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
            raise InputValidationError(
                MSG_UNSUPPORTED_INPUT_TYPE.format(input_type=input_type)
            )

        # Basic validation - can be extended by subclasses
        if input_type == InputMediaType.TEXT and not isinstance(content, str):
            raise InputValidationError(MSG_TEXT_INPUT_MUST_BE_STRING)
        elif input_type == InputMediaType.IMAGE and not isinstance(
            content, (str, bytes)
        ):
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
            PROVIDER: self.config.provider.value,
            MODEL_NAME: self.config.model_name,
            INPUTS: [i.value for i in capabilities.supported_input_types],
            OUTPUTS: [o.value for o in capabilities.supported_output_types],
            STREAMING: capabilities.supports_streaming,
            JSON_OUTPUT: self.config.json_output,
            TEMPERATURE_RANGE: (
                (0, 2)
                if self.config.provider.value == PROVIDER_AZURE_OPENAI
                else (
                    (0, 1)
                    if self.config.provider.value == PROVIDER_BEDROCK
                    else (
                        (0, 2)
                        if self.config.provider.value == PROVIDER_GEMINI
                        else (0, 2)
                    )
                )
            ),
            MAX_TOKENS_LIMIT: capabilities.max_output_tokens,
            MAX_CONTEXT_LENGTH: capabilities.max_context_length,
            SUPPORTS_VISION: capabilities.supports_vision,
            SUPPORTS_FUNCTION_CALLING: capabilities.supports_function_calling,
        }

    def _track_usage(
        self, content: str, duration_ms: int, streaming: bool = False
    ) -> Dict[str, Any]:
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
            COST_USD: 0.0,  # Will be calculated by subclasses if needed
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
            await self.get_answer([{ROLE: ROLE_USER, CONTENT: PING}])
            return True
        except Exception:
            return False

    def register_tools(
        self, tools: List[Any], handlers: Optional[Dict[str, Callable]] = None
    ) -> None:
        """
        Register tools for function calling.

        Args:
            tools: List of tool specifications (ToolSpec objects)
            handlers: Optional mapping of tool names to handler functions
        """
        from .tool_integration import convert_tools_for_provider

        if not self.model_capabilities.supports_function_calling:
            raise ProviderError(
                MSG_MODEL_DOES_NOT_SUPPORT_FUNCTION_CALLING.format(
                    model_name=self.config.model_name
                )
            )

        # Convert tools to provider format
        converted_tools = convert_tools_for_provider(tools, self.config.provider)

        # Store tools and handlers
        for tool, converted in zip(tools, converted_tools):
            tool_name = tool.tool_name
            self._available_tools[tool_name] = converted

            if handlers and tool_name in handlers:
                self._tool_handlers[tool_name] = handlers[tool_name]

    def get_registered_tools(self) -> Dict[str, Any]:
        """
        Get all registered tools in provider-specific format.

        Returns:
            Dictionary of tool names to provider-specific tool definitions
        """
        return self._available_tools.copy()

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ProviderError: If tool not found or execution fails
        """
        if tool_name not in self._available_tools:
            raise ProviderError(MSG_TOOL_NOT_FOUND.format(tool_name=tool_name))

        if tool_name not in self._tool_handlers:
            raise ProviderError(
                MSG_NO_HANDLER_REGISTERED_FOR_TOOL.format(tool_name=tool_name)
            )

        try:
            handler = self._tool_handlers[tool_name]
            result = (
                await handler(**arguments)
                if asyncio.iscoroutinefunction(handler)
                else handler(**arguments)
            )
            return result
        except Exception as e:
            raise ProviderError(MSG_TOOL_EXECUTION_FAILED.format(error=str(e)))

    def format_tool_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """
        Format tool execution result for provider.

        Args:
            result: Tool execution result
            tool_name: Name of the tool

        Returns:
            Provider-specific result format
        """
        from .tool_integration import convert_tool_result_for_provider

        return convert_tool_result_for_provider(result, tool_name, self.config.provider)

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
        raise NotImplementedError(EXC_ANSWER_NOT_IMPLEMENTED)

    async def _get_stream_impl(
        self, messages: List[Dict[str, Any]], **kwargs
    ) -> AsyncIterator[str]:
        """
        Implementation-specific method for getting streaming LLM response.

        Must be implemented by subclasses.

        Args:
            messages: Messages to send to LLM
            **kwargs: Additional parameters

        Yields:
            Raw text chunks from LLM
        """
        raise NotImplementedError(EXC_STREAMING_NOT_IMPLEMENTED)
