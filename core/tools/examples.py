"""
Example Usage of Tools Specification System

This module demonstrates how to create and use tools with the specification system.
It includes examples of tool definitions, parameter schemas, and execution patterns.
"""

import asyncio
from typing import Any, Dict, Optional

# Local imports
from .enum import ToolReturnTarget, ToolReturnType, ToolType
from .interfaces.tool_interfaces import IToolExecutor
from .spec.tool_config import CircuitBreakerConfig
from .spec.tool_context import ToolContext
from .spec.tool_result import ToolError, ToolResult
from .spec.tool_types import DbToolSpec, FunctionToolSpec, HttpToolSpec, ToolSpec
from .spec.tool_parameters import (
    ToolParameter,
    StringParameter,
    NumericParameter,
    BooleanParameter,
)
from .validators import BasicValidator
from .executors.executors import FunctionToolExecutor
from .implementations import NoOpLimiter, NoOpMemory, NoOpMetrics, NoOpTracer
from .constants import (
    ERROR_MATH,
    ERROR_INVALID_OPERATION,
    METRIC_TOOL_EXECUTION_STARTED,
    METRIC_TOOL_EXECUTION_SUCCESS,
    METRIC_TOOL_EXECUTION_FAILED,
    MSG_DIVISION_BY_ZERO,
    MSG_UNKNOWN_OPERATION,
)


# Example 1: Simple calculator tool
def create_calculator_tool() -> ToolSpec:
    """Create a simple calculator tool specification"""

    parameters = [
        StringParameter(
            name="operation",
            description="Mathematical operation to perform",
            required=True,
            enum=["add", "subtract", "multiply", "divide"],
            examples=["add", "multiply"]
        ),
        NumericParameter(
            name="a",
            description="First number",
            required=True,
            examples=[10, 3.14]
        ),
        NumericParameter(
            name="b",
            description="Second number",
            required=True,
            examples=[5, 2.71]
        )
    ]

    return FunctionToolSpec(
        id="calculator-v1",
        version="1.0.0",
        tool_name="calculator",
        description="Performs basic mathematical operations",
        parameters=parameters,
        return_type=ToolReturnType.JSON,
        return_target=ToolReturnTarget.STEP,
        examples=[
            {
                "operation": "add",
                "a": 10,
                "b": 5,
                "result": 15
            }
        ],
        metrics_tags={"category": "math", "complexity": "basic"}
    )


# Example 2: Weather API tool
def create_weather_tool() -> ToolSpec:
    """Create a weather API tool specification"""

    parameters = [
        StringParameter(
            name="location",
            description="City name or coordinates",
            required=True,
            min_length=2,
            max_length=100,
            examples=["New York", "London", "Tokyo"]
        ),
        StringParameter(
            name="units",
            description="Temperature units",
            required=False,
            default="celsius",
            enum=["celsius", "fahrenheit"],
            examples=["celsius", "fahrenheit"]
        )
    ]

    return HttpToolSpec(
        id="weather-api-v1",
        version="1.0.0",
        tool_name="weather_api",
        description="Get current weather information for a location",
        parameters=parameters,
        return_type=ToolReturnType.JSON,
        return_target=ToolReturnTarget.STEP,
        timeout_s=10,
        permissions=["weather:read"],
        url="https://api.weather.com/v1/current",
        method="GET",
        query_params={"format": "json"},
        examples=[
            {
                "location": "New York",
                "units": "celsius",
                "temperature": 22,
                "condition": "sunny"
            }
        ],
        metrics_tags={"category": "api", "service": "weather"}
    )


# Example 3: Database query tool
def create_db_query_tool() -> ToolSpec:
    """Create a database query tool specification"""

    parameters = [
        StringParameter(
            name="query",
            description="SQL query to execute",
            required=True,
            min_length=10,
            max_length=1000,
            pattern=r"^\s*SELECT.*",
            examples=["SELECT * FROM users WHERE active = true"]
        ),
        NumericParameter(
            name="max_rows",
            description="Maximum number of rows to return",
            required=False,
            default=100,
            min=1,
            max=1000
        )
    ]

    return DbToolSpec(
        id="db-query-v1",
        version="1.0.0",
        tool_name="database_query",
        description="Execute read-only SQL queries against the database",
        parameters=parameters,
        return_type=ToolReturnType.JSON,
        return_target=ToolReturnTarget.STEP,
        timeout_s=30,
        permissions=["db:read"],
        host="localhost",
        port=5432,
        database="myapp",
        username="readonly_user",
        driver="postgresql",
        circuit_breaker=CircuitBreakerConfig(
            enabled=True,
            failure_threshold=3,
            recovery_timeout_s=60
        ),
        examples=[
            {
                "query": "SELECT COUNT(*) as user_count FROM users",
                "max_rows": 10,
                "result": [{"user_count": 1250}]
            }
        ],
        metrics_tags={"category": "database", "operation": "read"}
    )


