import json
import os
import re
import logging
import logging.handlers
from pathlib import Path
from typing import Any
from datetime import datetime
from utils.logging.RedactionManager import RedactionManager
from utils.logging.Enum import LoggingFormat, Environment, RedactionConfig


class LoggerAdaptor:
    """
    Unified Logger Adaptor that provides a consistent interface across different logging mechanisms.

    This adaptor reads configuration and adapts its behavior based on the config.
    All configuration is controlled via environment-based configuration files.
    """

    _instances = {}
    _config = None

    def __init__(self, name: str = "default", environment: str = None):
        # Always detect environment first, default to 'prod' if not provided
        self.environment = (environment or self._detect_environment()).lower()
        self.name = name

        # Select config file based on environment
        self.config_file = self._get_environment_config_file(self.environment)
        self.logger = None
        self.redaction_manager = None
        self.context = {}  # For structured logging context

        # Load configuration if not already loaded or if config file changed
        if LoggerAdaptor._config is None or getattr(
                self, '_last_config_file', None) != self.config_file:
            LoggerAdaptor._config = self._load_config(self.config_file)
            self._last_config_file = self.config_file

        # Initialize logger
        self._initialize_logger()

    @classmethod
    def get_logger(
            cls,
            name: str = "default",
            environment: str = None) -> 'LoggerAdaptor':
        """
        Get or create a logger instance (singleton pattern per name/environment).
        """
        env = (environment or cls._detect_environment_static()).lower()
        instance_key = f"{name}_{env}"
        if instance_key not in cls._instances:
            cls._instances[instance_key] = cls(name, environment)
        return cls._instances[instance_key]

    @staticmethod
    def _detect_environment_static() -> str:
        """Static method to detect environment for class method. Defaults to 'prod' if not set."""
        env = os.getenv('ENVIRONMENT', os.getenv('ENV', 'prod')).lower()
        env_mapping = {
            'dev': Environment.DEVELOPMENT.value,
            'development': Environment.DEVELOPMENT.value,
            'stage': Environment.STAGING.value,
            'staging': Environment.STAGING.value,
            'prod': Environment.PRODUCTION.value,
            'production': Environment.PRODUCTION.value,
            'test': Environment.TESTING.value,
            'testing': Environment.TESTING.value
        }
        return env_mapping.get(env, Environment.PRODUCTION.value)

    def _detect_environment(self) -> str:
        """Detect current environment from env variables.

        Defaults to 'prod' if not set.
        """
        env = os.getenv('ENVIRONMENT', os.getenv('ENV', 'prod')).lower()
        env_mapping = {
            'dev': Environment.DEVELOPMENT.value,
            'development': Environment.DEVELOPMENT.value,
            'stage': Environment.STAGING.value,
            'staging': Environment.STAGING.value,
            'prod': Environment.PRODUCTION.value,
            'production': Environment.PRODUCTION.value,
            'test': Environment.TESTING.value,
            'testing': Environment.TESTING.value
        }
        return env_mapping.get(env, Environment.PRODUCTION.value)

    def _get_environment_config_file(self, environment: str) -> str:
        """Get configuration file based on environment."""
        config_dir = "Utils/Logging/Config"
        config_files = {
            Environment.DEVELOPMENT.value: f"{config_dir}/log_config_dev.json",
            Environment.STAGING.value: f"{config_dir}/log_config_staging.json",
            Environment.PRODUCTION.value: f"{config_dir}/log_config_prod.json",
            Environment.TESTING.value: f"{config_dir}/log_config_test.json"
        }
        config_file = config_files.get(
            environment, f"{config_dir}/log_config_prod.json")

        # Check if environment-specific config exists, otherwise use prod
        if not os.path.exists(config_file):
            config_file = f"{config_dir}/log_config_prod.json"
        return config_file

    def _load_config(self, config_file: str) -> dict[str, Any]:
        """Load logging configuration from file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # Return default configuration if file not found
            return self._get_default_config()
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in configuration file {config_file}: {e}"
            raise ValueError(msg) from e

    def _get_default_config(self) -> dict[str, Any]:
        """Get default logging configuration."""
        return {
            "backend": "standard",
            "level": "INFO",
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"}},
            "handlers": {
                "console": {
                    "type": "console",
                    "level": "INFO",
                    "formatter": "default"}}}

    def _initialize_logger(self):
        """Initialize the logger based on configuration."""
        config = LoggerAdaptor._config
        self.backend = config.get('backend', 'json').lower()

        # Initialize redaction if configured
        redaction_config = config.get('redaction', {})
        if redaction_config.get(RedactionConfig.ENABLED.value, False):
            self.redaction_manager = RedactionManager(redaction_config)

        # Create the underlying logger
        self.logger = logging.getLogger(self.name)
        self._configure_logger(config)

    def _configure_logger(self, config: dict[str, Any]):
        """Configure the logger based on configuration."""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Set log level
        level_str = config.get('level', 'INFO').upper()
        self.logger.setLevel(getattr(logging, level_str))

        # Create formatters
        formatters = self._create_formatters(config.get('formatters', {}))

        # Create handlers
        handlers_config = config.get('handlers', {})
        for handler_config in handlers_config.values():
            handler = self._create_handler(handler_config, formatters)
            if handler:
                self.logger.addHandler(handler)

    def _create_formatters(self,
                           formatters_config: dict[str,
                                                   Any]) -> dict[str,
                                                                 logging.Formatter]:
        """Create formatters from configuration."""
        formatters = {}
        for name, format_config in formatters_config.items():
            format_string = format_config.get(
                'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            date_format = format_config.get('datefmt')
            formatters[name] = logging.Formatter(format_string, date_format)
        return formatters

    def _create_handler(
        self,
        handler_config: dict[str, Any],
        formatters: dict[str, logging.Formatter],
    ) -> logging.Handler | None:
        """Create a handler from configuration."""
        handler_type = handler_config.get('type')
        formatter_name = handler_config.get('formatter', 'default')
        level_str = handler_config.get('level', 'INFO').upper()

        handler = None

        if handler_type == 'console':
            handler = logging.StreamHandler()
        elif handler_type == 'file':
            filename = handler_config.get('filename', 'app.log')
            filepath = self._get_log_filepath(filename)
            handler = logging.FileHandler(filepath)
        elif handler_type == 'rotating_file':
            filename = handler_config.get('filename', 'app.log')
            filepath = self._get_log_filepath(filename)
            max_bytes = handler_config.get('max_bytes', 10485760)  # 10MB
            backup_count = handler_config.get('backup_count', 5)
            handler = logging.handlers.RotatingFileHandler(
                filepath, maxBytes=max_bytes, backupCount=backup_count)
        elif handler_type == 'timed_rotating_file':
            filename = handler_config.get('filename', 'app.log')
            filepath = self._get_log_filepath(filename)
            when = handler_config.get('when', 'midnight')
            interval = handler_config.get('interval', 1)
            backup_count = handler_config.get('backup_count', 7)
            handler = logging.handlers.TimedRotatingFileHandler(
                filepath, when=when, interval=interval, backupCount=backup_count)

        if handler:
            handler.setLevel(getattr(logging, level_str))
            # Apply formatters if specified in config
            if formatter_name in formatters:
                handler.setFormatter(formatters[formatter_name])

        return handler

    def _get_log_filepath(self, filename: str) -> str:
        """Get the full filepath for log files based on configuration."""

        # Get log directory from config, default to ./logs
        config = LoggerAdaptor._config
        log_directory = config.get('log_directory', './logs')

        # Handle different path types
        if log_directory.startswith('~/'):
            # Expand ~ to user's home directory
            home_dir = Path.home()
            log_dir = home_dir / log_directory[2:]  # Remove ~/
        elif log_directory.startswith('./'):
            # Relative to current working directory
            log_dir = Path.cwd() / log_directory[2:]  # Remove ./
        else:
            # Absolute path or relative path
            log_dir = Path(log_directory)

        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        return str(log_dir / filename)

    def _format_message(self, *args, **_kwargs) -> str:
        """Format message from multiple arguments."""
        if not args:
            return ""

        # If only one argument and it's a string, use it as the message
        if len(args) == 1 and isinstance(args[0], str):
            message = args[0]
        else:
            # Format multiple arguments similar to print()
            message = " ".join(str(arg) for arg in args)

        return message

    def _redact_if_enabled(self, message: str, **
                           kwargs) -> tuple[str, dict[str, Any]]:
        """Apply redaction if enabled."""
        if self.redaction_manager:
            redacted_message = self.redaction_manager.redact_message(message)
            redacted_kwargs = self.redaction_manager.redact_data(kwargs)
            return redacted_message, redacted_kwargs
        return message, kwargs

    def _log_message(self, level: str, *args, **kwargs):
        """Log message based on backend type."""
        message = self._format_message(*args)
        redacted_message, redacted_kwargs = self._redact_if_enabled(
            message, **kwargs)

        if self.backend == LoggingFormat.JSON.value:
            self._log_json(level, redacted_message, **redacted_kwargs)
        elif self.backend == LoggingFormat.DETAILED.value:
            self._log_detailed(level, redacted_message, **redacted_kwargs)
        else:  # Standard logging
            self._log_standard(level, redacted_message, **redacted_kwargs)

    def _log_standard(self, level: str, message: str, **kwargs):
        """Log using standard Python logging."""
        if kwargs:
            # Include extra parameters in the message for standard logging
            extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} [{extra_info}]"
        else:
            full_message = message

        getattr(self.logger, level.lower())(full_message)

    def _log_json(self, level: str, message: str, **kwargs):
        """Log as JSON format."""
        # Check if formatters are defined in config
        config = LoggerAdaptor._config
        has_formatters = False
        if config is not None and isinstance(config, dict):
            # pylint: disable=unsupported-membership-test
            has_formatters = (
                'formatters' in config and
                config.get('formatters')
            )

        if has_formatters:
            # If formatters are specified, create JSON based on formatter
            # pattern
            formatters = config.get('formatters', {})
            default_formatter = formatters.get('default', {})
            format_pattern = default_formatter.get('format', '')

            # Build JSON data based on formatter pattern
            log_data = {}

            # Check which fields are in the format pattern
            if '%(asctime)s' in format_pattern:
                log_data['timestamp'] = datetime.utcnow().strftime(
                    default_formatter.get('datefmt', '%Y-%m-%d %H:%M:%S')
                )
            if '%(message)s' in format_pattern:
                log_data['message'] = message
            if '%(levelname)s' in format_pattern:
                log_data['level'] = level.upper()
            if '%(name)s' in format_pattern:
                log_data['logger'] = self.name

            # Add any kwargs if they're not already in the formatter
            for key, value in kwargs.items():
                if key not in log_data:
                    log_data[key] = value

            self.logger.log(
                getattr(
                    logging,
                    level.upper()),
                json.dumps(log_data))
        else:
            # No formatters specified, use default JSON structure
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': level.upper(),
                'logger': self.name,
                'message': message,
                **kwargs
            }
            self.logger.log(
                getattr(
                    logging,
                    level.upper()),
                json.dumps(log_data))

    def _log_detailed(self, level: str, message: str, **kwargs):
        """Log with detailed context as formatted text."""
        # Format the main message
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level_str = level.upper()
        logger_name = self.name

        # Build the detailed message
        detailed_message = f"[{timestamp}] {level_str} [{logger_name}] {message}"

        # Add context information if available
        if self.context or kwargs:
            context_parts = []

            # Add persistent context
            if self.context:
                context_parts.extend(
                    [f"{k}={v}" for k, v in self.context.items()])

            # Add immediate context (kwargs)
            if kwargs:
                context_parts.extend([f"{k}={v}" for k, v in kwargs.items()])

            if context_parts:
                detailed_message += f" | Context: {', '.join(context_parts)}"

        # Use the detailed message and let formatters handle it if configured
        self.logger.log(getattr(logging, level.upper()), detailed_message)

    def debug(self, *args, **kwargs):
        """Log debug message."""
        self._log_message('DEBUG', *args, **kwargs)

    def info(self, *args, **kwargs):
        """Log info message."""
        self._log_message('INFO', *args, **kwargs)

    def warning(self, *args, **kwargs):
        """Log warning message."""
        self._log_message('WARNING', *args, **kwargs)

    def error(self, *args, **kwargs):
        """Log error message."""
        self._log_message('ERROR', *args, **kwargs)

    def critical(self, *args, **kwargs):
        """Log critical message."""
        self._log_message('CRITICAL', *args, **kwargs)

    def set_context(self, **kwargs):
        """Set persistent context for structured logging."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear all persistent context."""
        self.context.clear()

    def reload_config(self, config_file: str = None):
        """Reload configuration and reinitialize logger."""
        if config_file:
            self.config_file = config_file

        LoggerAdaptor._config = self._load_config(self.config_file)
        self._initialize_logger()

    @property
    def level(self) -> str:
        """Get current log level."""
        return LoggerAdaptor._config.get("level", "INFO")

    @property
    def current_environment(self) -> str:
        """Get current environment."""
        return self.environment

    @property
    def config_file_used(self) -> str:
        """Get the config file actually used."""
        return self.config_file

    def add_redaction_pattern(
        self,
        pattern: str,
        placeholder: str = "[REDACTED]",
        flags: list[str] | None = None,
    ) -> None:
        """Add a new redaction pattern to the logger."""
        if self.redaction_manager:
            flags = flags or []

            # Compile and add the pattern
            regex_flags = self.redaction_manager._get_regex_flags(flags)
            try:
                compiled_pattern = re.compile(pattern, regex_flags)
                self.redaction_manager.redaction_patterns.append(
                    (compiled_pattern, placeholder)
                )
            except re.error as e:
                msg = f"Invalid regex pattern '{pattern}': {e}"
                raise ValueError(msg) from e

    def enable_redaction(self, *, enabled: bool = True) -> None:
        """Enable or disable redaction for this logger."""
        if enabled and not self.redaction_manager:
            # Create redaction manager with default config
            redaction_config = {
                "enabled": True,
                "placeholder": "[REDACTED]",
                "patterns": [],
            }
            self.redaction_manager = RedactionManager(redaction_config)
        elif not enabled and self.redaction_manager:
            self.redaction_manager = None

    def test_redaction(self, message: str) -> str:
        """Test redaction on a message without logging it."""
        if self.redaction_manager:
            return self.redaction_manager.redact_message(message)
        return message

    def has_redaction(self) -> bool:
        """Check if redaction is enabled and available."""
        return self.redaction_manager is not None
