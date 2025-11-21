"""
LLM Type Specifications.

This module defines the metadata schema for LLM models, including
capabilities, parameters, and provider-specific configuration.
"""

from typing import Dict, Any, Optional, Set, Callable
from pydantic import BaseModel, Field
from ..enum import (
    LLMProvider,
    ModelFamily,
    InputMediaType,
    OutputMediaType,
    LLMCapability,
    LLMType
)


class ModelMetadata(BaseModel):
    """
    Complete metadata specification for an LLM model.
    
    This is the core configuration object that defines everything about
    a model: capabilities, limits, parameters, costs, etc.
    
    Attributes:
        model_name: Unique model identifier
        provider: Provider hosting the model
        model_family: Model family grouping
        display_name: Human-readable name
        llm_type: Type of LLM (chat, completion, etc.)
        supported_input_types: Input media types supported
        supported_output_types: Output media types supported
        supports_streaming: Whether streaming is supported
        supports_function_calling: Whether function calling is supported
        supports_vision: Whether vision/image inputs are supported
        supports_json_mode: Whether JSON mode is supported
        max_context_length: Maximum context window in tokens
        max_output_tokens: Maximum output tokens
        max_input_tokens: Maximum input tokens
        parameter_mappings: Maps standard params to provider params
        default_parameters: Default parameter values
        api_requirements: Provider-specific API requirements
        converter_fn: Optional function to convert responses
        cost_per_1k_input_tokens: Cost per 1000 input tokens (USD)
        cost_per_1k_output_tokens: Cost per 1000 output tokens (USD)
        is_deprecated: Whether model is deprecated
        deprecation_date: When model was/will be deprecated
        replacement_model: Recommended replacement model
        
    Example:
        metadata = ModelMetadata(
            model_name="gpt-4-turbo",
            provider=LLMProvider.OPENAI,
            model_family=ModelFamily.GPT_4_TURBO,
            display_name="GPT-4 Turbo",
            supported_input_types={InputMediaType.TEXT, InputMediaType.IMAGE},
            supported_output_types={OutputMediaType.TEXT, OutputMediaType.JSON},
            supports_streaming=True,
            max_context_length=128000,
            max_output_tokens=4096
        )
    """
    
    # Core identification
    model_name: str = Field(description="Unique model identifier")
    provider: LLMProvider = Field(description="Provider hosting the model")
    model_family: ModelFamily = Field(description="Model family grouping")
    display_name: str = Field(description="Human-readable name")
    llm_type: LLMType = Field(default=LLMType.CHAT, description="Type of LLM")
    
    # Capabilities
    supported_input_types: Set[InputMediaType] = Field(
        default_factory=lambda: {InputMediaType.TEXT},
        description="Input media types supported"
    )
    supported_output_types: Set[OutputMediaType] = Field(
        default_factory=lambda: {OutputMediaType.TEXT},
        description="Output media types supported"
    )
    supports_streaming: bool = Field(default=False, description="Streaming support")
    supports_function_calling: bool = Field(default=False, description="Function calling support")
    supports_vision: bool = Field(default=False, description="Vision/image support")
    supports_json_mode: bool = Field(default=False, description="JSON mode support")
    
    # Limits
    max_context_length: int = Field(default=8192, ge=1, description="Maximum context window in tokens")
    max_output_tokens: int = Field(default=4096, ge=1, description="Maximum output tokens")
    max_input_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum input tokens")
    
    # Parameters
    parameter_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps standard parameter names to provider-specific names"
    )
    default_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default parameter values"
    )
    
    # Provider-specific
    api_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific API requirements"
    )
    converter_fn: Optional[str] = Field(
        default=None,
        description="Optional function name to convert responses"
    )
    
    # Pricing
    cost_per_1k_input_tokens: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost per 1000 input tokens in USD"
    )
    cost_per_1k_output_tokens: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost per 1000 output tokens in USD"
    )
    
    # Lifecycle
    is_deprecated: bool = Field(default=False, description="Whether model is deprecated")
    deprecation_date: Optional[str] = Field(default=None, description="Deprecation date (ISO format)")
    replacement_model: Optional[str] = Field(default=None, description="Recommended replacement")
    
    model_config = {
        "arbitrary_types_allowed": True,
        "use_enum_values": True,
        "json_schema_extra": {
            "examples": [
                {
                    "model_name": "gpt-4-turbo",
                    "provider": "openai",
                    "model_family": "gpt-4-turbo",
                    "display_name": "GPT-4 Turbo",
                    "supported_input_types": ["text", "image"],
                    "supported_output_types": ["text", "json"],
                    "supports_streaming": True,
                    "supports_function_calling": True,
                    "supports_vision": True,
                    "supports_json_mode": True,
                    "max_context_length": 128000,
                    "max_output_tokens": 4096,
                    "cost_per_1k_input_tokens": 0.01,
                    "cost_per_1k_output_tokens": 0.03
                }
            ]
        }
    }
    
    def supports_capability(self, capability: LLMCapability) -> bool:
        """
        Check if model supports a specific capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if capability is supported
        """
        capability_map = {
            LLMCapability.STREAMING: self.supports_streaming,
            LLMCapability.FUNCTION_CALLING: self.supports_function_calling,
            LLMCapability.VISION: self.supports_vision,
            LLMCapability.JSON_MODE: self.supports_json_mode,
        }
        return capability_map.get(capability, False)
    
    def supports_input_type(self, input_type: InputMediaType) -> bool:
        """
        Check if model supports an input type.
        
        Args:
            input_type: Input media type to check
            
        Returns:
            True if input type is supported
        """
        return input_type in self.supported_input_types
    
    def supports_output_type(self, output_type: OutputMediaType) -> bool:
        """
        Check if model supports an output type.
        
        Args:
            output_type: Output media type to check
            
        Returns:
            True if output type is supported
        """
        return output_type in self.supported_output_types
    
    def get_parameter_mapping(self, standard_param: str) -> str:
        """
        Get provider-specific parameter name.
        
        Args:
            standard_param: Standard parameter name
            
        Returns:
            Provider-specific parameter name (or original if no mapping)
        """
        return self.parameter_mappings.get(standard_param, standard_param)
    
    def get_default_parameter(self, param: str, default: Any = None) -> Any:
        """
        Get default value for a parameter.
        
        Args:
            param: Parameter name
            default: Fallback default
            
        Returns:
            Default parameter value
        """
        return self.default_parameters.get(param, default)
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        """
        Estimate cost for token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD, or None if pricing not available
        """
        if self.cost_per_1k_input_tokens is None or self.cost_per_1k_output_tokens is None:
            return None
        
        input_cost = (prompt_tokens / 1000) * self.cost_per_1k_input_tokens
        output_cost = (completion_tokens / 1000) * self.cost_per_1k_output_tokens
        return input_cost + output_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata to dictionary.
        
        Returns:
            Dictionary representation
        """
        return self.model_dump(exclude_none=True)


# Helper function to create model metadata

def create_model_metadata(
    model_name: str,
    provider: LLMProvider,
    model_family: ModelFamily,
    display_name: str,
    **kwargs
) -> ModelMetadata:
    """
    Helper to create ModelMetadata with required fields.
    
    Args:
        model_name: Model identifier
        provider: Provider
        model_family: Model family
        display_name: Display name
        **kwargs: Additional metadata fields
        
    Returns:
        ModelMetadata instance
    """
    return ModelMetadata(
        model_name=model_name,
        provider=provider,
        model_family=model_family,
        display_name=display_name,
        **kwargs
    )

