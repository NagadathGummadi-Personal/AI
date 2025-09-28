#!/usr/bin/env python3
"""
Simple Calculator Tool with Proper Logging and Metrics

This demonstrates using the existing tools system with comprehensive logging and metrics.
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any, Optional

# Add the core/tools directory to the path so we can import the tools system
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core', 'tools'))

from core.tools.tool_types import (
    ToolSpec,
    FunctionToolSpec,
    ToolParameter,
    StringParameter,
    NumericParameter,
    BooleanParameter,
    ToolType,
    ToolReturnType,
    ToolReturnTarget,
    ToolContext,
    ToolError,
    ToolResult,
    IToolMetrics
)
from core.tools.validators import BasicValidator
from core.tools.executors import FunctionToolExecutor
from core.tools.implementations import NoOpMemory, NoOpMetrics, NoOpTracer, NoOpLimiter, BasicSecurity
from core.tools.validators import BasicValidator


class LoggingMetricsCollector(IToolMetrics):
    """Simple metrics collector for demonstration"""

    def __init__(self):
        self.metrics = {
            "execution_times": [],
            "operation_counts": {},
            "error_counts": {},
            "total_executions": 0
        }

    async def timing_ms(self, name: str, value_ms: int, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing metric"""
        self.metrics["execution_times"].append(value_ms)
        print(f"[METRICS] {name}: {value_ms}ms")

    async def incr(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter metric"""
        if name not in self.metrics["operation_counts"]:
            self.metrics["operation_counts"][name] = 0
        self.metrics["operation_counts"][name] += value

        tag_str = f" ({tags})" if tags else ""
        print(f"[METRICS] {name}: +{value}{tag_str}")

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_executions": self.metrics["total_executions"],
            "avg_execution_time_ms": sum(self.metrics["execution_times"]) / len(self.metrics["execution_times"]) if self.metrics["execution_times"] else 0,
            "operation_counts": self.metrics["operation_counts"],
            "error_counts": self.metrics["error_counts"]
        }


class CalculatorTool:
    """Simple calculator tool implementation that demonstrates proper logging and metrics
    using the existing tools system infrastructure."""

    async def calculate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform calculation - context is handled by the executor"""
        # Extract parameters
        operation = args.get("operation", "add")
        a = args.get("a")
        b = args.get("b")

        # Validate parameters
        if a is None or b is None:
            raise ToolError("Missing required parameters: 'a' and 'b' are required", retryable=False, code="MISSING_PARAMS")

        # Type coercion
        try:
            a_float = float(a)
            b_float = float(b)
        except (ValueError, TypeError) as e:
            raise ToolError(f"Invalid number format: {e}", retryable=False, code="INVALID_NUMBER")

        # Add realistic delay to simulate processing time
        await asyncio.sleep(0.1)  # 100ms delay

        # Simulate error if requested
        if args.get("simulate_error"):
            error_msg = "Simulated error for testing"
            raise ToolError(error_msg, retryable=True, code="SIMULATED_ERROR")

        # Perform calculation
        if operation == "add":
            result = a_float + b_float
        elif operation == "subtract":
            result = a_float - b_float
        elif operation == "multiply":
            result = a_float * b_float
        elif operation == "divide":
            if b_float == 0:
                raise ToolError("Division by zero", retryable=False, code="MATH_ERROR")
            result = a_float / b_float
        else:
            raise ToolError(f"Unknown operation: {operation}", retryable=False, code="INVALID_OPERATION")

        return {
            "result": result,
            "operation": operation,
            "operands": [a_float, b_float],
            "success": True
        }



async def run_calculator_demo():
    """Run comprehensive tests for the calculator tool using the proper tools system"""
    print("🚀 Running Calculator Tool Demo with Proper Logging and Metrics")
    print("=" * 70)

    # Create tool specification
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
            description="First number (supports coercion from string)",
            required=True,
            examples=[10, 3.14, "5.5"]
        ),
        NumericParameter(
            name="b",
            description="Second number (supports coercion from string)",
            required=True,
            examples=[5, 2.71, "2.5"]
        ),
        BooleanParameter(
            name="simulate_error",
            description="Whether to simulate an error for testing error logging",
            required=False,
            default=False,
            examples=[False, True]
        )
    ]

    tool_spec = FunctionToolSpec(
        id="calculator-v1",
        version="1.0.0",
        tool_name="calculator",
        description="Performs basic mathematical operations with comprehensive logging and metrics",
        parameters=parameters,
        return_type=ToolReturnType.JSON,
        return_target=ToolReturnTarget.STEP,
        timeout_s=30,
        metrics_tags={"category": "math", "complexity": "basic"}
    )

    print(f"📋 Tool Specification: {tool_spec.tool_name} v{tool_spec.version}")
    print(f"📝 Description: {tool_spec.description}")
    print(f"🔧 Tool Type: {tool_spec.tool_type}")
    print(f"📊 Parameters: {len(tool_spec.parameters)}")
    for param in tool_spec.parameters:
        print(f"  • {param.name} ({param.param_type.value}): {param.description}")
    print()

    # Test Results
    tests_passed = 0
    total_tests = 0

    def test_passed(description: str):
        nonlocal tests_passed, total_tests
        total_tests += 1
        tests_passed += 1
        print(f"✅ PASS: {description}")

    def test_failed(description: str, error: str):
        nonlocal tests_passed, total_tests
        total_tests += 1
        print(f"❌ FAIL: {description} - {error}")

    # Create tool implementation and metrics collector
    calculator = CalculatorTool()
    metrics_collector = LoggingMetricsCollector()

    # Create tool executor
    executor = FunctionToolExecutor(tool_spec, calculator.calculate)

    # Create execution context with metrics
    context = ToolContext(
        user_id="demo_user_123",
        session_id="demo_session_456",
        trace_id="demo_trace_789",
        tenant_id="demo_tenant",
        locale="en-US",
        timezone="UTC",
        auth={"user_role": "demo", "permissions": ["math:execute"]},
        extras={"environment": "demo", "version": "1.0.0"},
        metrics=metrics_collector  # Use our custom metrics collector
    )

    print(f"👤 Execution Context: User={context.user_id}, Session={context.session_id}")
    print()

    # Test 1: Basic Addition
    print("🧪 Test 1: Basic Addition")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "add", "a": 10, "b": 5}, context)
        print(f'result: {result}')
        if result.content["result"] == 15.0:
            test_passed("Basic addition should return 15.0")
        else:
            test_failed("Basic addition", f"Expected 15.0, got {result.content['result']}")

        print(f"✅ Result: {result.content['result']}")
        print(f"⏱️  Execution Time: {result.content['execution_time_ms']}ms")

    except Exception as e:
        test_failed("Basic addition", str(e))

    print()

    # Test 2: Subtraction
    print("🧪 Test 2: Subtraction")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "subtract", "a": 10, "b": 3}, context)
        if result.content["result"] == 7.0:
            test_passed("Subtraction should return 7.0")
        else:
            test_failed("Subtraction", f"Expected 7.0, got {result.content['result']}")

        print(f"✅ Result: {result.content['result']}")

    except Exception as e:
        test_failed("Subtraction", str(e))

    print()

    # Test 3: Multiplication
    print("🧪 Test 3: Multiplication")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "multiply", "a": 6, "b": 7}, context)
        if result.content["result"] == 42.0:
            test_passed("Multiplication should return 42.0")
        else:
            test_failed("Multiplication", f"Expected 42.0, got {result.content['result']}")

        print(f"✅ Result: {result.content['result']}")

    except Exception as e:
        test_failed("Multiplication", str(e))

    print()

    # Test 4: Division
    print("🧪 Test 4: Division")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "divide", "a": 15, "b": 3}, context)
        if result.content["result"] == 5.0:
            test_passed("Division should return 5.0")
        else:
            test_failed("Division", f"Expected 5.0, got {result.content['result']}")

        print(f"✅ Result: {result.content['result']}")

    except Exception as e:
        test_failed("Division", str(e))

    print()

    # Test 5: String Coercion
    print("🧪 Test 5: String Coercion")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "add", "a": "10", "b": "5"}, context)
        if result.content["result"] == 15.0:
            test_passed("String coercion should work correctly")
        else:
            test_failed("String coercion", f"Expected 15.0, got {result.content['result']}")

        print(f"✅ Result: {result.content['result']}")

    except Exception as e:
        test_failed("String coercion", str(e))

    print()

    # Test 6: Error Simulation
    print("🧪 Test 6: Error Simulation")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "add", "a": 10, "b": 5, "simulate_error": True}, context)
        if "error" in result.content and "Simulated error" in result.content["error"]:
            test_passed("Error simulation should return error result")
        else:
            test_failed("Error simulation", f"Expected error result, got {result.content}")

        print(f"✅ Error correctly simulated in result: {result.content.get('error', 'N/A')}")

    except Exception as e:
        test_failed("Error simulation", f"Unexpected exception: {e}")

    print()

    # Test 7: Division by Zero Error
    print("🧪 Test 7: Division by Zero Error")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "divide", "a": 10, "b": 0}, context)
        if "error" in result.content and "Division by zero" in result.content["error"]:
            test_passed("Division by zero should return error result")
        else:
            test_failed("Division by zero", f"Expected error result, got {result.content}")

        print(f"✅ Division by zero correctly handled in result: {result.content.get('error', 'N/A')}")

    except Exception as e:
        test_failed("Division by zero", f"Unexpected exception: {e}")

    print()

    # Test 8: Invalid Operation
    print("🧪 Test 8: Invalid Operation")
    print("-" * 40)

    try:
        result = await executor.execute({"operation": "invalid", "a": 10, "b": 5}, context)
        if "error" in result.content and "Unknown operation" in result.content["error"]:
            test_passed("Invalid operation should return error result")
        else:
            test_failed("Invalid operation", f"Expected error result, got {result.content}")

        print(f"✅ Invalid operation correctly rejected in result: {result.content.get('error', 'N/A')}")

    except Exception as e:
        test_failed("Invalid operation", f"Unexpected exception: {e}")

    print()

    # Test 9: Successful Authorization
    print("🧪 Test 9: Successful Authorization")
    print("-" * 40)

    # Create context with proper authorization
    authorized_context = ToolContext(
        user_id="authorized_user",
        session_id="session_123",
        trace_id="trace_456",
        tenant_id="test_tenant",
        locale="en-US",
        timezone="UTC",
        auth={"user_role": "admin", "permissions": ["math:execute", "math:admin"]},
        extras={"environment": "test", "version": "1.0.0"},
        metrics=metrics_collector,
        validator=BasicValidator(),
        security=BasicSecurity(authorized_users=["authorized_user"], authorized_roles=["admin"])
    )

    try:
        result = await executor.execute({"operation": "add", "a": 5, "b": 3}, authorized_context)
        if result.content["result"] == 8.0:
            test_passed("Authorized user should be able to execute tool")
        else:
            test_failed("Authorized user execution", f"Expected 8.0, got {result.content['result']}")

        print(f"✅ Authorized execution successful: {result.content['result']}")

    except Exception as e:
        test_failed("Authorized user execution", f"Unexpected exception: {e}")

    print()

    # Test 10: Failed Authorization - Wrong User
    print("🧪 Test 10: Failed Authorization - Wrong User")
    print("-" * 40)

    unauthorized_context = ToolContext(
        user_id="unauthorized_user",
        session_id="session_123",
        trace_id="trace_456",
        tenant_id="test_tenant",
        locale="en-US",
        timezone="UTC",
        auth={"user_role": "user", "permissions": ["math:execute"]},
        extras={"environment": "test", "version": "1.0.0"},
        metrics=metrics_collector,
        validator=BasicValidator(),
        security=BasicSecurity(authorized_users=["authorized_user"], authorized_roles=["admin"])
    )

    try:
        result = await executor.execute({"operation": "add", "a": 5, "b": 3}, unauthorized_context)
        if "error" in result.content and "not authorized" in result.content["error"]:
            test_passed("Unauthorized user should return error result")
            print(f"✅ Unauthorized user correctly rejected in result: {result.content['error']}")
        else:
            test_failed("Unauthorized user", f"Expected error result, got {result.content}")

    except Exception as e:
        test_failed("Unauthorized user", f"Unexpected exception: {e}")

    print()

    # Test 11: Failed Authorization - Insufficient Permissions
    print("🧪 Test 11: Failed Authorization - Insufficient Permissions")
    print("-" * 40)

    insufficient_perms_context = ToolContext(
        user_id="user_with_wrong_perms",
        session_id="session_123",
        trace_id="trace_456",
        tenant_id="test_tenant",
        locale="en-US",
        timezone="UTC",
        auth={"user_role": "user", "permissions": ["read:only"]},  # Missing math:execute
        extras={"environment": "test", "version": "1.0.0"},
        metrics=metrics_collector,
        validator=BasicValidator(),
        security=BasicSecurity()
    )

    try:
        result = await executor.execute({"operation": "add", "a": 5, "b": 3}, insufficient_perms_context)
        if "error" in result.content and "missing required permissions" in result.content["error"]:
            test_passed("User with insufficient permissions should return error result")
            print(f"✅ Insufficient permissions correctly rejected in result: {result.content['error']}")
        else:
            test_failed("Insufficient permissions", f"Expected error result, got {result.content}")

    except Exception as e:
        test_failed("Insufficient permissions", f"Unexpected exception: {e}")

    print()

    # Print execution summary
    print("📈 Execution Summary")
    print("=" * 40)
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: ✅ {tests_passed}")
    print(f"Tests Failed: ❌ {total_tests - tests_passed}")

    # Show metrics summary
    metrics_summary = metrics_collector.get_summary()
    print(f"\n📊 Metrics Summary:")
    print(f"  Total Executions: {metrics_summary['total_executions']}")
    print(f"  Avg Execution Time: {metrics_summary['avg_execution_time_ms']:.2f}ms")
    print(f"  Operation Counts: {metrics_summary['operation_counts']}")
    print(f"  Error Counts: {metrics_summary['error_counts']}")

    print(f"\n🎉 Demo completed! The tool properly logged all operations and metrics.")
    # Return success status
    return total_tests - tests_passed == 0


async def main():
    """Main function to run the demo"""
    try:
        success = await run_calculator_demo()
        if success:
            print("\n🎉 All tests passed! The tools system is working correctly with proper logging and metrics.")
            return 0
        else:
            print("\n💥 Some tests failed. Please check the output above.")
            return 1
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
        return 0
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run the async demo
    exit_code = asyncio.run(main())
    exit(exit_code)
