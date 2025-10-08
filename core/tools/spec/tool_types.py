from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Local imports
from ..defaults import (
    DEFAULT_TOOL_VERSION,
    DEFAULT_TOOL_TIMEOUT_S,
    DEFAULT_RETURN_TYPE,
    DEFAULT_RETURN_TARGET,
    HTTP_DEFAULT_METHOD,
    DB_DEFAULT_DRIVER,
)
from ..constants import RETURNS, ARBITRARY_TYPES_ALLOWED, POPULATE_BY_NAME
from ..enum import ToolType, ToolReturnType, ToolReturnTarget
from .tool_parameters import ToolParameter
from .tool_config import RetryConfig, CircuitBreakerConfig, IdempotencyConfig

class ToolSpec(BaseModel):
    """Base class for tool specifications with common metadata"""
    id: str
    version: str = DEFAULT_TOOL_VERSION
    tool_name: str
    description: str
    tool_type: ToolType
    parameters: List[ToolParameter]
    return_type: ToolReturnType = Field(default=DEFAULT_RETURN_TYPE, alias=RETURNS)
    return_target: ToolReturnTarget = DEFAULT_RETURN_TARGET
    required: bool = False
    owner: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    timeout_s: int = DEFAULT_TOOL_TIMEOUT_S
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    # Advanced config
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    idempotency: IdempotencyConfig = Field(default_factory=IdempotencyConfig)
    metrics_tags: Dict[str, str] = Field(default_factory=dict)  # static tags for metrics
    model_config = {
        ARBITRARY_TYPES_ALLOWED: True,
        POPULATE_BY_NAME: True
    }


class FunctionToolSpec(ToolSpec):
    """Tool specification for function-based tools"""
    tool_type: ToolType = Field(default=ToolType.FUNCTION)


class HttpToolSpec(ToolSpec):
    """Tool specification for HTTP-based tools"""
    tool_type: ToolType = Field(default=ToolType.HTTP)

    # HTTP-specific fields
    url: str
    method: str = HTTP_DEFAULT_METHOD  # GET, POST, PUT, DELETE, etc.
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None  # Only for non-GET requests


class DbToolSpec(ToolSpec):
    """Tool specification for database-based tools"""
    tool_type: ToolType = Field(default=ToolType.DB)

    # Database-specific fields
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    driver: str = DB_DEFAULT_DRIVER  # postgresql, mysql, sqlite, etc.