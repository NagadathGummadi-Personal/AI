import sys
sys.path.append('d:/AI')
from utils.logging.LoggerAdaptor import LoggerAdaptor
from unittest.mock import patch

# Mock configuration (same as TestConstants.MOCK_CONFIG)
MOCK_CONFIG = {
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

print('MOCK_CONFIG:', MOCK_CONFIG)
print()

with patch.object(LoggerAdaptor, '_load_config') as mock_load:
    mock_load.return_value = MOCK_CONFIG

    logger = LoggerAdaptor()
    print('Redaction manager:', logger.redaction_manager)
    print('Has redaction:', logger.has_redaction())
