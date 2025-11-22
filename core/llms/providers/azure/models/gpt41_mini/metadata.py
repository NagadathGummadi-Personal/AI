"""
Azure GPT-4.1 Mini Model Metadata.

Defines configuration, capabilities, and parameters for GPT-4.1 Mini.
"""

from typing import Dict, Any
from .....constants import (
    # Parameter names
    PARAM_MAX_TOKENS,
    PARAM_MAX_COMPLETION_TOKENS,
    PARAM_TEMPERATURE,
    PARAM_TOP_P,
    PARAM_FREQUENCY_PENALTY,
    PARAM_PRESENCE_PENALTY,
    PARAM_STOP,
    # Model names
    MODEL_NAME_AZURE_GPT_41_MINI,
    # Display names
    DISPLAY_NAME_AZURE_GPT_41_MINI,
    # Provider
    PROVIDER_AZURE,
)


class GPT41MiniMetadata:
    """
    Azure GPT-4.1 Mini model metadata and configuration.
    
    Key Features:
    - 128K context window
    - Multimodal input (text + images)
    - Multiple output formats (text, JSON, image, audio)
    - Function calling support
    - Vision capabilities
    - JSON mode
    - Fast and cost-effective
    
    Limitations:
    - Fixed temperature (1.0) - cannot be customized
    - No audio or video input support
    
    Cost (per 1K tokens):
    - Input: $0.00015
    - Output: $0.0006
    """
    
    # Model identification
    NAME = MODEL_NAME_AZURE_GPT_41_MINI
    DISPLAY_NAME = DISPLAY_NAME_AZURE_GPT_41_MINI
    PROVIDER = PROVIDER_AZURE
    
    # Capabilities
    MAX_TOKENS = 16384
    MAX_CONTEXT_LENGTH = 128000
    MAX_INPUT_TOKENS = 124000
    
    # Cost (USD per 1K tokens)
    COST_PER_1K_INPUT = 0.00015
    COST_PER_1K_OUTPUT = 0.0006
    
    # Features
    SUPPORTS_STREAMING = True
    SUPPORTS_FUNCTION_CALLING = True
    SUPPORTS_VISION = True
    SUPPORTS_JSON_MODE = True
    
    # Parameter configuration
    PARAMETER_MAPPINGS = {
        PARAM_MAX_TOKENS: PARAM_MAX_COMPLETION_TOKENS,
    }
    
    DEFAULT_PARAMETERS = {
        # Note: GPT-4.1 Mini only supports default temperature (1.0), don't set it
        PARAM_MAX_TOKENS: 4096,
        PARAM_TOP_P: 1.0,
        PARAM_FREQUENCY_PENALTY: 0.0,
        PARAM_PRESENCE_PENALTY: 0.0,
    }
    
    PARAMETER_RANGES = {
        PARAM_MAX_TOKENS: (1, 16384),
        PARAM_TOP_P: (0.0, 1.0),
        PARAM_FREQUENCY_PENALTY: (-2.0, 2.0),
        PARAM_PRESENCE_PENALTY: (-2.0, 2.0),
    }
    
    # GPT-4.1 Mini only supports these parameters
    # Note: temperature is NOT in supported list (uses default only)
    SUPPORTED_PARAMS = {
        PARAM_MAX_TOKENS,
        PARAM_TOP_P,
        PARAM_FREQUENCY_PENALTY,
        PARAM_PRESENCE_PENALTY,
        PARAM_STOP
    }
    
    @classmethod
    def validate_params(cls, params: Dict[str, Any]) -> None:
        """
        Validate parameters for GPT-4.1 Mini.
        
        Args:
            params: Parameters to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        for param_name in params:
            # Check if parameter is supported
            if param_name not in cls.SUPPORTED_PARAMS:
                # Special message for temperature since it's commonly used
                if param_name == PARAM_TEMPERATURE:
                    raise ValueError(
                        f"GPT-4.1 Mini does not support custom temperature parameter. "
                        f"It always uses temperature=1.0"
                    )
                raise ValueError(
                    f"Parameter '{param_name}' not supported by {cls.NAME}. "
                    f"Supported: {cls.SUPPORTED_PARAMS}"
                )
            
            # Check if parameter is in valid range
            if param_name in cls.PARAMETER_RANGES:
                param_value = params[param_name]
                min_val, max_val = cls.PARAMETER_RANGES[param_name]
                if not (min_val <= param_value <= max_val):
                    raise ValueError(
                        f"Parameter '{param_name}' value {param_value} out of range. "
                        f"Valid range: [{min_val}, {max_val}]"
                    )

