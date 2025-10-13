"""
Amazon Bedrock LLM connector for the AI Agent SDK.
"""

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from core.llms.base_llm import BaseLLM
from core.llms.configs import BedrockConfig
from core.llms.constants import (
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ERROR_LLM,
    LOG_BEDROCK_COMPLETED,
    LOG_BEDROCK_FAILED,
    LOG_BEDROCK_REQUEST,
    METRIC_LLM_REQUEST_STARTED,
    METRIC_LLM_REQUEST_SUCCESS,
    METRIC_LLM_REQUEST_FAILED,
    PROVIDER_BEDROCK,
    ROLE_SYSTEM,
    ROLE_USER,
    ROLE_ASSISTANT,
    ROLE_FUNCTION,
)
from .converter import convert_to_bedrock_request
from core.llms.enums import InputMediaType, OutputMediaType
from core.llms.exceptions import InputValidationError, ProviderError, TimeoutError

# Optional imports for AWS Bedrock
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception


class BedrockLLM(BaseLLM):
    """
    Amazon Bedrock LLM implementation.

    Supports various models including Claude, Jurassic, and others.
    """

    def __init__(self, config: BedrockConfig):
        super().__init__(config)
        self.provider_name = PROVIDER_BEDROCK

        # Check if boto3 library is available
        if not BOTO3_AVAILABLE:
            raise ProviderError(
                "boto3 library is required for Bedrock connector. "
                "Install it with: pip install boto3"
            )

        # Initialize Bedrock client
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=config.region,
                aws_access_key_id=config.api_key if config.api_key != "bedrock" else None,
                aws_secret_access_key=getattr(config, 'api_secret', None),
            )
        except NoCredentialsError:
            raise ProviderError("AWS credentials not found for Bedrock")
        except Exception as e:
            raise ProviderError(f"Failed to initialize Bedrock client: {e}")

        # Update supported capabilities based on model
        self._update_capabilities()

    def _update_capabilities(self):
        """Update capabilities based on model type"""
        model_name = self.config.model_name.lower()

        # Check for vision models (Claude 3)
        if any(vision_model in model_name for vision_model in ["claude-3", "vision"]):
            self.config.supported_input_types.add(InputMediaType.IMAGE)
            self.config.supported_output_types.add(OutputMediaType.IMAGE)

        # Check for multimodal models
        if "claude-3" in model_name:
            self.config.supported_input_types.add(InputMediaType.MULTIMODAL)

    async def _get_answer_impl(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Get response from Amazon Bedrock.

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
                "json_mode": self.config.json_output,
            }

            if self.config.stop_sequences:
                request_kwargs["stop_sequences"] = self.config.stop_sequences

            # Convert to Bedrock specific format
            request_body = convert_to_bedrock_request(
                messages, self.config.model_name, **request_kwargs
            )

            model_id = self.config.model_id or self.config.model_name

            # Make the API call
            start_time = time.time()
            response = self.client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body).encode('utf-8')
            )
            duration = time.time() - start_time

            # Parse response
            response_body = json.loads(response['body'].read())

            # Extract content based on model type
            content = self._extract_response_content(response_body)

            # Track usage metrics (Bedrock doesn't always provide usage info)
            self._track_usage(response_body, duration)

            return content

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ThrottlingException':
                raise ProviderError(f"Bedrock rate limit exceeded: {e}")
            elif error_code == 'ServiceUnavailableException':
                raise ProviderError(f"Bedrock service unavailable: {e}")
            elif error_code == 'ValidationException':
                raise ProviderError(f"Bedrock validation error: {e}")
            else:
                raise ProviderError(f"Bedrock API error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError("Bedrock request timed out")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Bedrock request: {e}")

    async def _get_stream_impl(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """
        Get streaming response from Amazon Bedrock.

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
                "json_mode": self.config.json_output,
            }

            if self.config.stop_sequences:
                request_kwargs["stop_sequences"] = self.config.stop_sequences

            # Convert to Bedrock specific format for streaming
            request_body = convert_to_bedrock_request(
                messages, self.config.model_name, **request_kwargs
            )

            model_id = self.config.model_id or self.config.model_name

            # Make the streaming API call
            start_time = time.time()
            response = self.client.invoke_model_with_response_stream(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body).encode('utf-8')
            )
            duration = time.time() - start_time

            # Process streaming response
            accumulated_content = ""
            stream = response.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        # Parse the chunk
                        chunk_data = json.loads(chunk.get('bytes').decode())

                        # Extract content from chunk
                        if 'delta' in chunk_data:
                            delta = chunk_data['delta']
                            if 'text' in delta:
                                content_chunk = delta['text']
                                accumulated_content += content_chunk
                                yield content_chunk

            # Track usage metrics
            self._track_usage(chunk_data if 'chunk_data' in locals() else {}, duration)

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ThrottlingException':
                raise ProviderError(f"Bedrock streaming rate limit exceeded: {e}")
            else:
                raise ProviderError(f"Bedrock streaming API error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error in Bedrock streaming request: {e}")

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert internal message format to Bedrock format.

        Args:
            messages: Internal message format

        Returns:
            Bedrock-compatible message format
        """
        bedrock_messages = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Map internal roles to Bedrock roles (Anthropic Claude format)
            if role == "system":
                bedrock_role = "system"
            elif role == "user":
                bedrock_role = "user"
            elif role == "assistant":
                bedrock_role = "assistant"
            elif role == "function":
                bedrock_role = "user"  # Functions are treated as user messages in Bedrock
            else:
                bedrock_role = "user"  # Default fallback

            bedrock_messages.append({
                "role": bedrock_role,
                "content": content
            })

        return bedrock_messages

    def _extract_response_content(self, response_body: Dict[str, Any]) -> str:
        """
        Extract content from Bedrock response based on model type.

        Args:
            response_body: Raw response from Bedrock

        Returns:
            Extracted text content
        """
        # Handle different response formats based on model
        model_id = self.config.model_id or self.config.model_name

        if "claude" in model_id.lower():
            # Claude response format
            if 'content' in response_body:
                content_blocks = response_body['content']
                if isinstance(content_blocks, list) and len(content_blocks) > 0:
                    return content_blocks[0].get('text', '')
                elif isinstance(content_blocks, str):
                    return content_blocks

        elif "jurassic" in model_id.lower() or "j2" in model_id.lower():
            # AI21 Jurassic response format
            if 'completions' in response_body and len(response_body['completions']) > 0:
                return response_body['completions'][0].get('data', {}).get('text', '')

        # Fallback - try to find text in common response fields
        for field in ['text', 'completion', 'result', 'output']:
            if field in response_body:
                content = response_body[field]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict) and 'text' in content:
                    return content['text']

        return str(response_body)  # Last resort fallback

    def _track_usage(self, response_body: Dict[str, Any], duration: float):
        """Track usage metrics for monitoring"""
        # Bedrock doesn't always provide detailed usage info
        # This is a simplified implementation
        try:
            if 'usage' in response_body:
                usage = response_body['usage']
                tokens_in = usage.get('input_tokens', 0)
                tokens_out = usage.get('output_tokens', 0)

                # Calculate approximate cost (simplified)
                cost_per_token_in = 0.0000015  # Approximate Bedrock pricing
                cost_per_token_out = 0.000002  # Approximate Bedrock pricing
                total_cost = (tokens_in * cost_per_token_in) + (tokens_out * cost_per_token_out)

                print(f"Bedrock Usage - In: {tokens_in}, Out: {tokens_out}, Cost: ${total_cost:.6f}")

        except Exception:
            # If usage tracking fails, continue without error
            pass

    def validate_input(self, input_type: InputMediaType, content: Any) -> bool:
        """Validate Bedrock specific input"""
        # First do base validation
        super().validate_input(input_type, content)

        # Bedrock specific validation
        if input_type == InputMediaType.IMAGE:
            if isinstance(content, str):
                # Should be a URL or S3 path
                if not (content.startswith("http") or content.startswith("s3://")):
                    raise InputValidationError("Image must be a valid HTTP URL or S3 path")
            elif not isinstance(content, bytes):
                raise InputValidationError("Image content must be bytes or string (URL/S3 path)")

        return True
