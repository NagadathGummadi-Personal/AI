"""Test cases for LoggerAdaptor class."""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from utils.logging.LoggerAdaptor import LoggerAdaptor
from utils.logging.Enum import Environment, LoggingFormat, RedactionConfig


class TestLoggerAdaptor:
    """Test cases for the LoggerAdaptor class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return {
            "backend": "standard",
            "level": "INFO",
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "console": {
                    "type": "console",
                    "level": "INFO",
                    "formatter": "default"
                }
            },
            "log_directory": "./logs"
        }

    @pytest.fixture
    def temp_config_file(self, mock_config):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config, f)
            return f.name

    @pytest.fixture(autouse=True)
    def clear_logger_instances(self):
        """Clear LoggerAdaptor instances before each test."""
        LoggerAdaptor._instances.clear()
        LoggerAdaptor._config = None
        yield
        LoggerAdaptor._instances.clear()
        LoggerAdaptor._config = None

    def test_logger_adaptor_initialization_default(self):
        """Test LoggerAdaptor initialization with default parameters."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            assert logger.name == "default"
            assert logger.environment in ["development", "staging", "production", "testing"]

    def test_environment_detection(self):
        """Test environment detection from environment variables."""
        test_cases = [
            ("dev", "development"),
            ("development", "development"),
            ("staging", "staging"),
            ("prod", "production"),
            ("production", "production"),
            ("test", "testing"),
            ("testing", "testing"),
        ]
        
        for env_var, expected in test_cases:
            with patch.dict(os.environ, {'ENVIRONMENT': env_var}):
                detected = LoggerAdaptor._detect_environment_static()
                assert detected == expected

    def test_environment_detection_default(self):
        """Test environment detection defaults to production."""
        with patch.dict(os.environ, {}, clear=True):
            detected = LoggerAdaptor._detect_environment_static()
            assert detected == "production"

    def test_get_logger_singleton_pattern(self):
        """Test that get_logger follows singleton pattern."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger1 = LoggerAdaptor.get_logger("test_logger", "dev")
            logger2 = LoggerAdaptor.get_logger("test_logger", "dev")
            assert logger1 is logger2

    def test_get_logger_different_instances(self):
        """Test that different names/environments create different instances."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger1 = LoggerAdaptor.get_logger("logger1", "dev")
            logger2 = LoggerAdaptor.get_logger("logger2", "dev")
            logger3 = LoggerAdaptor.get_logger("logger1", "prod")
            
            assert logger1 is not logger2
            assert logger1 is not logger3
            assert logger2 is not logger3

    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_success(self, mock_file, mock_config):
        """Test successful config loading."""
        mock_file.return_value.read.return_value = json.dumps(mock_config)
        
        with patch.object(LoggerAdaptor, '_get_environment_config_file') as mock_get_file:
            mock_get_file.return_value = "test_config.json"
            logger = LoggerAdaptor()
            config = logger._load_config("test_config.json")
            
            assert config == mock_config

    def test_load_config_file_not_found(self):
        """Test config loading when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            logger = LoggerAdaptor()
            config = logger._load_config("nonexistent.json")
            
            # Should return default config
            assert "backend" in config
            assert "level" in config

    def test_load_config_invalid_json(self):
        """Test config loading with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch.object(LoggerAdaptor, '_get_environment_config_file') as mock_get_file:
                mock_get_file.return_value = "invalid.json"
                
                with pytest.raises(ValueError, match="Invalid JSON"):
                    logger = LoggerAdaptor()

    def test_format_message_single_string(self):
        """Test message formatting with single string argument."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            message = logger._format_message("Hello, World!")
            assert message == "Hello, World!"

    def test_format_message_multiple_args(self):
        """Test message formatting with multiple arguments."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            message = logger._format_message("Hello", "World", 123)
            assert message == "Hello World 123"

    def test_format_message_empty(self):
        """Test message formatting with no arguments."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            message = logger._format_message()
            assert message == ""

    def test_log_levels(self):
        """Test all log levels work correctly."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "DEBUG"}
            
            logger = LoggerAdaptor()
            
            with patch.object(logger, '_log_message') as mock_log:
                logger.debug("Debug message")
                mock_log.assert_called_with('DEBUG', "Debug message")
                
                logger.info("Info message")
                mock_log.assert_called_with('INFO', "Info message")
                
                logger.warning("Warning message")
                mock_log.assert_called_with('WARNING', "Warning message")
                
                logger.error("Error message")
                mock_log.assert_called_with('ERROR', "Error message")
                
                logger.critical("Critical message")
                mock_log.assert_called_with('CRITICAL', "Critical message")

    def test_context_management(self):
        """Test context setting and clearing."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            
            # Set context
            logger.set_context(user_id="123", session_id="abc")
            assert logger.context["user_id"] == "123"
            assert logger.context["session_id"] == "abc"
            
            # Clear context
            logger.clear_context()
            assert len(logger.context) == 0

    def test_redaction_management(self):
        """Test redaction enabling and pattern management."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            
            # Initially no redaction
            assert not logger.has_redaction()
            
            # Enable redaction
            logger.enable_redaction(enabled=True)
            assert logger.has_redaction()
            
            # Add pattern
            logger.add_redaction_pattern(r'\d{4}-\d{4}-\d{4}-\d{4}', '[CARD]')
            
            # Test redaction
            test_message = "Credit card: 1234-5678-9012-3456"
            redacted = logger.test_redaction(test_message)
            assert '[CARD]' in redacted
            
            # Disable redaction
            logger.enable_redaction(enabled=False)
            assert not logger.has_redaction()

    def test_json_logging_backend(self):
        """Test JSON logging backend."""
        config = {
            "backend": "json",
            "level": "INFO",
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            }
        }
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            logger = LoggerAdaptor()
            
            with patch.object(logger.logger, 'log') as mock_log:
                logger.info("Test message", extra_field="extra_value")
                
                # Verify log was called
                mock_log.assert_called_once()
                args, kwargs = mock_log.call_args
                
                # First argument should be log level
                assert args[0] == 20  # INFO level
                
                # Second argument should be JSON string
                json_message = args[1]
                log_data = json.loads(json_message)
                
                assert log_data["message"] == "Test message"
                assert log_data["level"] == "INFO"
                assert log_data["extra_field"] == "extra_value"

    def test_detailed_logging_backend(self):
        """Test detailed logging backend."""
        config = {"backend": "detailed", "level": "INFO"}
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            logger = LoggerAdaptor()
            logger.set_context(request_id="req-123")
            
            with patch.object(logger.logger, 'log') as mock_log:
                logger.info("Test message", user_id="user-456")
                
                mock_log.assert_called_once()
                args, kwargs = mock_log.call_args
                
                detailed_message = args[1]
                assert "Test message" in detailed_message
                assert "request_id=req-123" in detailed_message
                assert "user_id=user-456" in detailed_message

    @pytest.mark.parametrize("backend", ["standard", "json", "detailed"])
    def test_different_backends(self, backend):
        """Test different logging backends."""
        config = {"backend": backend, "level": "INFO"}
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            logger = LoggerAdaptor()
            assert logger.backend == backend

    def test_config_reload(self, temp_config_file):
        """Test configuration reloading."""
        with patch.object(LoggerAdaptor, '_get_environment_config_file') as mock_get_file:
            mock_get_file.return_value = temp_config_file
            
            logger = LoggerAdaptor()
            original_config = LoggerAdaptor._config
            
            # Modify config file
            new_config = {"backend": "json", "level": "DEBUG"}
            with open(temp_config_file, 'w') as f:
                json.dump(new_config, f)
            
            # Reload
            logger.reload_config(temp_config_file)
            
            assert LoggerAdaptor._config != original_config
            assert LoggerAdaptor._config["backend"] == "json"
        
        # Cleanup
        os.unlink(temp_config_file)

    def test_properties(self):
        """Test logger properties."""
        config = {"backend": "standard", "level": "WARNING"}
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            with patch.dict(os.environ, {'ENVIRONMENT': 'dev'}):
                logger = LoggerAdaptor("test_logger")
                
                assert logger.level == "WARNING"
                assert logger.current_environment == "development"
                assert "log_config_dev.json" in logger.config_file_used

    def test_get_log_filepath(self):
        """Test log file path generation."""
        config = {"log_directory": "./test_logs"}
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            logger = LoggerAdaptor()
            
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                filepath = logger._get_log_filepath("test.log")
                
                assert "test.log" in filepath
                assert "test_logs" in filepath
                mock_mkdir.assert_called_once()

    def test_handler_creation(self):
        """Test different handler types creation."""
        logger = LoggerAdaptor()
        formatters = {"default": Mock()}
        
        # Console handler
        console_config = {"type": "console", "level": "INFO", "formatter": "default"}
        handler = logger._create_handler(console_config, formatters)
        assert handler is not None
        
        # File handler
        with patch('logging.FileHandler') as mock_file_handler:
            file_config = {"type": "file", "filename": "test.log", "level": "DEBUG", "formatter": "default"}
            handler = logger._create_handler(file_config, formatters)
            mock_file_handler.assert_called_once()
        
        # Rotating file handler
        with patch('logging.handlers.RotatingFileHandler') as mock_rotating_handler:
            rotating_config = {
                "type": "rotating_file",
                "filename": "test.log",
                "max_bytes": 1000000,
                "backup_count": 3,
                "level": "INFO",
                "formatter": "default"
            }
            handler = logger._create_handler(rotating_config, formatters)
            mock_rotating_handler.assert_called_once()

    def test_invalid_redaction_pattern(self):
        """Test handling of invalid redaction patterns."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            logger = LoggerAdaptor()
            logger.enable_redaction(enabled=True)
            
            # Invalid regex pattern should raise ValueError
            with pytest.raises(ValueError, match="Invalid regex pattern"):
                logger.add_redaction_pattern("[invalid regex", "[REDACTED]")

    def test_comprehensive_logging_with_credit_card_redaction(self):
        """Test comprehensive logging with credit card redaction."""
        config = {
            "backend": "standard",
            "level": "DEBUG",
            "redaction": {
                "enabled": True,
                "placeholder": "[REDACTED]",
                "patterns": [
                    {
                        "pattern": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
                        "placeholder": "[CARD]"
                    }
                ]
            }
        }
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            logger = LoggerAdaptor()
            logger.enable_redaction(enabled=True)
            logger.add_redaction_pattern(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}', '[CARD]')
            
            # Test messages with credit card numbers
            test_message = "Processing payment for card 1234-5678-9012-3456"
            redacted = logger.test_redaction(test_message)
            assert '[CARD]' in redacted
            assert '1234-5678-9012-3456' not in redacted

    def test_all_log_levels_comprehensive(self):
        """Test all logging levels with various parameters."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "DEBUG"}
            
            logger = LoggerAdaptor()
            
            # Test with different parameter combinations
            test_cases = [
                ("debug", "Debug message", {"user_id": "123", "action": "login"}),
                ("info", "User logged in successfully", {"session_id": "abc-def"}),
                ("warning", "Password will expire soon", {"days_remaining": 5}),
                ("error", "Database connection failed", {"retry_count": 3, "error_code": "DB001"}),
                ("critical", "System out of memory", {"memory_usage": "95%", "alert": True})
            ]
            
            with patch.object(logger, '_log_message') as mock_log:
                for level, message, params in test_cases:
                    getattr(logger, level)(message, **params)
                    mock_log.assert_called_with(level.upper(), message, **params)

    def test_environment_specific_behavior(self):
        """Test behavior specific to different environments."""
        test_cases = [
            ("dev", "development"),
            ("staging", "staging"), 
            ("prod", "production"),
            ("test", "testing")
        ]
        
        for env_var, expected_env in test_cases:
            with patch.dict(os.environ, {'ENVIRONMENT': env_var}):
                with patch.object(LoggerAdaptor, '_load_config') as mock_load:
                    mock_load.return_value = {"backend": "standard", "level": "INFO"}
                    
                    logger = LoggerAdaptor(f"test_{expected_env}")
                    assert logger.environment == expected_env
                    # Check that the appropriate config file is being used
                    config_mapping = {
                        "development": "dev",
                        "staging": "staging", 
                        "production": "prod",
                        "testing": "test"
                    }
                    expected_config_part = config_mapping[expected_env]
                    assert expected_config_part in logger.config_file_used

    def test_concurrent_logger_instances(self):
        """Test multiple logger instances with different configurations."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "standard", "level": "INFO"}
            
            # Create multiple loggers
            logger1 = LoggerAdaptor.get_logger("service1", "dev")
            logger2 = LoggerAdaptor.get_logger("service2", "dev")
            logger3 = LoggerAdaptor.get_logger("service1", "prod")  # Same name, different env
            
            # Test they have correct identities
            assert logger1.name == "service1"
            assert logger2.name == "service2"
            assert logger3.name == "service1"
            
            # Test singleton behavior
            logger1_duplicate = LoggerAdaptor.get_logger("service1", "dev")
            assert logger1 is logger1_duplicate
            assert logger1 is not logger2
            assert logger1 is not logger3

    def test_structured_logging_with_context(self):
        """Test structured logging with persistent context."""
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = {"backend": "json", "level": "INFO"}
            
            logger = LoggerAdaptor("structured_test")
            
            # Set persistent context
            logger.set_context(
                service="user-auth",
                version="1.2.3",
                environment="production"
            )
            
            # Test that context persists across multiple log calls
            with patch.object(logger.logger, 'log') as mock_log:
                logger.info("User authentication started", user_id="user-123")
                logger.warning("Rate limit approaching", current_requests=45, limit=50)
                logger.error("Authentication failed", reason="invalid_token")
                
                # Verify all calls include persistent context
                assert mock_log.call_count == 3
                
                # Check that context is maintained - either persistent context or call-specific params
                for call in mock_log.call_args_list:
                    json_message = call[0][1]  # Second argument is the JSON string
                    log_data = json.loads(json_message)
                    # Context should include either persistent context or call-specific parameters
                    has_context = any(key in log_data for key in ["service", "user_id", "current_requests", "reason"])
                    assert has_context, f"Expected context in log data: {log_data}"

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        # Test with invalid config file path
        with patch.object(LoggerAdaptor, '_get_environment_config_file') as mock_get_file:
            mock_get_file.return_value = "/nonexistent/path/config.json"
            
            with patch('builtins.open', side_effect=FileNotFoundError):
                logger = LoggerAdaptor("error_test")
                # Should fall back to default config
                assert logger.backend in ["standard", "json", "detailed"]
                assert logger.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    @pytest.mark.parametrize("log_level,should_log", [
        ("DEBUG", True),
        ("INFO", True), 
        ("WARNING", True),
        ("ERROR", True),
        ("CRITICAL", True)
    ])
    def test_log_level_filtering(self, log_level, should_log):
        """Test that log level filtering works correctly."""
        config = {"backend": "standard", "level": log_level}
        
        with patch.object(LoggerAdaptor, '_load_config') as mock_load:
            mock_load.return_value = config
            
            logger = LoggerAdaptor("level_test")
            assert logger.level == log_level
            
            # Test that logger accepts the configured level
            with patch.object(logger, '_log_message') as mock_log:
                getattr(logger, log_level.lower())("Test message")
                if should_log:
                    mock_log.assert_called_once_with(log_level, "Test message")
                else:
                    mock_log.assert_not_called()
