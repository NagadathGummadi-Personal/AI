"""
OpenAI Connector Implementation.

This module provides the connector for OpenAI's API.
"""

import os
import asyncio
from typing import Dict, Any, Optional
import aiohttp
from ..base_connector import BaseConnector
from ...exceptions import (
    ConfigurationError,
    AuthenticationError,
    ServiceUnavailableError,
    TimeoutError,
    RateLimitError,
    ProviderError,
)
from ...constants import (
    ENV_OPENAI_API_KEY,
)


class OpenAIConnector(BaseConnector):
    """
    Connector for OpenAI API.
    
    Handles authentication, connection management, and request handling
    for OpenAI's API endpoints.
    
    Configuration:
        - api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        - base_url: Base URL for API (default: https://api.openai.com/v1)
        - timeout: Request timeout in seconds
        - max_retries: Maximum retry attempts
        
    Example:
        config = {
            "api_key": "sk-...",
            "timeout": 30,
            "max_retries": 3
        }
        connector = OpenAIConnector(config)
        await connector.connect()
    """
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI connector.
        
        Args:
            config: Connector configuration
            
        Raises:
            ConfigurationError: If required config is missing
        """
        super().__init__(config)
        self.base_url = config.get("base_url", self.DEFAULT_BASE_URL)
        self.api_key = self._get_api_key()
        self._session: Optional[aiohttp.ClientSession] = None
    
    def _validate_config(self) -> None:
        """Validate OpenAI-specific configuration."""
        super()._validate_config()
        
        # API key validation
        api_key = self._get_api_key()
        if not api_key:
            raise ConfigurationError(
                "OpenAI API key not found. Provide 'api_key' in config or set OPENAI_API_KEY environment variable.",
                provider="openai",
                details={"env_var": ENV_OPENAI_API_KEY}
            )
    
    def _get_api_key(self) -> str:
        """
        Get API key from config or environment.
        
        Returns:
            API key
        """
        # First check config
        if "api_key" in self.config:
            return self.config["api_key"]
        
        # Then check env var
        api_key_env = self.config.get("api_key_env", ENV_OPENAI_API_KEY)
        return os.environ.get(api_key_env, "")
    
    def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session (lazy initialization).
        
        Returns:
            Active aiohttp session
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.get_timeout())
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session
    
    async def close(self) -> None:
        """
        Close session and clean up resources (optional cleanup).
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def test_connection(self) -> bool:
        """
        Test connection by making a simple API call.
        
        Returns:
            True if connection test succeeds
            
        Raises:
            AuthenticationError: If API key is invalid
            ServiceUnavailableError: If service is down
        """
        try:
            # Make a simple request to list models
            url = f"{self.base_url}/models"
            session = self._get_session()
            async with session.get(url) as response:
                if response.status == 401:
                    raise AuthenticationError(
                        "Invalid OpenAI API key",
                        provider="openai",
                        details={"status_code": 401}
                    )
                
                if response.status == 503:
                    raise ServiceUnavailableError(
                        "OpenAI service unavailable",
                        provider="openai",
                        details={"status_code": 503}
                    )
                
                response.raise_for_status()
                return True
        
        except aiohttp.ClientError as e:
            raise ServiceUnavailableError(
                f"Failed to connect to OpenAI: {str(e)}",
                provider="openai",
                details={"error": str(e)}
            )
    
    async def request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make a request to OpenAI API.
        
        Args:
            endpoint: API endpoint (e.g., "chat/completions")
            payload: Request payload
            **kwargs: Additional options (stream, timeout, etc.)
            
        Returns:
            Response dictionary
            
        Raises:
            TimeoutError: If request times out
            RateLimitError: If rate limited
            AuthenticationError: If authentication fails
            ProviderError: For other API errors
        """
        url = f"{self.base_url}/{endpoint}"
        timeout = kwargs.get("timeout", self.get_timeout())
        session = self._get_session()
        
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                # Handle error status codes
                if response.status == 401:
                    raise AuthenticationError(
                        "Authentication failed",
                        provider="openai",
                        details={"status_code": 401}
                    )
                
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Rate limit exceeded",
                        provider="openai",
                        details={"status_code": 429},
                        retry_after=int(retry_after) if retry_after else None
                    )
                
                if response.status == 503:
                    raise ServiceUnavailableError(
                        "Service temporarily unavailable",
                        provider="openai",
                        details={"status_code": 503}
                    )
                
                if response.status >= 400:
                    error_body = await response.text()
                    raise ProviderError(
                        f"OpenAI API error: {response.status}",
                        provider="openai",
                        details={
                            "status_code": response.status,
                            "error_body": error_body
                        }
                    )
                
                # Parse and return response
                return await response.json()
        
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Request timed out after {timeout} seconds",
                provider="openai",
                details={"timeout_seconds": timeout}
            )
        
        except aiohttp.ClientError as e:
            raise ProviderError(
                f"Request failed: {str(e)}",
                provider="openai",
                details={"error": str(e)}
            )
    
    async def stream_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        **kwargs: Any
    ):
        """
        Make a streaming request to OpenAI API.
        
        Args:
            endpoint: API endpoint
            payload: Request payload (should have stream=True)
            **kwargs: Additional options
            
        Yields:
            Response chunks as they arrive
            
        Raises:
            TimeoutError: If request times out
            ProviderError: For API errors
        """
        url = f"{self.base_url}/{endpoint}"
        timeout = kwargs.get("timeout", self.get_timeout())
        session = self._get_session()
        
        # Ensure streaming is enabled in payload
        payload["stream"] = True
        
        try:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                # Check for errors
                if response.status >= 400:
                    error_body = await response.text()
                    raise ProviderError(
                        f"OpenAI API error: {response.status}",
                        provider="openai",
                        details={
                            "status_code": response.status,
                            "error_body": error_body
                        }
                    )
                
                # Yield chunks as they arrive
                async for line in response.content:
                    if line:
                        yield line.decode('utf-8')
        
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Stream request timed out after {timeout} seconds",
                provider="openai",
                details={"timeout_seconds": timeout}
            )
        
        except aiohttp.ClientError as e:
            raise ProviderError(
                f"Stream request failed: {str(e)}",
                provider="openai",
                details={"error": str(e)}
            )

