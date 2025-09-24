"""
Integration tests for the modular logging system.

This module contains comprehensive integration tests that verify:
- How LoggerAdaptor, DurationLogger, DelayedLogger, and ConfigManager work together
- End-to-end functionality across module boundaries
- Configuration flow and environment-specific behavior
- Complete logging workflows with all features enabled

Test Structure:
===============
1. Test Constants: Shared test data and configuration
2. Fixtures: Setup for integration scenarios
3. Integration Tests: End-to-end functionality tests
4. Module Interaction Tests: Cross-module functionality
5. Complete Workflow Tests: Full feature integration

Key Integration Points:
=======================
- ConfigManager -> LoggerAdaptor (configuration loading)
- ConfigManager -> DurationLogger (duration thresholds)
- ConfigManager -> DelayedLogger (delayed logging settings)
- LoggerAdaptor -> DurationLogger (log_duration method)
- LoggerAdaptor -> DelayedLogger (logger instance sharing)
- DurationLogger -> LoggerAdaptor (duration logging)
- DelayedLogger -> LoggerAdaptor (fallback logging)

Testing Standards:
==================
- Each test verifies a complete user workflow
- Comprehensive mocking where necessary
- Real configuration files for realistic testing
- Error scenarios and edge cases covered
- Performance implications considered

Pytest Markers:
===============
- integration: All tests in this module
"""

import pytest
import json
import time
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from utils.logging.LoggerAdaptor import LoggerAdaptor
from utils.logging.DurationLogger import DurationLogger, durationlogger
from utils.logging.DelayedLogger import DelayedLogger
from utils.logging.ConfigManager import ConfigManager
from utils.logging.Enum import Environment, LoggingFormat, RedactionConfig


class TestIntegrationConstants:
    """Constants used throughout integration tests."""

    # Sample configuration data
    SAMPLE_CONFIG = {
        "backend": "json",
        "level": "INFO",
        "log_directory": "./test_logs",
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "json": {
                "format": "%(timestamp)s %(level)s %(logger)s %(message)s",
                "class": "logging.Formatter"
            },
            "detailed": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(extra)s",
                "class": "logging.Formatter"
            }
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        },
        "duration_logging": {
            "slow_threshold_seconds": 1.0,
            "warn_threshold_seconds": 5.0,
            "error_threshold_seconds": 30.0
        },
        "delayed_logging": {
            "enabled": True,
            "queue_size_kb": 10,
            "flush_on_exception": True,
            "flush_on_completion": True
        },
        "redaction": {
            "enabled": True,
            "placeholder": "[REDACTED]",
            "patterns": [
                {
                    "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
                    "placeholder": "[CREDIT_CARD]"
                },
                {
                    "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
                    "placeholder": "[SSN]"
                },
                {
                    "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    "placeholder": "[EMAIL]"
                }
            ]
        }
    }

    # Sample log messages
    TEST_MESSAGES = {
        "simple": "Test message",
        "with_context": "User login successful",
        "with_sensitive": "User john@example.com logged in with credit card 4111-1111-1111-1111",
        "structured": "Processing batch of 100 records",
        "error": "Database connection failed"
    }

    # Test contexts
    TEST_CONTEXTS = {
        "user_login": {
            "user_id": "12345",
            "username": "john_doe",
            "ip_address": "192.168.1.100"
        },
        "batch_processing": {
            "batch_id": "batch_123",
            "records_processed": 100,
            "success_rate": 0.95
        },
        "error_context": {
            "error_code": "DB_CONN_001",
            "retry_count": 3,
            "last_attempt": "2025-01-15T10:30:00Z"
        }
    }


