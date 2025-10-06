from pydantic import BaseModel, Field
from typing import List, Optional

class RetryConfig(BaseModel):
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay_s: float = 0.2
    max_delay_s: float = 2.0
    jitter_s: float = 0.1


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern"""
    enabled: bool = True
    failure_threshold: int = 5  # consecutive failures to open
    recovery_timeout_s: int = 30  # OPEN -> HALF_OPEN after timeout
    half_open_max_calls: int = 1  # allowed test calls in HALF_OPEN
    error_codes_to_trip: List[str] = Field(default_factory=lambda: ["TIMEOUT", "UNAVAILABLE", "TOOL_ERROR"])


class IdempotencyConfig(BaseModel):
    """Configuration for idempotency behavior"""
    enabled: bool = True
    key_fields: Optional[List[str]] = None  # if None, use all args
    ttl_s: Optional[int] = 3600
    persist_result: bool = True  # store result for reuse
    bypass_on_missing_key: bool = False  # if key_fields missing, bypass idempotency