# Example 4: Tool implementation
class CalculatorImpl:
    """Implementation of the calculator tool"""

    async def calculate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the calculation - context handled by executor"""
        import asyncio
        operation = args["operation"]
        a = args["a"]
        b = args["b"]

        # Add realistic delay to simulate processing time
        await asyncio.sleep(0.1)  # 100ms delay

        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ToolError(MSG_DIVISION_BY_ZERO, retryable=False, code=ERROR_MATH)
            result = a / b
        else:
            raise ToolError(MSG_UNKNOWN_OPERATION.format(operation=operation), retryable=False, code=ERROR_INVALID_OPERATION)

        return {
            "operation": operation,
            "operands": [a, b],
            "result": result
        }


# Example 5: Tool registry and execution
class ToolRegistry:
    """Simple registry for managing tools"""

    def __init__(self):
        self.tools: Dict[str, ToolSpec] = {}
        self.executors: Dict[str, IToolExecutor] = {}
        self.validator = BasicValidator()

    def register_tool(self, spec: ToolSpec, executor: IToolExecutor):
        """Register a tool with its executor"""
        self.tools[spec.id] = spec
        self.executors[spec.id] = executor

    async def execute_tool(self, tool_id: str, args: Dict[str, Any], ctx: Optional[ToolContext] = None) -> ToolResult:
        """Execute a tool by ID"""
        if tool_id not in self.tools:
            raise ToolError(f"Tool not found: {tool_id}", retryable=False, code="TOOL_NOT_FOUND")

        spec = self.tools[tool_id]
        executor = self.executors[tool_id]

        # Create context if not provided
        if ctx is None:
            ctx = ToolContext()

        # Inject dependencies
        ctx.memory = ctx.memory or NoOpMemory()
        ctx.metrics = ctx.metrics or NoOpMetrics()
        ctx.tracer = ctx.tracer or NoOpTracer()
        ctx.limiter = ctx.limiter or NoOpLimiter()

        # Validate arguments
        await self.validator.validate(args, spec)

        # Execute with tracing
        async with ctx.tracer.span(f"tool.{spec.tool_name}", {"tool_id": tool_id}) as span_id:
            ctx.span_id = span_id

            # Record metrics
            if ctx.metrics:
                await ctx.metrics.incr("tool.execution.started", tags={"tool_id": tool_id})

            try:
                result = await executor.execute(args, ctx)

                # Record success metrics
                if ctx.metrics:
                    await ctx.metrics.incr("tool.execution.success", tags={"tool_id": tool_id})
                    if result.usage:
                        await ctx.metrics.timing_ms("tool.execution.duration", result.usage.get("latency_ms", 0))

                return result

            except Exception as e:
                # Record failure metrics
                if ctx.metrics:
                    await ctx.metrics.incr("tool.execution.failed", tags={"tool_id": tool_id})

                raise ToolError(f"Tool execution failed: {str(e)}", retryable=True)


# Example usage
async def example_usage():
    """Demonstrate how to use the tools system"""

    # Create tool registry
    registry = ToolRegistry()

    # Create calculator tool
    calc_spec = create_calculator_tool()
    calc_impl = CalculatorImpl()
    calc_executor = FunctionToolExecutor(calc_spec, calc_impl.calculate)

    registry.register_tool(calc_spec, calc_executor)

    # Create context
    ctx = ToolContext(
        user_id="user123",
        session_id="session456",
        metrics_tags={"user": "user123"}
    )

    # Execute tool
    try:
        result = await registry.execute_tool("calculator-v1", {
            "operation": "add",
            "a": 10,
            "b": 5
        }, ctx)

        print(f"Result: {result.content}")
        print(f"Usage: {result.usage}")

    except ToolError as e:
        print(f"Tool error: {e.message} (code: {e.code})")


if __name__ == "__main__":
    asyncio.run(example_usage())
