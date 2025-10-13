# LLM Tool Integration Guide

This guide explains how to integrate tools from the `core/tools` specification with LLM providers to enable function calling capabilities.

## Overview

The LLM tool integration system allows you to:
- Convert tool specifications from `core/tools` format to provider-specific formats
- Register tools with LLM instances for function calling
- Automatically execute tools when LLMs request them
- Handle tool results and continue conversations

## Supported Providers

| Provider | Function Calling Support | Status |
|----------|-------------------------|---------|
| Azure OpenAI | ✅ Full support | Implemented |
| Amazon Bedrock | ✅ Full support | Pending |
| Google Gemini | ✅ Full support | Pending |

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐
│   Tool Specs        │     │   LLM Provider       │
│  (core/tools)       │────▶│  Tool Converter      │
└─────────────────────┘     └──────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────────┐
                            │ Provider-Specific    │
                            │   Tool Format        │
                            └──────────────────────┘
```

## Basic Usage

### 1. Define Tools

Tools are defined using the `core/tools` specification format:

```python
from core.tools.spec.tool_types import FunctionToolSpec
from core.tools.spec.tool_parameters import StringParameter, NumericParameter

weather_tool = FunctionToolSpec(
    id="weather_tool_v1",
    tool_name="get_weather",
    description="Get current weather information for a city",
    parameters=[
        StringParameter(
            name="city",
            description="The city to get weather for",
            required=True
        )
    ]
)
```

### 2. Create Tool Handlers

Implement the actual functionality for each tool:

```python
async def get_weather(city: str) -> dict:
    # Your implementation here
    return {"city": city, "temperature": 22, "condition": "sunny"}
```

### 3. Register Tools with LLM

```python
from core.llms import LLMFactory, AzureOpenAIConfig

# Create LLM instance
config = AzureOpenAIConfig(
    api_key="your-key",
    model_name="gpt-4o",
    deployment_name="deployment",
    endpoint="https://endpoint.openai.azure.com/"
)
llm = LLMFactory.create_llm(config)

# Register tools
tools = [weather_tool]
handlers = {"get_weather": get_weather}
llm.register_tools(tools, handlers)
```

### 4. Use the LLM

The LLM will automatically call tools when needed:

```python
messages = [{"role": "user", "content": "What's the weather in Paris?"}]
response = await llm.get_answer(messages)
print(response.content)
# Output: "The weather in Paris is currently sunny with a temperature of 22°C."
```

## Advanced Features

### Tool Choice Control

Control when and how tools are used:

```python
# Always use a specific tool
response = await llm.get_answer(messages, tool_choice={"type": "function", "function": {"name": "get_weather"}})

# Let the model decide (default)
response = await llm.get_answer(messages, tool_choice="auto")

# Never use tools
response = await llm.get_answer(messages, tool_choice="none")
```

### Multiple Tools

Register multiple tools at once:

```python
tools = [weather_tool, calculator_tool, search_tool]
handlers = {
    "get_weather": get_weather,
    "calculate": calculate,
    "search": search_database
}
llm.register_tools(tools, handlers)
```

### Error Handling

Tool errors are gracefully handled and reported back to the LLM:

```python
async def risky_tool(param: str) -> str:
    if param == "error":
        raise ValueError("Something went wrong!")
    return f"Success: {param}"

# The LLM will receive the error and can respond appropriately
```

## Tool Converter API

For custom tool conversion needs:

```python
from core.llms import ToolConverterFactory, LLMProvider

# Get a converter for a specific provider
converter = ToolConverterFactory.get_converter(LLMProvider.AZURE_OPENAI)

# Convert a single tool
azure_tool = converter.convert_tool_spec(weather_tool)

# Convert tool results
result = {"temperature": 22}
formatted_result = converter.convert_tool_result(result, "get_weather")
```

## Provider-Specific Formats

### Azure OpenAI Format

```json
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather information for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city to get weather for"
                }
            },
            "required": ["city"]
        }
    }
}
```

### Bedrock (Claude) Format

```json
{
    "name": "get_weather",
    "description": "Get current weather information for a city",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city to get weather for"
            }
        },
        "required": ["city"]
    }
}
```

### Gemini Format

```json
{
    "name": "get_weather",
    "description": "Get current weather information for a city",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city to get weather for"
            }
        },
        "required": ["city"]
    }
}
```

## Best Practices

1. **Clear Descriptions**: Write clear, concise descriptions for tools and parameters
2. **Error Handling**: Always handle potential errors in tool implementations
3. **Async Tools**: Use async functions for I/O-bound operations
4. **Type Safety**: Use proper type hints in tool handlers
5. **Testing**: Test tools independently before integrating with LLMs

## Example Implementation

See `core/llms/examples/tool_usage_example.py` for a complete working example.

## Troubleshooting

### Common Issues

1. **Model doesn't support function calling**
   - Check `model_capabilities.supports_function_calling`
   - Use a model that supports function calling (e.g., GPT-4, Claude 3)

2. **Tools not being called**
   - Ensure tool descriptions clearly explain when to use them
   - Check that tools are properly registered
   - Verify `tool_choice` parameter

3. **Tool execution errors**
   - Check handler function signatures match tool parameters
   - Ensure async handlers are properly awaited
   - Verify parameter types and validation

## Future Enhancements

- [ ] Streaming support for tool calls
- [ ] Tool call batching optimization
- [ ] Tool result caching
- [ ] Dynamic tool registration/unregistration
- [ ] Tool usage analytics and monitoring