class TestIntegrationFixtures:
    """Fixtures for integration testing."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary configuration file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(TestIntegrationConstants.SAMPLE_CONFIG, f, indent=2)
            temp_file = f.name

        yield temp_file

        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def logger_adaptor(self):
        """Create a LoggerAdaptor instance with test configuration."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = TestIntegrationConstants.SAMPLE_CONFIG
            logger = LoggerAdaptor("integration_test")
            yield logger

    @pytest.fixture
    def duration_logger(self, logger_adaptor):
        """Create a DurationLogger instance using LoggerAdaptor."""
        return DurationLogger(logger_adaptor)

    @pytest.fixture
    def delayed_logger(self, logger_adaptor):
        """Create a DelayedLogger instance using LoggerAdaptor."""
        dl = DelayedLogger(logger_adaptor)
        dl.configure(TestIntegrationConstants.SAMPLE_CONFIG)
        yield dl

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigManager instance."""
        return ConfigManager()


@pytest.mark.integration
class TestModuleIntegration:
    """Test integration between individual modules."""

    def test_config_manager_to_logger_adaptor(self, config_manager, temp_config_file):
        """Test ConfigManager providing configuration to LoggerAdaptor."""
        # Load configuration using ConfigManager
        config = config_manager.load_config(temp_config_file)

        # Verify configuration structure
        assert config["backend"] == "json"
        assert config["level"] == "INFO"
        assert "duration_logging" in config
        assert "delayed_logging" in config
        assert "redaction" in config

        # Create LoggerAdaptor with loaded config
        with patch('utils.logging.LoggerAdaptor.ConfigManager') as mock_cm:
            mock_cm.return_value.load_config.return_value = config

            logger = LoggerAdaptor("test_config_integration")

            # Verify logger was configured with the loaded config
            assert logger._config is not None
            assert logger.current_environment() in Environment.__members__

    def test_duration_logger_with_logger_adaptor(self, duration_logger, logger_adaptor):
        """Test DurationLogger using LoggerAdaptor for logging."""
        # Mock the log_duration method
        with patch.object(logger_adaptor, 'log_duration') as mock_log_duration:
            # Test decorator functionality
            @duration_logger
            def test_function():
                time.sleep(0.01)  # Simulate work
                return "success"

            result = test_function()

            # Verify function executed correctly
            assert result == "success"

            # Verify log_duration was called with proper parameters
            mock_log_duration.assert_called_once()
            call_args = mock_log_duration.call_args

            assert call_args[0][0] == "test_function"  # operation name
            assert call_args[0][1] > 0  # duration > 0
            assert call_args[1]["success"] is True

    def test_delayed_logger_with_logger_adaptor(self, delayed_logger, logger_adaptor):
        """Test DelayedLogger using LoggerAdaptor for logging."""
        # Mock immediate logging fallback
        with patch.object(logger_adaptor, '_log_message') as mock_log:
            # Send a delayed log message
            delayed_logger.info_delayed("Delayed test message", user_id="123")

            # Verify message was queued (not logged immediately)
            mock_log.assert_not_called()

            # Flush the logs
            delayed_logger.flush_delayed_logs()

            # Verify message was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            assert call_args[0] == 'INFO'  # log level
            assert "Delayed test message" in call_args[1]  # message

    def test_config_manager_to_duration_logger(self, config_manager, temp_config_file):
        """Test ConfigManager providing duration thresholds to DurationLogger."""
        config = config_manager.load_config(temp_config_file)
        duration_config = config_manager.get_duration_config()

        # Verify duration configuration
        assert duration_config["slow_threshold_seconds"] == 1.0
        assert duration_config["warn_threshold_seconds"] == 5.0
        assert duration_config["error_threshold_seconds"] == 30.0

        # Test that DurationLogger can access these thresholds
        # (Implementation would need to use these thresholds for log level determination)
        assert duration_config["slow_threshold_seconds"] > 0
        assert duration_config["warn_threshold_seconds"] > duration_config["slow_threshold_seconds"]
        assert duration_config["error_threshold_seconds"] > duration_config["warn_threshold_seconds"]


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete logging workflows using all modules together."""

    def test_basic_logging_workflow(self, logger_adaptor):
        """Test basic logging workflow with LoggerAdaptor."""
        with patch.object(logger_adaptor, '_log_message') as mock_log:
            # Set context
            logger_adaptor.set_context(service="test_service", version="1.0")

            # Log various types of messages
            logger_adaptor.info(TestIntegrationConstants.TEST_MESSAGES["simple"])
            logger_adaptor.info(TestIntegrationConstants.TEST_MESSAGES["with_context"],
                               **TestIntegrationConstants.TEST_CONTEXTS["user_login"])

            # Verify logging calls
            assert mock_log.call_count == 2

            # Check first call
            first_call = mock_log.call_args_list[0]
            assert first_call[0][0] == 'INFO'
            assert TestIntegrationConstants.TEST_MESSAGES["simple"] in first_call[0][1]

            # Check second call includes context
            second_call = mock_log.call_args_list[1]
            assert second_call[0][0] == 'INFO'
            assert TestIntegrationConstants.TEST_CONTEXTS["user_login"]["user_id"] in str(second_call[1])

    def test_duration_logging_workflow(self, duration_logger):
        """Test duration logging workflow with DurationLogger."""
        with patch.object(duration_logger.logger, 'log_duration') as mock_log_duration:
            # Use duration logger as decorator
            @duration_logger
            def slow_operation():
                time.sleep(0.05)  # Simulate slow operation
                return "completed"

            result = slow_operation()

            # Verify operation completed
            assert result == "completed"

            # Verify duration was logged
            mock_log_duration.assert_called_once()
            call_args = mock_log_duration.call_args
            assert call_args[0][0] == "slow_operation"
            assert call_args[0][1] >= 0.05  # Duration should be at least 0.05s
            assert call_args[1]["success"] is True

    def test_delayed_logging_workflow(self, delayed_logger):
        """Test delayed logging workflow with DelayedLogger."""
        with patch.object(delayed_logger.logger, '_log_message') as mock_log:
            # Send multiple delayed messages
            delayed_logger.info_delayed("Starting batch processing")
            delayed_logger.info_delayed("Processing record 1", record_id="1")
            delayed_logger.info_delayed("Processing record 2", record_id="2")
            delayed_logger.warning_delayed("Minor issue detected", issue_code="MINOR_001")

            # Verify no immediate logging
            mock_log.assert_not_called()

            # Flush logs
            delayed_logger.flush_delayed_logs()

            # Verify all messages were logged
            assert mock_log.call_count == 4

            # Check that messages contain expected content
            call_args_list = mock_log.call_args_list
            messages = [call[0][1] for call in call_args_list]
            assert any("Starting batch processing" in msg for msg in messages)
            assert any("record_id" in str(call[1]) for call in call_args_list)

    def test_redaction_workflow(self, logger_adaptor):
        """Test redaction workflow with LoggerAdaptor."""
        # Enable redaction
        logger_adaptor.enable_redaction(enabled=True)

        # Add redaction patterns
        logger_adaptor.add_redaction_pattern(
            pattern=r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
            placeholder="[CREDIT_CARD]"
        )

        with patch.object(logger_adaptor, '_log_message') as mock_log:
            # Log message with sensitive data
            sensitive_message = TestIntegrationConstants.TEST_MESSAGES["with_sensitive"]
            logger_adaptor.info(sensitive_message)

            # Verify message was logged
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]

            # Verify sensitive data was redacted
            logged_message = call_args[1]
            assert "[CREDIT_CARD]" in logged_message
            assert "[EMAIL]" in logged_message
            assert "4111-1111-1111-1111" not in logged_message
            assert "john@example.com" not in logged_message

    def test_context_and_redaction_together(self, logger_adaptor):
        """Test context management combined with redaction."""
        # Set context
        logger_adaptor.set_context(
            **TestIntegrationConstants.TEST_CONTEXTS["user_login"]
        )

        # Enable redaction
        logger_adaptor.enable_redaction(enabled=True)

        with patch.object(logger_adaptor, '_log_message') as mock_log:
            # Log message with context and sensitive data
            message = "User login with sensitive data"
            logger_adaptor.info(message)

            # Verify both context and redaction worked
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]

            # Message should be logged
            assert message in call_args[1]

            # Context should be preserved in kwargs
            call_kwargs = mock_log.call_args[1]
            assert "user_id" in call_kwargs
            assert call_kwargs["user_id"] == "12345"


