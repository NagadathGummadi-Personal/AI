#!/usr/bin/env python3
"""
Demo: Logging Addition Tool

This script demonstrates the "log everything" addition tool that provides
comprehensive logging of all operations, parameters, context, and results.
"""

import asyncio
import json
import time
from typing import Dict, Any
from datetime import datetime

# Import the tools system
from core.tools import (
    ToolSpec,
    ToolParameter,
    ToolType,
    ToolReturnType,
    ToolReturnTarget,
    ToolContext,
    FunctionToolExecutor,
    BasicValidator
)

from core.tools.tool_types import RetryConfig, CircuitBreakerConfig, IdempotencyConfig


class ComprehensiveLoggingAdditionTool:
    """
    Addition tool that logs EVERYTHING that happens during execution.

    This tool demonstrates comprehensive observability by logging:
    - Input parameters and validation
    - Execution context and metadata
    - Step-by-step operation progress
    - Performance metrics and timing
    - Error conditions and handling
    - Memory and caching operations
    - Tracing and span information
    """

    def __init__(self):
        self.execution_history = []
        self.operation_count = 0
        self.error_count = 0

    def log_event(self, event_type: str, details: Dict[str, Any], level: str = "INFO"):
        """Log an event with timestamp and context"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "level": level,
            "details": details
        }
        self.execution_history.append(event)
        print(f"[{level}] {event_type}: {json.dumps(details, indent=2)}")

    async def add_numbers(self, args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
        """Add numbers with comprehensive logging"""
        self.operation_count += 1
        operation_id = f"op_{self.operation_count}_{int(time.time())}"
        start_time = time.time()

        # Log execution start
        self.log_event("EXECUTION_STARTED", {
            "operation_id": operation_id,
            "tool_name": "comprehensive_addition",
            "input_args": args,
            "context": {
                "user_id": ctx.user_id,
                "session_id": ctx.session_id,
                "trace_id": ctx.trace_id,
                "tenant_id": ctx.tenant_id,
                "locale": ctx.locale,
                "timezone": ctx.timezone
            },
            "memory_available": ctx.memory is not None,
            "metrics_available": ctx.metrics is not None,
            "tracer_available": ctx.tracer is not None
        })

        try:
            # Parameter extraction and validation logging
            a = args.get("a")
            b = args.get("b")

            self.log_event("PARAMETER_EXTRACTION", {
                "operation_id": operation_id,
                "raw_a": args.get("a"),
                "raw_b": args.get("b"),
                "a_type": type(a).__name__ if a is not None else "None",
                "b_type": type(b).__name__ if b is not None else "None"
            })

            # Validation with detailed logging
            if a is None or b is None:
                raise ValueError("Missing required parameters: 'a' and 'b' are required")

            # Type coercion logging
            try:
                a_float = float(a)
                b_float = float(b)

                self.log_event("TYPE_COERCION", {
                    "operation_id": operation_id,
                    "original_a": a,
                    "original_b": b,
                    "coerced_a": a_float,
                    "coerced_b": b_float,
                    "coercion_successful": True
                })
            except (ValueError, TypeError) as e:
                self.log_event("TYPE_COERCION_FAILED", {
                    "operation_id": operation_id,
                    "error": str(e),
                    "a_value": a,
                    "b_value": b
                }, level="ERROR")
                raise ValueError(f"Invalid number format: {e}")

            # Simulate error if requested
            if args.get("simulate_error"):
                error_msg = "Simulated error for testing comprehensive logging"
                self.log_event("SIMULATED_ERROR", {
                    "operation_id": operation_id,
                    "error_message": error_msg,
                    "requested_by_user": True
                }, level="WARNING")
                raise ValueError(error_msg)

            # Perform calculation with step-by-step logging
            self.log_event("CALCULATION_STARTED", {
                "operation_id": operation_id,
                "operand_a": a_float,
                "operand_b": b_float
            })

            # Simulate some processing time for demonstration
            await asyncio.sleep(0.01)

            result = a_float + b_float

            calculation_time = time.time() - start_time

            self.log_event("CALCULATION_COMPLETED", {
                "operation_id": operation_id,
                "result": result,
                "calculation_time_ms": round(calculation_time * 1000, 2),
                "performance_metrics": {
                    "input_size_bytes": len(json.dumps(args).encode()),
                    "output_size_bytes": len(json.dumps({"result": result}).encode()),
                    "memory_usage_estimate": "low"
                }
            })

            # Metrics logging
            if ctx.metrics:
                await ctx.metrics.incr("addition.success", tags={"operation": "add"})
                await ctx.metrics.timing_ms("addition.duration", int(calculation_time * 1000))

                self.log_event("METRICS_RECORDED", {
                    "operation_id": operation_id,
                    "metrics_calls": ["addition.success", "addition.duration"]
                })

            # Tracing logging
            if ctx.tracer:
                async with ctx.tracer.span("addition_calculation", {
                    "operation_id": operation_id,
                    "operands": [a_float, b_float]
                }) as span_id:
                    self.log_event("TRACING_SPAN_CREATED", {
                        "operation_id": operation_id,
                        "span_id": span_id,
                        "span_attributes": {"operation_id": operation_id, "operands": [a_float, b_float]}
                    })

            # Memory/caching logging
            if ctx.memory:
                cache_key = f"addition_result_{hash((a_float, b_float))}"
                await ctx.memory.set(cache_key, result, ttl_s=300)
                self.log_event("CACHE_OPERATION", {
                    "operation_id": operation_id,
                    "cache_key": cache_key,
                    "cached_value": result,
                    "ttl_seconds": 300
                })

            # Final result logging
            execution_time = time.time() - start_time
            result_data = {
                "result": result,
                "operation": "addition",
                "operands": [a_float, b_float],
                "operation_id": operation_id,
                "total_execution_time_ms": round(execution_time * 1000, 2),
                "success": True
            }

            self.log_event("EXECUTION_COMPLETED", {
                "operation_id": operation_id,
                "result_summary": {
                    "result": result,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "success": True
                }
            })

            return result_data

        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time

            # Comprehensive error logging
            self.log_event("EXECUTION_ERROR", {
                "operation_id": operation_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time_before_error_ms": round(execution_time * 1000, 2),
                "partial_results": {
                    "a_processed": a is not None,
                    "b_processed": b is not None
                }
            }, level="ERROR")

            # Record error metrics
            if ctx.metrics:
                await ctx.metrics.incr("addition.error", tags={"error_type": type(e).__name__})

            raise


def create_logging_addition_tool_spec() -> ToolSpec:
    """Create the comprehensive logging addition tool specification"""
    parameters = [
        ToolParameter(
            name="a",
            type="number",
            description="First number to add (supports coercion from string)",
            required=True,
            examples=[10, 3.14, "5.5"]
        ),
        ToolParameter(
            name="b",
            type="number",
            description="Second number to add (supports coercion from string)",
            required=True,
            examples=[5, 2.71, "2.5"]
        ),
        ToolParameter(
            name="simulate_error",
            type="boolean",
            description="Whether to simulate an error for testing error logging",
            required=False,
            default=False,
            examples=[False, True]
        )
    ]

    return ToolSpec(
        id="comprehensive-logging-addition-v1",
        version="1.0.0",
        tool_name="comprehensive_addition",
        description="Adds two numbers with comprehensive logging of all operations, parameters, context, metrics, and errors",
        tool_type=ToolType.FUNCTION,
        parameters=parameters,
        return_type=ToolReturnType.JSON,
        return_target=ToolReturnTarget.STEP,
        timeout_s=30,
        retry=RetryConfig(
            max_attempts=3,
            base_delay_s=0.5,
            max_delay_s=5.0
        ),
        circuit_breaker=CircuitBreakerConfig(
            enabled=True,
            failure_threshold=5,
            recovery_timeout_s=60
        ),
        idempotency=IdempotencyConfig(
            enabled=True,
            key_fields=["a", "b"],
            ttl_s=3600
        ),
        metrics_tags={
            "category": "mathematics",
            "operation": "addition",
            "logging_level": "comprehensive",
            "version": "1.0.0"
        }
    )


async def demonstrate_logging_addition_tool():
    """Demonstrate the comprehensive logging addition tool"""
    print("🚀 Starting Comprehensive Logging Addition Tool Demo")
    print("=" * 60)

    # Create tool specification
    tool_spec = create_logging_addition_tool_spec()
    print(f"📋 Tool Specification: {tool_spec.tool_name} v{tool_spec.version}")

    # Create tool implementation
    logging_tool = ComprehensiveLoggingAdditionTool()

    # Create tool executor
    executor = FunctionToolExecutor(tool_spec, logging_tool.add_numbers)

    # Create execution context
    context = ToolContext(
        user_id="demo_user_123",
        session_id="demo_session_456",
        trace_id="demo_trace_789",
        tenant_id="demo_tenant",
        locale="en-US",
        timezone="UTC",
        auth={"user_role": "demo", "permissions": ["math:execute"]},
        extras={"environment": "demo", "version": "1.0.0"}
    )

    print(f"👤 Execution Context: User={context.user_id}, Session={context.session_id}")
    print()

    # Test cases demonstrating comprehensive logging
    test_cases = [
        {"name": "Basic Addition", "args": {"a": 10, "b": 5}},
        {"name": "Float Addition", "args": {"a": 3.14, "b": 2.86}},
        {"name": "String Coercion", "args": {"a": "10", "b": "5"}},
        {"name": "Large Numbers", "args": {"a": 1000000, "b": 500000}},
        {"name": "Error Simulation", "args": {"a": 10, "b": 5, "simulate_error": True}}
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test Case {i}: {test_case['name']}")
        print("-" * 40)

        try:
            result = await executor.execute(test_case["args"], context)

            print(f"✅ Success: {result.content['result']}")
            print(f"⏱️  Execution Time: {result.content['total_execution_time_ms']}ms")
            print(f"🆔 Operation ID: {result.content['operation_id']}")

        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"🔍 Error Type: {type(e).__name__}")

        print(f"📊 Total Events Logged: {len(logging_tool.execution_history)}")
        print()

    # Print execution summary
    print("📈 Execution Summary")
    print("=" * 30)
    print(f"Total Operations: {logging_tool.operation_count}")
    print(f"Successful Operations: {logging_tool.operation_count - logging_tool.error_count}")
    print(f"Failed Operations: {logging_tool.error_count}")
    print(f"Total Events Logged: {len(logging_tool.execution_history)}")

    # Show recent events
    if logging_tool.execution_history:
        print("\n🔍 Recent Events (Last 3):")
        for event in logging_tool.execution_history[-3:]:
            print(f"  • {event['event_type']} ({event['level']}): {event['details'].get('operation_id', 'N/A')}")

    print("\n🎉 Demo completed! The tool logged every aspect of execution.")


async def main():
    """Main function to run the demo"""
    try:
        await demonstrate_logging_addition_tool()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main())
