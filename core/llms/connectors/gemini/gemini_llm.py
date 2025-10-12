"""
Google Gemini LLM connector for the AI Agent SDK.
"""

import asyncio
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from core.llms.base_llm import BaseLLM
from core.llms.configs import GeminiConfig
from core.llms.constants import (
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ERROR_LLM,
    LOG_GEMINI_COMPLETED,
    LOG_GEMINI_FAILED,
    LOG_GEMINI_REQUEST,
    METRIC_LLM_REQUEST_STARTED,
    METRIC_LLM_REQUEST_SUCCESS,
    METRIC_LLM_REQUEST_FAILED,
    PROVIDER_GEMINI,
    ROLE_SYSTEM,
    ROLE_USER,
    ROLE_ASSISTANT,
    ROLE_FUNCTION,
    GEMINI_SAFETY_HARM_CATEGORY_HARASSMENT,
    GEMINI_SAFETY_HARM_CATEGORY_HATE_SPEECH,
    GEMINI_SAFETY_HARM_CATEGORY_SEXUALLY_EXPLICIT,
    GEMINI_SAFETY_HARM_CATEGORY_DANGEROUS_CONTENT,
    GEMINI_SAFETY_THRESHOLD_BLOCK_MEDIUM_AND_ABOVE,
)
from .converter import convert_to_gemini_request
from core.llms.enums import InputType, OutputMediaType
from core.llms.exceptions import InputValidationError, ProviderError, TimeoutError

# Optional imports for Google Gemini
try:
    import google.generativeai as genai
    from google.generativeai.types import RequestOptions
    from google.api_core.exceptions import GoogleAPIError, InvalidArgument
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    RequestOptions = None
    GoogleAPIError = Exception
    InvalidArgument = Exception


