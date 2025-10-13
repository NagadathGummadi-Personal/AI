"""
Amazon Bedrock tool converter.

Converts tool specifications from core/tools format to Bedrock function calling format.
"""

from typing import Any, Dict

from core.llms.tool_integration import ToolConverter


class BedrockToolConverter(ToolConverter):
    """Converter for Amazon Bedrock function calling format."""
    
    def convert_tool_spec(self, tool_spec: Any) -> Dict[str, Any]:
        """
        Convert ToolSpec to Bedrock tool format.
        
        Bedrock (Claude) expects:
        {
            "name": "function_name",
            "description": "function description",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        properties = {}
        required = []
        
        for param in tool_spec.parameters:
            properties[param.name] = self._convert_parameter_to_json_schema(param)
            if param.required:
                required.append(param.name)
        
        return {
            "name": tool_spec.tool_name,
            "description": tool_spec.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def convert_tool_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """Convert tool result for Bedrock."""
        return {
            "type": "tool_result",
            "tool_use_id": tool_name,  # This would need to be tracked from the request
            "content": str(result) if not isinstance(result, str) else result
        }
