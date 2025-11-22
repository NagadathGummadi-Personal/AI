"""
Azure OpenAI Base LLM Implementation.

This module provides the base LLM implementation for Azure OpenAI Service.
Shared by all Azure models, with model-specific implementations overriding as needed.
"""

import json
import time
from typing import Dict, Any, List, AsyncIterator
from ..base.implementation import BaseLLM
from ...spec.llm_result import LLMResponse, LLMStreamChunk, LLMUsage
from ...spec.llm_context import LLMContext
from ...exceptions import InvalidResponseError
from ...enum import FinishReason
from ...constants import (
    OPENAI_FIELD_MESSAGES,
    RESPONSE_FIELD_CHOICES,
    RESPONSE_FIELD_MESSAGE,
    RESPONSE_FIELD_CONTENT,
    RESPONSE_FIELD_FINISH_REASON,
    RESPONSE_FIELD_USAGE,
    RESPONSE_FIELD_PROMPT_TOKENS,
    RESPONSE_FIELD_COMPLETION_TOKENS,
    RESPONSE_FIELD_TOTAL_TOKENS,
    STREAM_FIELD_DELTA,
    STREAM_FIELD_CONTENT,
    STREAM_DATA_PREFIX,
    STREAM_DATA_PREFIX_LENGTH,
    STREAM_DONE_TOKEN,
    STREAM_PARAM_TRUE,
    MESSAGE_FIELD_ROLE,
    META_MODEL,
    META_ID,
    META_DEPLOYMENT,
    PROVIDER_AZURE,
    PARAM_MAX_TOKENS,
    ERROR_MSG_RESPONSE_MISSING_CHOICES,
    FINISH_REASON_STOP,
    FINISH_REASON_LENGTH,
    FINISH_REASON_CONTENT_FILTER,
    FINISH_REASON_FUNCTION_CALL,
    DEFAULT_RESPONSE_ROLE,
)


