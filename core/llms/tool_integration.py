"""
Tool integration for LLM providers.

This module provides the base functionality to convert tool specifications from the
core/tools format to provider-specific formats for function calling.

Provider-specific converters are located in their respective connector subfolders:
- Azure OpenAI: connectors/azure/tool_converter.py
- Bedrock: connectors/bedrock/tool_converter.py
- Gemini: connectors/gemini/tool_converter.py
"""

from typing import Any, Dict, List
from abc import ABC, abstractmethod

from core.tools.spec.tool_types import ToolSpec
from core.tools.spec.tool_parameters import (
    ToolParameter,
    StringParameter,
    NumericParameter,
    IntegerParameter,
    ArrayParameter,
    ObjectParameter,
)
from core.tools.enum import ParameterType

from .enums import LLMProvider


class ToolConverter(ABC):
    """Abstract base class for converting tool specs to provider formats."""

    @abstractmethod
    def convert_tool_spec(self, tool_spec: ToolSpec) -> Dict[str, Any]:
        """
        Convert a ToolSpec to provider-specific format.

        Args:
            tool_spec: The tool specification to convert

        Returns:
            Provider-specific tool definition
        """
        pass

    @abstractmethod
    def convert_tool_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """
        Convert tool execution result to provider-specific format.

        Args:
            result: The tool execution result
            tool_name: Name of the tool that was executed

        Returns:
            Provider-specific result format
        """
        pass

    def _convert_parameter_to_json_schema(self, param: ToolParameter) -> Dict[str, Any]:
        """
        Convert a ToolParameter to JSON Schema format.

        Args:
            param: The parameter to convert

        Returns:
            JSON Schema representation
        """
        schema = {"description": param.description}

        if param.param_type == ParameterType.STRING:
            schema["type"] = "string"
            if isinstance(param, StringParameter):
                if param.enum:
                    schema["enum"] = param.enum
                if param.min_length:
                    schema["minLength"] = param.min_length
                if param.max_length:
                    schema["maxLength"] = param.max_length
                if param.pattern:
                    schema["pattern"] = param.pattern
                if param.format:
                    schema["format"] = param.format

        elif param.param_type == ParameterType.NUMBER:
            schema["type"] = "number"
            if isinstance(param, NumericParameter):
                if param.min is not None:
                    schema["minimum"] = param.min
                if param.max is not None:
                    schema["maximum"] = param.max

        elif param.param_type == ParameterType.INTEGER:
            schema["type"] = "integer"
            if isinstance(param, IntegerParameter):
                if param.min is not None:
                    schema["minimum"] = int(param.min)
                if param.max is not None:
                    schema["maximum"] = int(param.max)

        elif param.param_type == ParameterType.BOOLEAN:
            schema["type"] = "boolean"

        elif param.param_type == ParameterType.ARRAY:
            schema["type"] = "array"
            if isinstance(param, ArrayParameter):
                if param.items:
                    schema["items"] = self._convert_parameter_to_json_schema(
                        param.items
                    )
                if param.min_items is not None:
                    schema["minItems"] = param.min_items
                if param.max_items is not None:
                    schema["maxItems"] = param.max_items
                if param.unique_items:
                    schema["uniqueItems"] = param.unique_items

        elif param.param_type == ParameterType.OBJECT:
            schema["type"] = "object"
            if isinstance(param, ObjectParameter):
                if param.properties:
                    schema["properties"] = {
                        name: self._convert_parameter_to_json_schema(prop)
                        for name, prop in param.properties.items()
                    }
                    required = [
                        name for name, prop in param.properties.items() if prop.required
                    ]
                    if required:
                        schema["required"] = required

        if param.default is not None:
            schema["default"] = param.default

        return schema


class ToolConverterFactory:
    """Factory for creating provider-specific tool converters."""

    @classmethod
    def _get_converter_class(cls, provider: LLMProvider):
        """Lazy import of provider-specific converters."""
        if provider == LLMProvider.AZURE_OPENAI:
            from .connectors.azure.tool_converter import AzureOpenAIToolConverter

            return AzureOpenAIToolConverter
        elif provider == LLMProvider.BEDROCK:
            from .connectors.bedrock.tool_converter import BedrockToolConverter

            return BedrockToolConverter
        elif provider == LLMProvider.GEMINI:
            from .connectors.gemini.tool_converter import GeminiToolConverter

            return GeminiToolConverter
        else:
            raise ValueError(f"No tool converter available for provider: {provider}")

    @classmethod
    def get_converter(cls, provider: LLMProvider) -> ToolConverter:
        """
        Get the appropriate tool converter for a provider.

        Args:
            provider: The LLM provider

        Returns:
            Tool converter instance

        Raises:
            ValueError: If provider is not supported
        """
        converter_class = cls._get_converter_class(provider)
        return converter_class()


def convert_tools_for_provider(
    tools: List[ToolSpec], provider: LLMProvider
) -> List[Dict[str, Any]]:
    """
    Convert a list of tool specs to provider-specific format.

    Args:
        tools: List of tool specifications
        provider: The target LLM provider

    Returns:
        List of provider-specific tool definitions
    """
    converter = ToolConverterFactory.get_converter(provider)
    return [converter.convert_tool_spec(tool) for tool in tools]


def convert_tool_result_for_provider(
    result: Any, tool_name: str, provider: LLMProvider
) -> Dict[str, Any]:
    """
    Convert a tool execution result to provider-specific format.

    Args:
        result: The tool execution result
        tool_name: Name of the tool
        provider: The target LLM provider

    Returns:
        Provider-specific result format
    """
    converter = ToolConverterFactory.get_converter(provider)
    return converter.convert_tool_result(result, tool_name)
