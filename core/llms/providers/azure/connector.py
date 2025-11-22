"""
Azure OpenAI Connector Implementation.

This module provides the connector for Azure OpenAI Service.
"""

import os
import asyncio
from typing import Dict, Any, Optional
import aiohttp
from ..base.connector import BaseConnector
from ...exceptions import (
    ConfigurationError,
    AuthenticationError,
    ServiceUnavailableError,
    TimeoutError,
    RateLimitError,
    ProviderError,
)
from ...constants import (
    ENV_AZURE_OPENAI_KEY,
    ENV_AZURE_OPENAI_ENDPOINT,
    ENV_AZURE_OPENAI_DEPLOYMENT,
    ENV_AZURE_OPENAI_API_VERSION,
    PROVIDER_AZURE,
)


class AzureConnector(BaseConnector):
    """
    Connector for Azure OpenAI Service.
    
    Handles authentication, connection management, and request handling
    for Azure OpenAI API endpoints.
    
    Configuration:
        - api_key: Azure OpenAI API key
        - endpoint: Azure OpenAI endpoint URL
        - deployment_name: Deployment name for the model
        - api_version: API version (default: 2024-02-15-preview)
        - timeout: Request timeout in seconds
        - max_retries: Maximum retry attempts
        
    Example:
        config = {
            "api_key": "...",
            "endpoint": "https://my-resource.openai.azure.com",
            "deployment_name": "gpt-4",
            "api_version": "2024-02-15-preview",
            "timeout": 30
        }
        connector = AzureConnector(config)
        await connector.connect()
    """
    
    DEFAULT_API_VERSION = "2024-02-15-preview"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure connector.
        
        Args:
            config: Connector configuration
            
        Raises:
            ConfigurationError: If required config is missing
        """
        super().__init__(config)
        self.api_key = self._get_api_key()
        self.endpoint = self._get_endpoint()
        self.deployment_name = self._get_deployment_name()
        self.api_version = self._get_api_version()
        self._session: Optional[aiohttp.ClientSession] = None
    
    def _validate_config(self) -> None:
        """Validate Azure-specific configuration."""
        super()._validate_config()
        
        # Validate required fields
        if not self._get_api_key():
            raise ConfigurationError(
                "Azure OpenAI API key not found. Provide 'api_key' in config or set AZURE_OPENAI_KEY environment variable.",
                provider=PROVIDER_AZURE,
                details={"env_var": ENV_AZURE_OPENAI_KEY}
            )
        
        if not self._get_endpoint():
            raise ConfigurationError(
                "Azure OpenAI endpoint not found. Provide 'endpoint' in config or set AZURE_OPENAI_ENDPOINT environment variable.",
                provider=PROVIDER_AZURE,
                details={"env_var": ENV_AZURE_OPENAI_ENDPOINT}
            )
        
        if not self._get_deployment_name():
            raise ConfigurationError(
                "Azure OpenAI deployment name not found. Provide 'deployment_name' in config or set AZURE_OPENAI_DEPLOYMENT environment variable.",
                provider=PROVIDER_AZURE,
                details={"env_var": ENV_AZURE_OPENAI_DEPLOYMENT}
            )
    
    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        if "api_key" in self.config:
            return self.config["api_key"]
        return os.environ.get(ENV_AZURE_OPENAI_KEY, "")
    
    def _get_endpoint(self) -> str:
        """Get endpoint from config or environment."""
        if "endpoint" in self.config:
            return self.config["endpoint"].rstrip("/")
        endpoint = os.environ.get(ENV_AZURE_OPENAI_ENDPOINT, "")
        return endpoint.rstrip("/") if endpoint else ""
    
    def _get_deployment_name(self) -> str:
        """Get deployment name from config or environment."""
        if "deployment_name" in self.config:
            return self.config["deployment_name"]
        return os.environ.get(ENV_AZURE_OPENAI_DEPLOYMENT, "")
    
    def _get_api_version(self) -> str:
        """Get API version from config or environment."""
        if "api_version" in self.config:
            return self.config["api_version"]
        return os.environ.get(ENV_AZURE_OPENAI_API_VERSION, self.DEFAULT_API_VERSION)
    
    def _build_url(self, operation: str) -> str:
        """
        Build full URL for Azure OpenAI API.
        
        Args:
            operation: API operation (e.g., "chat/completions")
            
        Returns:
            Full URL with deployment and API version
        """
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment_name}/"
            f"{operation}?api-version={self.api_version}"
        )
    
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
                    "api-key": self.api_key,
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
            # Try to make a minimal chat completion request
            url = self._build_url("chat/completions")
            test_payload = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            session = self._get_session()
            
            async with session.post(url, json=test_payload) as response:
                if response.status == 401:
                    raise AuthenticationError(
                        "Invalid Azure OpenAI API key",
                        provider=PROVIDER_AZURE,
                        details={"status_code": 401}
                    )
                
                if response.status == 404:
                    raise ConfigurationError(
                        "Azure OpenAI deployment not found. Check endpoint and deployment_name.",
                        provider=PROVIDER_AZURE,
                        details={
                            "status_code": 404,
                            "endpoint": self.endpoint,
                            "deployment": self.deployment_name
                        }
                    )
                
                if response.status == 503:
                    raise ServiceUnavailableError(
                        "Azure OpenAI service unavailable",
                        provider=PROVIDER_AZURE,
                        details={"status_code": 503}
                    )
                
                # Any 2xx or even 4xx (bad request) means connection works
                # We just want to verify auth and connectivity
                return True
        
        except aiohttp.ClientError as e:
            raise ServiceUnavailableError(
                f"Failed to connect to Azure OpenAI: {str(e)}",
                provider=PROVIDER_AZURE,
                details={"error": str(e)}
            )
    
    async def request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make a request to Azure OpenAI API.
        
        Args:
            endpoint: API operation (e.g., "chat/completions")
            payload: Request payload
            **kwargs: Additional options
            
        Returns:
            Response dictionary
            
        Raises:
            TimeoutError: If request times out
            RateLimitError: If rate limited
            AuthenticationError: If authentication fails
            ProviderError: For other API errors
        """
        url = self._build_url(endpoint)
        timeout = kwargs.get("timeout", self.get_timeout())
        session = self._get_session()
        
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                # Handle error status codes
                if response.status == 401:
                    raise AuthenticationError(
                        "Authentication failed",
                        provider=PROVIDER_AZURE,
                        details={"status_code": 401}
                    )
                
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Rate limit exceeded",
                        provider=PROVIDER_AZURE,
                        details={"status_code": 429},
                        retry_after=int(retry_after) if retry_after else None
                    )
                
                if response.status == 503:
                    raise ServiceUnavailableError(
                        "Service temporarily unavailable",
                        provider=PROVIDER_AZURE,
                        details={"status_code": 503}
                    )
                
                if response.status >= 400:
                    error_body = await response.text()
                    raise ProviderError(
                        f"Azure OpenAI API error: {response.status}",
                        provider=PROVIDER_AZURE,
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
                provider=PROVIDER_AZURE,
                details={"timeout_seconds": timeout}
            )
        
        except aiohttp.ClientError as e:
            raise ProviderError(
                f"Request failed: {str(e)}",
                provider=PROVIDER_AZURE,
                details={"error": str(e)}
            )
    
    async def stream_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        **kwargs: Any
    ):
        """
        Make a streaming request to Azure OpenAI API.
        
        Args:
            endpoint: API operation
            payload: Request payload (should have stream=True)
            **kwargs: Additional options
            
        Yields:
            Response chunks as they arrive
            
        Raises:
            TimeoutError: If request times out
            ProviderError: For API errors
        """
        url = self._build_url(endpoint)
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
                        f"Azure OpenAI API error: {response.status}",
                        provider=PROVIDER_AZURE,
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
                provider=PROVIDER_AZURE,
                details={"timeout_seconds": timeout}
            )
        
        except aiohttp.ClientError as e:
            raise ProviderError(
                f"Stream request failed: {str(e)}",
                provider=PROVIDER_AZURE,
                details={"error": str(e)}
            )