class AzureBaseLLM(BaseLLM):
    """
    Azure OpenAI base LLM implementation.
    
    Provides shared implementation for all Azure OpenAI models.
    Implements get_answer() and stream_answer() for Azure OpenAI's API.
    Uses the same response format as OpenAI.
    
    Example:
        from core.llms.runtimes.connectors.azure import AzureConnector, AzureLLM
        from core.llms.spec import LLMContext
        
        config = {
            "api_key": "...",
            "endpoint": "https://my-resource.openai.azure.com",
            "deployment_name": "gpt-4"
        }
        connector = AzureConnector(config)
        llm = AzureLLM(metadata, connector)
        
        messages = [{"role": "user", "content": "Hello!"}]
        response = await llm.get_answer(messages, LLMContext(), temperature=0.7)
    """
    
    async def get_answer(
        self,
        messages: List[Dict[str, Any]],
        ctx: LLMContext,
        **kwargs: Any
    ) -> LLMResponse:
        """
        Get complete response from Azure OpenAI.
        
        Args:
            messages: List of message dicts
            ctx: LLM context
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLMResponse with content and usage
        """
        start_time = time.time()
        
        # Validate and prepare
        self._validate_messages(messages)
        
        # Merge parameters
        params = self._merge_parameters(kwargs)
        max_tokens = params.get(PARAM_MAX_TOKENS, self.metadata.max_output_tokens)
        
        # Validate token limits
        self._validate_token_limits(messages, max_tokens)
        
        # Apply parameter mappings
        mapped_params = self._apply_parameter_mappings(params)
        
        # Build request payload (Azure doesn't need model name in payload)
        payload = {
            OPENAI_FIELD_MESSAGES: messages,
            **mapped_params
        }
        
        # Make request
        response = await self.connector.request("chat/completions", payload)
        
        # Parse response (same format as OpenAI)
        return self._parse_response(response, start_time)
    
    async def stream_answer(
        self,
        messages: List[Dict[str, Any]],
        ctx: LLMContext,
        **kwargs: Any
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Get streaming response from Azure OpenAI.
        
        Args:
            messages: List of message dicts
            ctx: LLM context
            **kwargs: Additional parameters
            
        Yields:
            LLMStreamChunk objects
        """
        start_time = time.time()
        
        # Validate and prepare
        self._validate_messages(messages)
        
        # Merge parameters
        params = self._merge_parameters(kwargs)
        max_tokens = params.get(PARAM_MAX_TOKENS, self.metadata.max_output_tokens)
        
        # Validate token limits
        self._validate_token_limits(messages, max_tokens)
        
        # Apply parameter mappings and enable streaming
        mapped_params = self._apply_parameter_mappings(params)
        
        # Build request payload
        payload = {
            OPENAI_FIELD_MESSAGES: messages,
            STREAM_PARAM_TRUE: True,
            **mapped_params
        }
        
        # Stream request
        accumulated_content = []
        
        async for line in self.connector.stream_request("chat/completions", payload):
            # Azure OpenAI uses same format as OpenAI: "data: {...}"
            line = line.strip()
            if not line:
                continue
            
            if line.startswith(STREAM_DATA_PREFIX):
                line = line[STREAM_DATA_PREFIX_LENGTH:]  # Remove "data: " prefix
            
            if line == STREAM_DONE_TOKEN:
                # Final chunk with usage info
                duration_ms = int((time.time() - start_time) * 1000)
                yield LLMStreamChunk(
                    content="",
                    is_final=True,
                    finish_reason=FinishReason.STOP,
                    usage=LLMUsage(
                        prompt_tokens=self._estimate_tokens(messages),
                        completion_tokens=self._estimate_tokens([{"content": "".join(accumulated_content)}]),
                        duration_ms=duration_ms
                    )
                )
                break
            
            try:
                chunk_data = json.loads(line)
                
                # Extract content from delta
                choices = chunk_data.get(RESPONSE_FIELD_CHOICES, [])
                if not choices:
                    continue
                
                delta = choices[0].get(STREAM_FIELD_DELTA, {})
                content = delta.get(STREAM_FIELD_CONTENT, "")
                finish_reason = choices[0].get(RESPONSE_FIELD_FINISH_REASON)
                
                if content:
                    accumulated_content.append(content)
                    yield LLMStreamChunk(
                        content=content,
                        is_final=False
                    )
                
                if finish_reason:
                    duration_ms = int((time.time() - start_time) * 1000)
                    yield LLMStreamChunk(
                        content="",
                        is_final=True,
                        finish_reason=self._map_finish_reason(finish_reason),
                        usage=LLMUsage(
                            prompt_tokens=self._estimate_tokens(messages),
                            completion_tokens=self._estimate_tokens([{"content": "".join(accumulated_content)}]),
                            duration_ms=duration_ms
                        )
                    )
            
            except json.JSONDecodeError:
                # Skip malformed chunks
                continue
    
    def _parse_response(self, response: Dict[str, Any], start_time: float) -> LLMResponse:
        """
        Parse Azure OpenAI API response into LLMResponse.
        
        Args:
            response: Raw API response
            start_time: Request start time
            
        Returns:
            LLMResponse object
            
        Raises:
            InvalidResponseError: If response format is invalid
        """
        try:
            choices = response.get(RESPONSE_FIELD_CHOICES, [])
            if not choices:
                raise InvalidResponseError(
                    ERROR_MSG_RESPONSE_MISSING_CHOICES,
                    provider=PROVIDER_AZURE,
                    details={"response": response}
                )
            
            message = choices[0].get(RESPONSE_FIELD_MESSAGE, {})
            content = message.get(RESPONSE_FIELD_CONTENT)
            
            # Handle null content
            if content is None:
                content = ""
            finish_reason = choices[0].get(RESPONSE_FIELD_FINISH_REASON)
            
            # Parse usage
            usage_data = response.get(RESPONSE_FIELD_USAGE, {})
            duration_ms = int((time.time() - start_time) * 1000)
            
            usage = LLMUsage(
                prompt_tokens=usage_data.get(RESPONSE_FIELD_PROMPT_TOKENS, 0),
                completion_tokens=usage_data.get(RESPONSE_FIELD_COMPLETION_TOKENS, 0),
                total_tokens=usage_data.get(RESPONSE_FIELD_TOTAL_TOKENS, 0),
                duration_ms=duration_ms
            )
            
            # Calculate cost
            if usage.prompt_tokens > 0:
                usage.cost_usd = self._calculate_cost(usage)
            
            return LLMResponse(
                content=content,
                role=message.get(MESSAGE_FIELD_ROLE, DEFAULT_RESPONSE_ROLE),
                finish_reason=self._map_finish_reason(finish_reason) if finish_reason else None,
                usage=usage,
                metadata={
                    META_MODEL: response.get(META_MODEL),
                    META_ID: response.get(META_ID),
                    META_DEPLOYMENT: self.connector.deployment_name,
                }
            )
        
        except (KeyError, TypeError, AttributeError) as e:
            raise InvalidResponseError(
                f"Failed to parse Azure OpenAI response: {str(e)}",
                provider=PROVIDER_AZURE,
                details={"error": str(e), "response": response}
            )
    
    def _map_finish_reason(self, reason: str) -> FinishReason:
        """Map Azure finish reason to standard enum."""
        mapping = {
            FINISH_REASON_STOP: FinishReason.STOP,
            FINISH_REASON_LENGTH: FinishReason.LENGTH,
            FINISH_REASON_CONTENT_FILTER: FinishReason.CONTENT_FILTER,
            FINISH_REASON_FUNCTION_CALL: FinishReason.FUNCTION_CALL,
            "tool_calls": FinishReason.FUNCTION_CALL,  # Provider-specific
        }
        return mapping.get(reason, FinishReason.STOP)

