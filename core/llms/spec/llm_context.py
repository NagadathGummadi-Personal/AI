"""
LLM Context.

This module defines the context object that carries execution metadata,
configuration, and optional services through LLM operations.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class LLMContext(BaseModel):
    """
    Context for LLM execution.
    
    Carries metadata, configuration, and optional service references
    through LLM operations. Similar to ToolContext for tools.
    
    Attributes:
        request_id: Unique request identifier
        user_id: User making the request
        session_id: Session identifier
        tenant_id: Tenant/organization identifier
        trace_id: Distributed tracing ID
        locale: User locale/language
        timezone: User timezone
        metadata: Additional context metadata
        config: Runtime configuration overrides
        
    Example:
        context = LLMContext(
            user_id="user-123",
            session_id="session-456",
            metadata={"app": "chatbot"}
        )
    """
    
    # Identifiers
    request_id: str = Field(
        default_factory=lambda: f"req-{uuid.uuid4()}",
        description="Unique request identifier"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User making the request"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier"
    )
    tenant_id: Optional[str] = Field(
        default=None,
        description="Tenant/organization identifier"
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="Distributed tracing ID"
    )
    
    # Localization
    locale: str = Field(
        default="en-US",
        description="User locale/language"
    )
    timezone: str = Field(
        default="UTC",
        description="User timezone"
    )
    
    # Additional data
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context metadata"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime configuration overrides"
    )
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "examples": [
                {
                    "request_id": "req-12345",
                    "user_id": "user-001",
                    "session_id": "session-abc",
                    "locale": "en-US",
                    "metadata": {
                        "app": "chatbot",
                        "version": "1.0"
                    }
                }
            ]
        }
    }
    
    def with_metadata(self, **kwargs) -> 'LLMContext':
        """
        Create a new context with additional metadata.
        
        Args:
            **kwargs: Metadata key-value pairs to add
            
        Returns:
            New LLMContext with merged metadata
            
        Example:
            new_ctx = context.with_metadata(model="gpt-4", temperature=0.7)
        """
        new_metadata = self.metadata.copy()
        new_metadata.update(kwargs)
        return self.model_copy(update={"metadata": new_metadata})
    
    def with_config(self, **kwargs) -> 'LLMContext':
        """
        Create a new context with additional config.
        
        Args:
            **kwargs: Config key-value pairs to add
            
        Returns:
            New LLMContext with merged config
            
        Example:
            new_ctx = context.with_config(timeout=60, max_retries=5)
        """
        new_config = self.config.copy()
        new_config.update(kwargs)
        return self.model_copy(update={"config": new_config})
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a config value.
        
        Args:
            key: Config key
            default: Default value if key not found
            
        Returns:
            Config value or default
        """
        return self.config.get(key, default)
    
    def to_log_dict(self) -> Dict[str, Any]:
        """
        Convert context to a dictionary suitable for logging.
        
        Returns:
            Dictionary with loggable context data
        """
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "trace_id": self.trace_id,
            "locale": self.locale,
        }


# Helper functions

def create_context(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> LLMContext:
    """
    Helper to create an LLMContext.
    
    Args:
        user_id: Optional user ID
        session_id: Optional session ID
        **kwargs: Additional context fields
        
    Returns:
        LLMContext instance
        
    Example:
        context = create_context(
            user_id="user-123",
            metadata={"app": "chatbot"}
        )
    """
    return LLMContext(
        user_id=user_id,
        session_id=session_id,
        **kwargs
    )


def create_test_context() -> LLMContext:
    """
    Create a context for testing purposes.
    
    Returns:
        LLMContext with test identifiers
        
    Example:
        context = create_test_context()
    """
    return LLMContext(
        user_id="test-user",
        session_id="test-session",
        tenant_id="test-tenant",
        metadata={"environment": "test"}
    )