class GeminiLLM(BaseLLM):
    """
    Google Gemini LLM implementation.

    Supports text, image, and multimodal inputs with streaming.
    """

    def __init__(self, config: GeminiConfig):
        super().__init__(config)
        self.provider_name = PROVIDER_GEMINI

        # Check if google-generativeai library is available
        if not GENAI_AVAILABLE:
            raise ProviderError(
                "google-generativeai library is required for Gemini connector. "
                "Install it with: pip install google-generativeai"
            )

        # Initialize Gemini client
        try:
            genai.configure(api_key=config.api_key)
            self.client = genai.GenerativeModel(
                model_name=config.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.temperature,
                    max_output_tokens=config.max_tokens,
                    top_p=config.top_p,
                )
            )
        except Exception as e:
            raise ProviderError(f"Failed to initialize Gemini client: {e}")

        # Update supported capabilities based on model
        self._update_capabilities()

    def _update_capabilities(self):
        """Update capabilities based on model type"""
        model_name = self.config.model_name.lower()

        # Check for vision models (Gemini Pro Vision)
        if any(vision_model in model_name for vision_model in ["gemini-pro-vision", "gemini-1.5"]):
            self.config.supported_input_types.add(InputType.IMAGE)
            self.config.supported_output_types.add(OutputMediaType.IMAGE)

        # Check for multimodal models
        if "gemini-1.5" in model_name or "vision" in model_name:
            self.config.supported_input_types.add(InputType.MULTIMODAL)

    async def _get_answer_impl(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Get response from Google Gemini.

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
            }

            # Convert to Gemini specific format
            request_params = convert_to_gemini_request(
                messages, self.config.model_name, **request_kwargs
            )

            generation_config = request_params["generation_config"]
            safety_settings = request_params["safety_settings"]

            # Convert messages to Gemini format for the API call
            gemini_content = self._convert_messages(messages)

            # Make the API call
            start_time = time.time()
            response = self.client.generate_content(
                gemini_content,
                generation_config=generation_config,
                safety_settings=safety_settings,
                request_options=RequestOptions(timeout=self.config.timeout)
            )
            duration = time.time() - start_time

            # Extract response content
            if not response.text:
                raise ProviderError("No response text returned from Gemini")

            content = response.text

            # Track usage metrics (Gemini provides limited usage info)
            self._track_usage(response, duration)

            return content

        except GoogleAPIError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Gemini request timed out: {e}")
            elif "rate" in str(e).lower() or "quota" in str(e).lower():
                raise ProviderError(f"Gemini rate limit or quota exceeded: {e}")
            elif "blocked" in str(e).lower():
                raise ProviderError(f"Gemini content blocked: {e}")
            else:
                raise ProviderError(f"Gemini API error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError("Gemini request timed out")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Gemini request: {e}")

    async def _get_stream_impl(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """
        Get streaming response from Google Gemini.

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
            }

            # Convert to Gemini specific format for streaming
            request_params = convert_to_gemini_request(
                messages, self.config.model_name, **request_kwargs
            )

            generation_config = request_params["generation_config"]
            safety_settings = request_params["safety_settings"]

            # Convert messages to Gemini format for the API call
            gemini_content = self._convert_messages(messages)

            # Make the streaming API call
            start_time = time.time()
            response = self.client.generate_content(
                gemini_content,
                generation_config=generation_config,
                safety_settings=safety_settings,
                request_options=RequestOptions(timeout=self.config.timeout),
                stream=True
            )

            accumulated_content = ""
            for chunk in response:
                if chunk.text:
                    accumulated_content += chunk.text
                    yield chunk.text

            duration = time.time() - start_time

            # Track usage metrics
            self._track_usage(response, duration)

        except GoogleAPIError as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"Gemini streaming request timed out: {e}")
            elif "rate" in str(e).lower() or "quota" in str(e).lower():
                raise ProviderError(f"Gemini streaming rate limit or quota exceeded: {e}")
            else:
                raise ProviderError(f"Gemini streaming API error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Gemini streaming request: {e}")

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Convert internal message format to Gemini format.

        Args:
            messages: Internal message format

        Returns:
            Gemini-compatible content format
        """
        gemini_parts = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                # Gemini doesn't have system role, so prepend to first user message
                if gemini_parts and gemini_parts[0].startswith("User:"):
                    gemini_parts[0] = f"System: {content}\n\n{gemini_parts[0]}"
                else:
                    gemini_parts.insert(0, f"System: {content}\n\n")
            elif role == "user":
                gemini_parts.append(f"User: {content}")
            elif role == "assistant":
                gemini_parts.append(f"Assistant: {content}")
            elif role == "function":
                gemini_parts.append(f"Function: {content}")

        # Combine all parts into a single string for Gemini
        combined_content = "\n\n".join(gemini_parts)

        # For multimodal content, we would need to handle images differently
        # This is a simplified implementation
        return combined_content

    def _track_usage(self, response, duration: float):
        """Track usage metrics for monitoring"""
        # Gemini provides limited usage information
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                tokens_in = getattr(usage, 'prompt_token_count', 0)
                tokens_out = getattr(usage, 'candidates_token_count', 0)

                # Calculate approximate cost (simplified)
                cost_per_token_in = 0.00000125  # Approximate Gemini pricing
                cost_per_token_out = 0.000005   # Approximate Gemini pricing
                total_cost = (tokens_in * cost_per_token_in) + (tokens_out * cost_per_token_out)

                print(f"Gemini Usage - In: {tokens_in}, Out: {tokens_out}, Cost: ${total_cost:.6f}")

        except Exception:
            # If usage tracking fails, continue without error
            pass

    def validate_input(self, input_type: InputType, content: Any) -> bool:
        """Validate Gemini specific input"""
        # First do base validation
        super().validate_input(input_type, content)

        # Gemini specific validation
        if input_type == InputType.IMAGE:
            if isinstance(content, str):
                # Should be a URL or file path
                if not (content.startswith("http") or content.startswith("gs://")):
                    raise InputValidationError("Image must be a valid HTTP URL or Google Cloud Storage path")
            elif not isinstance(content, bytes):
                raise InputValidationError("Image content must be bytes or string (URL/GCS path)")

        return True
