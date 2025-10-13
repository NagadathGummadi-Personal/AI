"""
Google Gemini tool converter.

Converts tool specifications from core/tools format to Gemini function calling format.
"""

from typing import Any, Dict

from core.llms.tool_integration import ToolConverter


class GeminiToolConverter(ToolConverter):
    """Converter for Google Gemini function calling format."""
    
    def convert_tool_spec(self, tool_spec: Any) -> Dict[str, Any]:
        """
        Convert ToolSpec to Gemini function format.
        
        Gemini expects:
        {
            "name": "function_name",
            "description": "function description",
            "parameters": {
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
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def convert_tool_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """Convert tool result for Gemini."""
        return {
            "functionResponse": {
                "name": tool_name,
                "response": result if isinstance(result, dict) else {"result": str(result)}
            }
        }