@pytest.mark.integration
class TestCrossModuleFunctionality:
    """Test functionality that spans multiple modules."""

    def test_duration_logger_with_different_backends(self, logger_adaptor):
        """Test DurationLogger works with different LoggerAdaptor backends."""
        backends = ['standard', 'json', 'detailed']

        for backend in backends:
            with patch.object(LoggerAdaptor, '_load_config') as mock_load:
                config = TestIntegrationConstants.SAMPLE_CONFIG.copy()
                config["backend"] = backend
                mock_load.return_value = config

                logger = LoggerAdaptor("test_backend")
                duration_logger = DurationLogger(logger)

                with patch.object(logger, '_log_message') as mock_log:
                    @duration_logger
                    def test_function():
                        time.sleep(0.01)
                        return "success"

                    result = test_function()

                    # Verify function worked
                    assert result == "success"

                    # Verify logging occurred (backend-specific format will vary)
                    mock_log.assert_called_once()
                    call_args = mock_log.call_args[0]
                    assert call_args[0] == 'INFO'  # Log level should be INFO

    def test_delayed_logger_with_different_environments(self, logger_adaptor):
        """Test DelayedLogger behavior in different environments."""
        environments = ['dev', 'prod', 'test']

        for env in environments:
            with patch.object(LoggerAdaptor, '_load_config') as mock_load:
                config = TestIntegrationConstants.SAMPLE_CONFIG.copy()
                mock_load.return_value = config

                with patch.dict(os.environ, {'ENVIRONMENT': env}):
                    logger = LoggerAdaptor("test_env")
                    delayed_logger = DelayedLogger(logger)

                    # Configure delayed logger
                    delayed_logger.configure(config)

                    # Verify environment-specific behavior
                    if env == 'prod':
                        # Production should be more conservative
                        assert not delayed_logger.delayed_logging_enabled
                    else:
                        # Other environments can use delayed logging
                        assert delayed_logger.delayed_logging_enabled

    def test_config_manager_environment_detection(self, config_manager):
        """Test ConfigManager's environment detection affects other modules."""
        environments = [
            ('dev', 'development'),
            ('prod', 'production'),
            ('test', 'testing')
        ]

        for env_var, expected_env in environments:
            with patch.dict(os.environ, {'ENVIRONMENT': env_var}):
                detected_env = config_manager.detect_environment()
                assert detected_env == expected_env

                # Test that environment affects config file selection
                config_file = config_manager.get_environment_config_file(expected_env)
                assert f"log_config_{env_var}" in config_file or f"log_config_{expected_env}" in config_file


