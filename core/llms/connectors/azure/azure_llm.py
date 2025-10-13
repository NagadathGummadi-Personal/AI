"""
Azure OpenAI LLM connector for the AI Agent SDK.
"""

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List

from core.llms.base_llm import BaseLLM
from core.llms.configs import AzureOpenAIConfig
from core.llms.constants import (
    PROVIDER_AZURE_OPENAI,
)
from .converter import convert_to_azure_openai_request
from core.llms.enums import InputMediaType, OutputMediaType
from core.llms.exceptions import InputValidationError, ProviderError, TimeoutError

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
            # Prepare unified request parameters
            request_kwargs = {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "json_mode": self.config.json_output,
                "streaming": False,
            }

            if self.config.stop_sequences:
                request_kwargs["stop_sequences"] = self.config.stop_sequences

            # Add any additional kwargs
            request_kwargs.update(kwargs)

            # Convert to Azure OpenAI specific format
            request_params = convert_to_azure_openai_request(
                messages, self.config.model_name, **request_kwargs
            )
            
            # Add tools if registered and supported
            if self._available_tools and self.model_capabilities.supports_function_calling:
                request_params["tools"] = list(self._available_tools.values())
                request_params["tool_choice"] = kwargs.get("tool_choice", "auto")

            # Make the API call
            start_time = time.time()
            response: ChatCompletion = await self.client.chat.completions.create(**request_params)
            duration = time.time() - start_time

            # Extract response content
            if not response.choices:
                raise ProviderError("No response choices returned from Azure OpenAI")

            message = response.choices[0].message
            
            # Check if the model wants to call tools
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Handle tool calls
                tool_results = []
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    try:
                        result = await self.execute_tool(tool_name, tool_args)
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_name,
                            "content": str(result)
                        })
                    except Exception as e:
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_name,
                            "content": f"Error: {str(e)}"
                        })
                
                # If tools were called, make another request with the results
                if tool_results:
                    # Add the assistant's message with tool calls
                    new_messages = messages + [{
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    }]
                    
                    # Add tool results
                    new_messages.extend(tool_results)
                    
                    # Make follow-up request
                    return await self._get_answer_impl(new_messages, **kwargs)
            
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
            # Prepare unified request parameters for streaming
            request_kwargs = {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "json_mode": self.config.json_output,
                "streaming": True,
            }

            if self.config.stop_sequences:
                request_kwargs["stop_sequences"] = self.config.stop_sequences

            # Add any additional kwargs
            request_kwargs.update(kwargs)

            # Convert to Azure OpenAI specific format for streaming
            request_params = convert_to_azure_openai_request(
                messages, self.config.model_name, **request_kwargs
            )

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
