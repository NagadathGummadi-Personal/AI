"""
Comprehensive Test Suite for Tools Specification System

This module tests the complete tools system including:
- Tool specification and validation
- Tool execution with comprehensive logging
- Error handling and retry logic
- Metrics and observability
- Memory and caching functionality
"""

import asyncio
import pytest
import json
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

# Import the tools system
from core.tools import (
    ToolSpec,
    ToolParameter,
    ToolType,
    ToolReturnType,
    ToolReturnTarget,
    ToolContext,
    ToolError,
    BasicValidator,
    FunctionToolExecutor,
    BaseToolExecutor
)

from core.tools.implementations import (
    NoOpMemory,
    NoOpMetrics,
    NoOpTracer,
    NoOpLimiter
)

from core.tools.tool_types import (
    RetryConfig,
    CircuitBreakerConfig,
    IdempotencyConfig
)


class LoggingAdditionTool:
    """Addition tool that logs everything"""

    def __init__(self):
        self.execution_log = []

    async def add_numbers(self, args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
        """Add two numbers with comprehensive logging"""
        start_time = time.time()

        # Log input parameters
        self.execution_log.append({
            "event": "execution_started",
            "tool_name": "addition_tool",
            "args": args,
            "context": {
                "user_id": ctx.user_id,
                "session_id": ctx.session_id,
                "trace_id": ctx.trace_id
            },
            "timestamp": start_time
        })

        try:
            # Validate inputs
            a = args.get("a")
            b = args.get("b")

            if a is None or b is None:
                raise ToolError("Missing required parameters: 'a' and 'b' are required", retryable=False, code="MISSING_PARAMS")

            # Log parameter validation
            self.execution_log.append({
                "event": "parameters_validated",
                "a": a,
                "b": b,
                "a_type": type(a).__name__,
                "b_type": type(b).__name__,
                "timestamp": time.time()
            })

            # Perform addition with potential error simulation
            if args.get("simulate_error"):
                raise ToolError("Simulated error for testing", retryable=True, code="SIMULATED_ERROR")

            result = float(a) + float(b)

            # Log successful calculation
            self.execution_log.append({
                "event": "calculation_completed",
                "result": result,
                "timestamp": time.time()
            })

            # Log metrics if available
            if ctx.metrics:
                await ctx.metrics.incr("addition_operations", tags={"status": "success"})
                await ctx.metrics.timing_ms("addition_duration", int((time.time() - start_time) * 1000))

            # Log tracing if available
            if ctx.tracer:
                async with ctx.tracer.span("addition_calculation", {"operation": "add", "operands": [a, b]}) as span_id:
                    pass

            return {
                "result": result,
                "operation": "addition",
                "operands": [a, b],
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }

        except Exception as e:
            # Log error
            error_time = time.time()
            self.execution_log.append({
                "event": "execution_error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": error_time
            })

            # Log metrics for error
            if ctx.metrics:
                await ctx.metrics.incr("addition_operations", tags={"status": "error"})
                await ctx.metrics.timing_ms("addition_duration", int((error_time - start_time) * 1000))

            raise


class TestToolsSystem:
    """Test class for the tools system"""

    @pytest.fixture
    def addition_tool_spec(self):
        """Create addition tool specification"""
        parameters = [
            ToolParameter(
                name="a",
                type="number",
                description="First number to add",
                required=True,
                examples=[10, 3.14]
            ),
            ToolParameter(
                name="b",
                type="number",
                description="Second number to add",
                required=True,
                examples=[5, 2.71]
            ),
            ToolParameter(
                name="simulate_error",
                type="boolean",
                description="Whether to simulate an error",
                required=False,
                default=False
            )
        ]

        return ToolSpec(
            id="addition-tool-v1",
            version="1.0.0",
            tool_name="addition_tool",
            description="Adds two numbers with comprehensive logging",
            tool_type=ToolType.FUNCTION,
            parameters=parameters,
            return_type=ToolReturnType.JSON,
            return_target=ToolReturnTarget.STEP,
            timeout_s=30,
            retry=RetryConfig(max_attempts=2),
            circuit_breaker=CircuitBreakerConfig(enabled=True, failure_threshold=2),
            idempotency=IdempotencyConfig(enabled=True, key_fields=["a", "b"]),
            metrics_tags={"category": "math", "operation": "addition"}
        )

    @pytest.fixture
    def logging_addition_impl(self):
        """Create logging addition tool implementation"""
        return LoggingAdditionTool()

    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return BasicValidator()

    @pytest.fixture
    def mock_context(self):
        """Create mock tool context"""
        return ToolContext(
            user_id="test_user",
            session_id="test_session",
            trace_id="test_trace_123",
            memory=NoOpMemory(),
            metrics=NoOpMetrics(),
            tracer=NoOpTracer(),
            limiter=NoOpLimiter()
        )

    def test_tool_spec_creation(self, addition_tool_spec):
        """Test tool specification creation"""
        assert addition_tool_spec.id == "addition-tool-v1"
        assert addition_tool_spec.tool_name == "addition_tool"
        assert addition_tool_spec.tool_type == ToolType.FUNCTION
        assert len(addition_tool_spec.parameters) == 3
        assert addition_tool_spec.return_type == ToolReturnType.JSON
        assert addition_tool_spec.timeout_s == 30

    def test_parameter_validation(self, validator, addition_tool_spec):
        """Test parameter validation"""
        # Valid parameters
        valid_args = {"a": 10, "b": 5}
        asyncio.run(validator.validate(valid_args, addition_tool_spec))

        # Missing required parameter
        with pytest.raises(ToolError) as exc_info:
            asyncio.run(validator.validate({"a": 10}, addition_tool_spec))
        assert "Missing required parameter" in str(exc_info.value)

        # Invalid parameter type
        with pytest.raises(ToolError) as exc_info:
            asyncio.run(validator.validate({"a": "not_a_number", "b": 5}, addition_tool_spec))
        assert "failed validation" in str(exc_info.value)

    def test_successful_addition(self, addition_tool_spec, logging_addition_impl, mock_context):
        """Test successful addition operation"""
        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        result = asyncio.run(executor.execute({"a": 10, "b": 5}, mock_context))

        assert result.return_type == ToolReturnType.JSON
        assert result.content["result"] == 15.0
        assert result.content["operation"] == "addition"
        assert result.content["operands"] == [10, 5]

        # Check execution log
        log = logging_addition_impl.execution_log
        assert len(log) >= 3  # Should have start, validation, and completion events
        assert log[0]["event"] == "execution_started"
        assert log[-1]["event"] == "calculation_completed"

    def test_addition_with_floats(self, addition_tool_spec, logging_addition_impl, mock_context):
        """Test addition with floating point numbers"""
        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        result = asyncio.run(executor.execute({"a": 3.14, "b": 2.86}, mock_context))

        assert result.content["result"] == 6.0
        assert result.content["operands"] == [3.14, 2.86]

    def test_addition_with_simulated_error(self, addition_tool_spec, logging_addition_impl, mock_context):
        """Test addition with simulated error"""
        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        with pytest.raises(ToolError) as exc_info:
            asyncio.run(executor.execute({"a": 10, "b": 5, "simulate_error": True}, mock_context))

        assert exc_info.value.code == "SIMULATED_ERROR"
        assert exc_info.value.retryable == True

        # Check execution log includes error
        log = logging_addition_impl.execution_log
        assert any(entry["event"] == "execution_error" for entry in log)

    def test_addition_with_missing_parameters(self, addition_tool_spec, logging_addition_impl, mock_context):
        """Test addition with missing required parameters"""
        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        with pytest.raises(ToolError) as exc_info:
            asyncio.run(executor.execute({"a": 10}, mock_context))  # Missing 'b'

        assert exc_info.value.code == "MISSING_PARAMS"

    def test_context_metadata(self, addition_tool_spec, logging_addition_impl):
        """Test context metadata handling"""
        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        context = ToolContext(
            user_id="user123",
            session_id="session456",
            trace_id="trace789",
            locale="en-US",
            timezone="UTC"
        )

        result = asyncio.run(executor.execute({"a": 1, "b": 2}, context))

        # Check that context was logged
        log = logging_addition_impl.execution_log
        context_log = log[0]["context"]
        assert context_log["user_id"] == "user123"
        assert context_log["session_id"] == "session456"
        assert context_log["trace_id"] == "trace789"

    def test_execution_metrics(self, addition_tool_spec, logging_addition_impl):
        """Test execution metrics collection"""
        # Mock metrics implementation
        metrics = AsyncMock()
        context = ToolContext(metrics=metrics)

        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        result = asyncio.run(executor.execute({"a": 7, "b": 3}, context))

        # Verify metrics were called
        metrics.incr.assert_called()
        metrics.timing_ms.assert_called()

    def test_parameter_coercion(self, addition_tool_spec, logging_addition_impl, mock_context):
        """Test parameter type coercion"""
        # Test with string numbers that should be coerced
        executor = FunctionToolExecutor(addition_tool_spec, logging_addition_impl.add_numbers)

        result = asyncio.run(executor.execute({"a": "10", "b": "5"}, mock_context))

        assert result.content["result"] == 15.0

    def test_timeout_configuration(self, addition_tool_spec):
        """Test timeout configuration"""
        assert addition_tool_spec.timeout_s == 30

        # Create spec with custom timeout
        custom_timeout_spec = ToolSpec(
            id="test-timeout",
            tool_name="test",
            description="test",
            tool_type=ToolType.FUNCTION,
            parameters=[],
            timeout_s=60
        )

        assert custom_timeout_spec.timeout_s == 60

    def test_retry_configuration(self, addition_tool_spec):
        """Test retry configuration"""
        retry = addition_tool_spec.retry
        assert retry.max_attempts == 2
        assert retry.base_delay_s == 0.2

    def test_circuit_breaker_configuration(self, addition_tool_spec):
        """Test circuit breaker configuration"""
        cb = addition_tool_spec.circuit_breaker
        assert cb.enabled == True
        assert cb.failure_threshold == 2
        assert cb.recovery_timeout_s == 30

    def test_idempotency_configuration(self, addition_tool_spec):
        """Test idempotency configuration"""
        idemp = addition_tool_spec.idempotency
        assert idemp.enabled == True
        assert idemp.key_fields == ["a", "b"]
        assert idemp.ttl_s == 3600

    def test_metrics_tags(self, addition_tool_spec):
        """Test metrics tags"""
        assert addition_tool_spec.metrics_tags["category"] == "math"
        assert addition_tool_spec.metrics_tags["operation"] == "addition"


class TestToolErrorHandling:
    """Test class for error handling scenarios"""

    def test_tool_error_structure(self):
        """Test ToolError structure"""
        error = ToolError("Test error", retryable=True, code="TEST_ERROR")

        assert str(error) == "Test error"
        assert error.retryable == True
        assert error.code == "TEST_ERROR"

    def test_non_retryable_error(self):
        """Test non-retryable error"""
        error = ToolError("Validation failed", retryable=False, code="VALIDATION_ERROR")
        assert error.retryable == False

    def test_default_error_values(self):
        """Test default ToolError values"""
        error = ToolError("Default error")
        assert error.retryable == False
        assert error.code == "TOOL_ERROR"


class TestComprehensiveLogging:
    """Test comprehensive logging functionality"""

    @pytest.fixture
    def comprehensive_tool_spec(self):
        """Create tool spec with comprehensive logging"""
        parameters = [
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=True,
                enum=["add", "subtract", "multiply", "divide"]
            ),
            ToolParameter(
                name="values",
                type="array",
                description="Array of numbers",
                required=True,
                items=ToolParameter(
                    name="value",
                    type="number",
                    description="A number"
                ),
                min_items=2
            )
        ]

        return ToolSpec(
            id="comprehensive-logging-v1",
            version="1.0.0",
            tool_name="comprehensive_logger",
            description="Tool that logs every aspect of execution",
            tool_type=ToolType.FUNCTION,
            parameters=parameters,
            return_type=ToolReturnType.JSON,
            return_target=ToolReturnTarget.STEP,
            timeout_s=60,
            metrics_tags={"category": "logging", "level": "comprehensive"}
        )

    def test_array_parameter_logging(self, comprehensive_tool_spec):
        """Test logging with array parameters"""
        class ArrayOperationTool:
            def __init__(self):
                self.log = []

            async def operate(self, args: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
                operation = args["operation"]
                values = args["values"]

                # Log array processing
                self.log.append({
                    "event": "array_processing_started",
                    "operation": operation,
                    "array_length": len(values),
                    "array_sum": sum(values),
                    "timestamp": time.time()
                })

                if operation == "add":
                    result = sum(values)
                elif operation == "multiply":
                    result = 1
                    for v in values:
                        result *= v
                else:
                    raise ToolError(f"Unsupported operation: {operation}", retryable=False)

                self.log.append({
                    "event": "array_processing_completed",
                    "result": result,
                    "timestamp": time.time()
                })

                return {"result": result, "operation": operation, "processed_values": values}

        tool = ArrayOperationTool()
        executor = FunctionToolExecutor(comprehensive_tool_spec, tool.operate)

        context = ToolContext(user_id="test_user", session_id="test_session")

        result = asyncio.run(executor.execute({
            "operation": "add",
            "values": [1, 2, 3, 4, 5]
        }, context))

        assert result.content["result"] == 15
        assert result.content["operation"] == "add"
        assert result.content["processed_values"] == [1, 2, 3, 4, 5]

        # Check comprehensive logging
        assert len(tool.log) >= 2
        assert tool.log[0]["event"] == "array_processing_started"
        assert tool.log[1]["event"] == "array_processing_completed"


# Integration test
class TestIntegration:
    """Integration tests for the complete system"""

    async def test_full_execution_pipeline(self):
        """Test the complete execution pipeline with logging"""
        from core.tools import ToolRegistry

        # This would test the full registry system
        # For now, just test individual components work together
        pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