@pytest.mark.integration
class TestErrorScenarios:
    """Test error handling across module boundaries."""

    def test_duration_logger_handles_logger_errors(self, logger_adaptor):
        """Test DurationLogger handles errors from LoggerAdaptor gracefully."""
        duration_logger = DurationLogger(logger_adaptor)

        with patch.object(logger_adaptor, 'log_duration', side_effect=Exception("Logger error")):
            # Should not raise exception, but handle it gracefully
            @duration_logger
            def failing_function():
                return "success"

            # Function should still execute
            result = failing_function()
            assert result == "success"

    def test_delayed_logger_handles_queue_errors(self, logger_adaptor):
        """Test DelayedLogger handles queue processing errors."""
        delayed_logger = DelayedLogger(logger_adaptor)
        delayed_logger.configure(TestIntegrationConstants.SAMPLE_CONFIG)

        with patch.object(logger_adaptor, '_log_message', side_effect=Exception("Log error")):
            # Should not raise exception, but handle it gracefully
            delayed_logger.info_delayed("Test message")

            # Should fall back to immediate logging or handle error
            # (Implementation-specific behavior)

    def test_config_manager_handles_invalid_config(self, config_manager):
        """Test ConfigManager handles invalid configuration gracefully."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            # Should return default config instead of crashing
            config = config_manager.load_config("invalid.json")

            # Should have default structure
            assert "backend" in config
            assert "level" in config
            assert "handlers" in config


@pytest.mark.integration
class TestPerformanceScenarios:
    """Test performance implications of module interactions."""

    def test_high_frequency_logging(self, logger_adaptor):
        """Test high-frequency logging with context management."""
        # Set up context once
        logger_adaptor.set_context(service="perf_test", version="1.0")

        with patch.object(logger_adaptor, '_log_message') as mock_log:
            # Log many messages with context
            for i in range(100):
                logger_adaptor.info(f"Message {i}", batch_id=i, record_count=1000)

            # Verify all messages were logged with context
            assert mock_log.call_count == 100

            # Check that context was included in calls
            for call in mock_log.call_args_list:
                assert "service" in call[1]
                assert call[1]["service"] == "perf_test"

    def test_concurrent_module_usage(self, logger_adaptor):
        """Test concurrent usage of multiple modules."""
        duration_logger = DurationLogger(logger_adaptor)
        delayed_logger = DelayedLogger(logger_adaptor)
        delayed_logger.configure(TestIntegrationConstants.SAMPLE_CONFIG)

        with patch.object(logger_adaptor, '_log_message') as mock_log:
            # Use multiple modules concurrently
            @duration_logger
            def fast_operation():
                return "fast"

            # Duration logging
            result1 = fast_operation()

            # Delayed logging
            delayed_logger.info_delayed("Concurrent test")

            # Immediate logging
            logger_adaptor.info("Direct logging")

            # Flush delayed logs
            delayed_logger.flush_delayed_logs()

            # Verify all logging occurred
            assert result1 == "fast"
            assert mock_log.call_count >= 2  # At least direct + flushed delayed

    def test_memory_efficient_configuration(self, config_manager):
        """Test that configuration loading is memory efficient."""
        # Load same config multiple times
        configs = []
        for _ in range(10):
            config = config_manager.load_config("dummy.json")
            configs.append(config)

        # All configs should be identical (ConfigManager may cache)
        for config in configs[1:]:
            assert config == configs[0]
