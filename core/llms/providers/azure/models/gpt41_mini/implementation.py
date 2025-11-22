"""
Azure GPT-4.1 Mini LLM Implementation.

Model-specific implementation with custom parameter transformation.
"""

from typing import Dict, Any, List
from ...base_implementation import AzureBaseLLM
from .metadata import GPT41MiniMetadata
from .....constants import (
    PARAM_MAX_TOKENS,
    PARAM_MAX_COMPLETION_TOKENS,
    PARAM_TEMPERATURE,
)
from utils.logging.LoggerAdaptor import LoggerAdaptor


class GPT41MiniLLM(AzureBaseLLM):
    """
    GPT-4.1 Mini specific LLM implementation.
    
    Extends AzureBaseLLM with GPT-4.1 Mini specific behavior:
    - Parameter transformation (max_tokens → max_completion_tokens)
    - Temperature removal (not supported)
    - Vision-specific methods
    
    Most functionality is inherited from AzureBaseLLM.
    Only overrides methods that need model-specific behavior.
    """
    
    def __init__(self, connector, metadata=None):
        """
        Initialize GPT-4.1 Mini LLM.
        
        Args:
            connector: AzureConnector instance
            metadata: GPT41MiniMetadata (optional, defaults to class metadata)
        """
        if metadata is None:
            metadata = GPT41MiniMetadata
        super().__init__(metadata=metadata, connector=connector)
        self.logger = LoggerAdaptor.get_logger(f"llm.{GPT41MiniMetadata.NAME}")
    
    def _transform_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform parameters for GPT-4.1 Mini.
        
        Key transformations:
        1. max_tokens → max_completion_tokens (GPT-4.1 specific)
        2. Remove temperature (not supported)
        
        Args:
            params: Raw parameters
            
        Returns:
            Transformed parameters
        """
        transformed = params.copy()
        
        # Transform max_tokens to max_completion_tokens
        if PARAM_MAX_TOKENS in transformed:
            transformed[PARAM_MAX_COMPLETION_TOKENS] = transformed.pop(PARAM_MAX_TOKENS)
            self.logger.debug(
                "Transformed max_tokens to max_completion_tokens",
                value=transformed[PARAM_MAX_COMPLETION_TOKENS]
            )
        
        # Remove temperature if present (GPT-4.1 Mini doesn't support it)
        if PARAM_TEMPERATURE in transformed:
            self.logger.warning(
                "Temperature parameter ignored for GPT-4.1 Mini (uses default 1.0)",
                requested_temperature=transformed[PARAM_TEMPERATURE]
            )
            del transformed[PARAM_TEMPERATURE]
        
        return transformed
    
    async def generate_with_vision(
        self,
        prompt: str,
        images: List[str],
        context,
        **kwargs
    ) -> str:
        """
        Generate response with vision (images).
        
        GPT-4.1 Mini specific method for multimodal input.
        
        Args:
            prompt: Text prompt
            images: List of image URLs or base64 encoded images
            context: LLM context
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
            
        Example:
            response = await llm.generate_with_vision(
                "What's in this image?",
                images=["https://example.com/image.jpg"],
                context=ctx,
                max_tokens=500
            )
        """
        # Build multimodal message
        content = [
            {"type": "text", "text": prompt},
        ]
        
        # Add images
        for image in images:
            content.append({
                "type": "image_url",
                "image_url": {"url": image}
            })
        
        messages = [{"role": "user", "content": content}]
        
        # Use base class's get_answer with transformed messages
        response = await self.get_answer(messages, context, **kwargs)
        return response.content

