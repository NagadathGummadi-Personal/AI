"""
Example of using tool integration with LLMs.

This example demonstrates how to:
1. Define tools using the core/tools specification format
2. Register tools with an LLM
3. Execute tool calls automatically
"""

import asyncio
from typing import Dict, Any

# Import LLM components
from core.llms import (
    AzureOpenAIConfig,
    LLMFactory,
    LLMProvider,
)

# Import tool specification components
from core.tools.spec.tool_types import FunctionToolSpec
from core.tools.spec.tool_parameters import (
    StringParameter,
    NumericParameter,
    ObjectParameter,
)
from core.tools.enum import ParameterType, ToolReturnType


# Example tool handlers
async def get_weather(city: str, unit: str = "celsius") -> Dict[str, Any]:
    """Simulated weather API call."""
    # In a real scenario, this would call an actual weather API
    weather_data = {
        "city": city,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "sunny",
        "humidity": 65,
        "wind_speed": 15
    }
    return weather_data


async def calculate(operation: str, a: float, b: float) -> float:
    """Simple calculator function."""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float('inf')
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](a, b)


def search_database(query: str, table: str = "products") -> Dict[str, Any]:
    """Simulated database search."""
    # Simulate database results
    results = {
        "query": query,
        "table": table,
        "count": 3,
        "results": [
            {"id": 1, "name": "Product A", "price": 29.99},
            {"id": 2, "name": "Product B", "price": 39.99},
            {"id": 3, "name": "Product C", "price": 49.99},
        ]
    }
    return results


async def main():
    """Main example demonstrating tool usage with LLMs."""
    
    # Step 1: Define tools using the core/tools specification format
    weather_tool = FunctionToolSpec(
        id="weather_tool_v1",
        tool_name="get_weather",
        description="Get current weather information for a city",
        parameters=[
            StringParameter(
                name="city",
                description="The city to get weather for",
                required=True,
                examples=["New York", "London", "Tokyo"]
            ),
            StringParameter(
                name="unit",
                description="Temperature unit",
                required=False,
                default="celsius",
                enum=["celsius", "fahrenheit"]
            )
        ],
        return_type=ToolReturnType.DICT
    )
    
    calculator_tool = FunctionToolSpec(
        id="calculator_tool_v1",
        tool_name="calculate",
        description="Perform basic mathematical operations",
        parameters=[
            StringParameter(
                name="operation",
                description="The operation to perform",
                required=True,
                enum=["add", "subtract", "multiply", "divide"]
            ),
            NumericParameter(
                name="a",
                description="First number",
                required=True
            ),
            NumericParameter(
                name="b",
                description="Second number",
                required=True
            )
        ],
        return_type=ToolReturnType.NUMBER
    )
    
    search_tool = FunctionToolSpec(
        id="search_tool_v1",
        tool_name="search_database",
        description="Search for items in the database",
        parameters=[
            StringParameter(
                name="query",
                description="Search query",
                required=True,
                min_length=1,
                max_length=100
            ),
            StringParameter(
                name="table",
                description="Database table to search",
                required=False,
                default="products",
                enum=["products", "users", "orders"]
            )
        ],
        return_type=ToolReturnType.DICT
    )
    
    # Step 2: Create LLM configuration and instance
    config = AzureOpenAIConfig(
        api_key="your-api-key-here",  # Replace with actual API key
        model_name="gpt-4o",
        deployment_name="gpt-4o-deployment",
        endpoint="https://your-endpoint.openai.azure.com/",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create LLM instance
    llm = LLMFactory.create_llm(config)
    
    # Step 3: Register tools with their handlers
    tools = [weather_tool, calculator_tool, search_tool]
    handlers = {
        "get_weather": get_weather,
        "calculate": calculate,
        "search_database": search_database
    }
    
    llm.register_tools(tools, handlers)
    
    # Step 4: Test various prompts that should trigger tool usage
    
    # Example 1: Weather query
    print("=" * 50)
    print("Example 1: Weather Query")
    print("=" * 50)
    
    messages = [
        {"role": "user", "content": "What's the weather like in Paris right now?"}
    ]
    
    try:
        response = await llm.get_answer(messages)
        print(f"Assistant: {response.content}")
        print(f"Usage: {response.usage}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Calculation
    print("\n" + "=" * 50)
    print("Example 2: Calculation")
    print("=" * 50)
    
    messages = [
        {"role": "user", "content": "Can you calculate 147 multiplied by 23 for me?"}
    ]
    
    try:
        response = await llm.get_answer(messages)
        print(f"Assistant: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Database search
    print("\n" + "=" * 50)
    print("Example 3: Database Search")
    print("=" * 50)
    
    messages = [
        {"role": "user", "content": "Search for products with 'laptop' in the name"}
    ]
    
    try:
        response = await llm.get_answer(messages)
        print(f"Assistant: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Multiple tool calls in one request
    print("\n" + "=" * 50)
    print("Example 4: Multiple Tool Calls")
    print("=" * 50)
    
    messages = [
        {
            "role": "user", 
            "content": "What's the weather in Tokyo and New York? Also, what's 50 fahrenheit in celsius? (hint: C = (F - 32) × 5/9)"
        }
    ]
    
    try:
        response = await llm.get_answer(messages)
        print(f"Assistant: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Tool choice control
    print("\n" + "=" * 50)
    print("Example 5: Tool Choice Control")
    print("=" * 50)
    
    messages = [
        {"role": "user", "content": "Tell me about the weather (but don't actually check it)"}
    ]
    
    try:
        # Use tool_choice="none" to prevent tool calls
        response = await llm.get_answer(messages, tool_choice="none")
        print(f"Assistant: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Step 5: Demonstrate error handling
    print("\n" + "=" * 50)
    print("Example 6: Error Handling")
    print("=" * 50)
    
    messages = [
        {"role": "user", "content": "Divide 100 by 0"}
    ]
    
    try:
        response = await llm.get_answer(messages)
        print(f"Assistant: {response.content}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
