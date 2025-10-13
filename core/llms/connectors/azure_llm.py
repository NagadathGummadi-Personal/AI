"""
Azure OpenAI LLM connector for the AI Agent SDK.
"""

import asyncio
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from ..base_llm import BaseLLM
from ..configs import AzureOpenAIConfig
from ..constants import (
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ERROR_LLM,
    LOG_AZURE_OPENAI_COMPLETED,
    LOG_AZURE_OPENAI_FAILED,
    LOG_AZURE_OPENAI_REQUEST,
    METRIC_LLM_REQUEST_STARTED,
    METRIC_LLM_REQUEST_SUCCESS,
    METRIC_LLM_REQUEST_FAILED,
    METRIC_LLM_TOKENS_IN,
    METRIC_LLM_TOKENS_OUT,
    METRIC_LLM_COST_USD,
    PROVIDER_AZURE_OPENAI,
    ROLE_SYSTEM,
    ROLE_USER,
    ROLE_ASSISTANT,
    ROLE_FUNCTION,
)
from ..enums import InputMediaType, OutputMediaType
from ..exceptions import InputValidationError, ProviderError, TimeoutError

# Optional imports for Azure OpenAI
try:
    from openai import AsyncAzureOpenAI, AzureOpenAIError
    from openai.types.chat import ChatCompletion, ChatCompletionChunk
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncAzureOpenAI = None
    AzureOpenAIError = Exception
    ChatCompletion = None
    ChatCompletionChunk = None


class AzureLLM(BaseLLM):
    """
    Azure OpenAI LLM implementation.

    Supports chat completions, streaming, and JSON mode.
    """

    def __init__(self, config: AzureOpenAIConfig):
        super().__init__(config)
        self.provider_name = PROVIDER_AZURE_OPENAI

        # Check if OpenAI library is available
        if not OPENAI_AVAILABLE:
            raise ProviderError(
                "OpenAI library is required for Azure OpenAI connector. "
                "Install it with: pip install openai"
            )

        # Initialize Azure OpenAI client
        try:
            self.client = AsyncAzureOpenAI(
                api_key=config.api_key,
                azure_endpoint=config.endpoint or f"https://{config.deployment_name}.openai.azure.com/",
                api_version=config.api_version,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        except Exception as e:
            raise ProviderError(f"Failed to initialize Azure OpenAI client: {e}")

        # Update supported capabilities based on model
        self._update_capabilities()

    def _update_capabilities(self):
        """Update capabilities based on model type"""
        model_name = self.config.model_name.lower()

        # Check for vision models (GPT-4v, GPT-4o)
        if any(vision_model in model_name for vision_model in ["gpt-4v", "gpt-4o", "vision"]):
            self.config.supported_input_types.add(InputMediaType.IMAGE)
            self.config.supported_output_types.add(OutputMediaType.IMAGE)

        # Check for multimodal models
        if "gpt-4o" in model_name or "vision" in model_name:
            self.config.supported_input_types.add(InputMediaType.MULTIMODAL)

    async def _get_answer_impl(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Get response from Azure OpenAI.

        Args:
            messages: Messages to send
            **kwargs: Additional parameters

        Returns:
            Response content as string
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            # Prepare request parameters
            request_params = {
                "model": self.config.deployment_name or self.config.model_name,
                "messages": openai_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "stop": self.config.stop_sequences or None,
                "stream": False,
            }

            # Add JSON mode if configured
            if self.config.json_output:
                request_params["response_format"] = {"type": "json_object"}

            # Add any additional kwargs
            request_params.update(kwargs)

            # Make the API call
            start_time = time.time()
            response: ChatCompletion = await self.client.chat.completions.create(**request_params)
            duration = time.time() - start_time

            # Extract response content
            if not response.choices:
                raise ProviderError("No response choices returned from Azure OpenAI")

            message = response.choices[0].message
            content = message.content or ""

            # Track usage metrics
            if response.usage:
                self._track_usage(response.usage, duration)

            return content

        except AzureOpenAIError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Azure OpenAI request timed out: {e}")
            elif "rate limit" in str(e).lower():
                raise ProviderError(f"Azure OpenAI rate limit exceeded: {e}")
            else:
                raise ProviderError(f"Azure OpenAI API error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError("Azure OpenAI request timed out")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Azure OpenAI request: {e}")

    async def _get_stream_impl(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """
        Get streaming response from Azure OpenAI.

        Args:
            messages: Messages to send
            **kwargs: Additional parameters

        Yields:
            Response content chunks
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)

            # Prepare request parameters for streaming
            request_params = {
                "model": self.config.deployment_name or self.config.model_name,
                "messages": openai_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "stop": self.config.stop_sequences or None,
                "stream": True,
            }

            # Add JSON mode if configured
            if self.config.json_output:
                request_params["response_format"] = {"type": "json_object"}

            # Add any additional kwargs
            request_params.update(kwargs)

            # Make the streaming API call
            start_time = time.time()
            stream = await self.client.chat.completions.create(**request_params)

            accumulated_content = ""
            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if delta.content:
                    accumulated_content += delta.content
                    yield delta.content

            duration = time.time() - start_time

            # Track usage metrics if available
            if hasattr(stream, 'response') and hasattr(stream.response, 'usage'):
                self._track_usage(stream.response.usage, duration)

        except AzureOpenAIError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Azure OpenAI streaming request timed out: {e}")
            elif "rate limit" in str(e).lower():
                raise ProviderError(f"Azure OpenAI rate limit exceeded: {e}")
            else:
                raise ProviderError(f"Azure OpenAI streaming API error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError("Azure OpenAI streaming request timed out")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Azure OpenAI streaming request: {e}")

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert internal message format to OpenAI format.

        Args:
            messages: Internal message format

        Returns:
            OpenAI-compatible message format
        """
        openai_messages = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Map internal roles to OpenAI roles
            if role == "system":
                openai_role = "system"
            elif role == "user":
                openai_role = "user"
            elif role == "assistant":
                openai_role = "assistant"
            elif role == "function":
                openai_role = "function"
            else:
                openai_role = "user"  # Default fallback

            openai_messages.append({
                "role": openai_role,
                "content": content
            })

        return openai_messages

    def _track_usage(self, usage, duration: float):
        """Track usage metrics for monitoring"""
        # This would typically integrate with your metrics system
        # For now, just log the usage
        if usage:
            tokens_in = getattr(usage, 'prompt_tokens', 0)
            tokens_out = getattr(usage, 'completion_tokens', 0)

            # Calculate approximate cost (this is a simplified calculation)
            # In practice, you'd use the actual pricing for the specific model
            cost_per_token_in = 0.00003  # Approximate cost per input token
            cost_per_token_out = 0.00006  # Approximate cost per output token
            total_cost = (tokens_in * cost_per_token_in) + (tokens_out * cost_per_token_out)

            # Log metrics (in a real implementation, use your metrics system)
            print(f"Azure OpenAI Usage - In: {tokens_in}, Out: {tokens_out}, Cost: ${total_cost:.6f}")

    def validate_input(self, input_type: InputMediaType, content: Any) -> bool:
        """Validate Azure OpenAI specific input"""
        # First do base validation
        super().validate_input(input_type, content)

        # Azure OpenAI specific validation
        if input_type == InputMediaType.IMAGE:
            if isinstance(content, str):
                # Should be a URL or file path
                if not (content.startswith("http") or content.endswith((".jpg", ".jpeg", ".png", ".gif"))):
                    raise InputValidationError("Image must be a valid URL or file path")
            elif not isinstance(content, bytes):
                raise InputValidationError("Image content must be bytes or string (URL/path)")

        return True
