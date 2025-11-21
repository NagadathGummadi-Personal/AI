"""
OpenAI LLM Implementation.

This module provides the concrete LLM implementation for OpenAI's API.
"""

import json
import time
from typing import Dict, Any, List, AsyncIterator
from ..base_llm import BaseLLM
from ...spec.llm_result import LLMResponse, LLMStreamChunk, LLMUsage
from ...spec.llm_context import LLMContext
from ...exceptions import ProviderError, InvalidResponseError, StreamingError
from ...enum import FinishReason
from ...constants import (
    OPENAI_FIELD_MESSAGES,
    OPENAI_FIELD_MODEL,
    RESPONSE_FIELD_CHOICES,
    RESPONSE_FIELD_MESSAGE,
    RESPONSE_FIELD_CONTENT,
    RESPONSE_FIELD_FINISH_REASON,
    RESPONSE_FIELD_USAGE,
    STREAM_FIELD_DELTA,
    STREAM_FIELD_CONTENT,
)


class OpenAILLM(BaseLLM):
    """
    OpenAI LLM implementation.
    
    Implements get_answer() and stream_answer() for OpenAI's chat completion API.
    
    Example:
        from core.llms.runtimes.connectors.openai import OpenAIConnector, OpenAILLM
        from core.llms.spec import LLMContext
        
        config = {"api_key": "sk-..."}
        connector = OpenAIConnector(config)
        llm = OpenAILLM(metadata, connector)
        
        messages = [{"role": "user", "content": "Hello!"}]
        response = await llm.get_answer(messages, LLMContext(), temperature=0.7)
        print(response.content)
    """
    
    async def get_answer(
        self,
        messages: List[Dict[str, Any]],
        ctx: LLMContext,
        **kwargs: Any
    ) -> LLMResponse:
        """
        Get complete response from OpenAI.
        
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
        max_tokens = params.get("max_tokens", self.metadata.max_output_tokens)
        
        # Validate token limits
        self._validate_token_limits(messages, max_tokens)
        
        # Apply parameter mappings
        mapped_params = self._apply_parameter_mappings(params)
        
        # Build request payload
        payload = {
            OPENAI_FIELD_MODEL: self.metadata.model_name,
            OPENAI_FIELD_MESSAGES: messages,
            **mapped_params
        }
        
        # Make request
        response = await self.connector.request("chat/completions", payload)
        
        # Parse response
        return self._parse_response(response, start_time)
    
    async def stream_answer(
        self,
        messages: List[Dict[str, Any]],
        ctx: LLMContext,
        **kwargs: Any
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Get streaming response from OpenAI.
        
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
        max_tokens = params.get("max_tokens", self.metadata.max_output_tokens)
        
        # Validate token limits
        self._validate_token_limits(messages, max_tokens)
        
        # Apply parameter mappings and enable streaming
        mapped_params = self._apply_parameter_mappings(params)
        
        # Build request payload
        payload = {
            OPENAI_FIELD_MODEL: self.metadata.model_name,
            OPENAI_FIELD_MESSAGES: messages,
            "stream": True,
            **mapped_params
        }
        
        # Stream request
        accumulated_content = []
        
        async for line in self.connector.stream_request("chat/completions", payload):
            # OpenAI sends "data: {...}" format
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("data: "):
                line = line[6:]  # Remove "data: " prefix
            
            if line == "[DONE]":
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
        Parse OpenAI API response into LLMResponse.
        
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
                    "Response missing choices",
                    provider="openai",
                    details={"response": response}
                )
            
            message = choices[0].get(RESPONSE_FIELD_MESSAGE, {})
            content = message.get(RESPONSE_FIELD_CONTENT, "")
            finish_reason = choices[0].get(RESPONSE_FIELD_FINISH_REASON)
            
            # Parse usage
            usage_data = response.get(RESPONSE_FIELD_USAGE, {})
            duration_ms = int((time.time() - start_time) * 1000)
            
            usage = LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                duration_ms=duration_ms
            )
            
            # Calculate cost
            if usage.prompt_tokens > 0:
                usage.cost_usd = self._calculate_cost(usage)
            
            return LLMResponse(
                content=content,
                role=message.get("role", "assistant"),
                finish_reason=self._map_finish_reason(finish_reason) if finish_reason else None,
                usage=usage,
                metadata={
                    "model": response.get("model"),
                    "id": response.get("id"),
                }
            )
        
        except (KeyError, TypeError, AttributeError) as e:
            raise InvalidResponseError(
                f"Failed to parse OpenAI response: {str(e)}",
                provider="openai",
                details={"error": str(e), "response": response}
            )
    
    def _map_finish_reason(self, reason: str) -> FinishReason:
        """Map OpenAI finish reason to standard enum."""
        mapping = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "content_filter": FinishReason.CONTENT_FILTER,
            "function_call": FinishReason.FUNCTION_CALL,
            "tool_calls": FinishReason.FUNCTION_CALL,
        }
        return mapping.get(reason, FinishReason.STOP)

