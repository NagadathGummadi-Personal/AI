"""
Retry Policies for Tools Specification System.

This module provides pluggable retry strategies for handling transient failures
with configurable retry logic, backoff strategies, and exception handling.

Strategy Pattern Implementation:
=================================
All policies implement IRetryPolicy, allowing runtime selection of the
appropriate retry strategy for each tool.

Available Strategies:
=====================
- NoRetryPolicy: Fail immediately on first error
- FixedRetryPolicy: Retry with fixed delay between attempts
- ExponentialBackoffRetryPolicy: Retry with exponentially increasing delays
- CustomRetryPolicy: User-defined retry logic

Usage:
    from core.tools.executors.policies import ExponentialBackoffRetryPolicy
    
    # Configure at tool spec creation
    spec.retry_policy = ExponentialBackoffRetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0
    )
    
    # Or use factory
    from core.tools.executors.policies import RetryPolicyFactory
    policy = RetryPolicyFactory.get_policy('exponential')
    spec.retry_policy = policy

Extending:
==========
Create custom policy by implementing IRetryPolicy:

    class CircuitBreakerRetry(IRetryPolicy):
        async def execute_with_retry(self, func, *args, **kwargs):
            # Your retry logic
            pass

Note:
    Retry policies should handle only retryable errors. Validation errors,
    authentication failures, etc. should fail immediately.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable, Dict, List, Optional, Type
from enum import Enum


class RetryableErrorType(Enum):
    """Types of errors that are typically retryable."""
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"


class IRetryPolicy(ABC):
    """
    Interface for retry policies.
    
    Retry policies handle transient failures by retrying operations with
    configurable delays and backoff strategies.
    
    Methods:
        execute_with_retry: Execute function with retry logic
        should_retry: Determine if an error should trigger retry
    """
    
    @abstractmethod
    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Async function to execute
            tool_name: Name of the tool (for logging/metrics)
            
        Returns:
            Result from the function
            
        Raises:
            Exception: If all retries exhausted or non-retryable error
        """
        pass
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        # Default: retry on common transient errors
        retryable_types = (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        )
        return isinstance(exception, retryable_types)


class NoRetryPolicy(IRetryPolicy):
    """
    No retry policy - fail immediately on first error.
    
    Useful for:
    - Operations that should never retry
    - Development/testing
    - When circuit breaker handles resilience
    
    Usage:
        policy = NoRetryPolicy()
        spec.retry_policy = policy
        
        # First error causes immediate failure
    """
    
    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """Execute without retry."""
        return await func()


class FixedRetryPolicy(IRetryPolicy):
    """
    Fixed delay retry policy.
    
    Retries with a fixed delay between attempts. Simple and predictable.
    
    Features:
        - Configurable number of attempts
        - Fixed delay between retries
        - Configurable retryable exceptions
        - Optional jitter to avoid thundering herd
    
    Usage:
        policy = FixedRetryPolicy(
            max_attempts=3,
            delay_seconds=2.0,
            jitter=0.5  # ±0.5 seconds random jitter
        )
        
        spec.retry_policy = policy
    
    Example:
        # Attempt 1: Execute immediately
        # Fails
        # Wait 2 seconds
        # Attempt 2: Execute
        # Fails
        # Wait 2 seconds
        # Attempt 3: Execute
        # If fails, raise exception
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay_seconds: float = 1.0,
        jitter: float = 0.0,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize fixed retry policy.
        
        Args:
            max_attempts: Maximum number of attempts (including first)
            delay_seconds: Fixed delay between retries
            jitter: Random jitter to add/subtract from delay (seconds)
            retryable_exceptions: List of exception types to retry
        """
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        ]
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if should retry based on exception type and attempt count."""
        if attempt >= self.max_attempts - 1:  # -1 because attempt is 0-based
            return False
        
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
    
    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """Execute with fixed delay retry."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = await func()
                return result
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    raise
                
                if attempt < self.max_attempts - 1:
                    # Calculate delay with jitter
                    delay = self.delay_seconds
                    if self.jitter > 0:
                        delay += random.uniform(-self.jitter, self.jitter)
                    delay = max(0, delay)  # Ensure non-negative
                    
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception


class ExponentialBackoffRetryPolicy(IRetryPolicy):
    """
    Exponential backoff retry policy.
    
    Retries with exponentially increasing delays. Good for handling rate limits
    and giving failing services time to recover.
    
    Features:
        - Exponentially increasing delays
        - Configurable base and max delay
        - Optional jitter
        - Configurable multiplier
    
    Delay Formula:
        delay = min(base_delay * (multiplier ^ attempt), max_delay) ± jitter
    
    Usage:
        policy = ExponentialBackoffRetryPolicy(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0,
            multiplier=2.0,
            jitter=0.1
        )
    
    Example:
        # Attempt 1: Execute immediately
        # Fails, wait 1 second
        # Attempt 2: Execute
        # Fails, wait 2 seconds
        # Attempt 3: Execute
        # Fails, wait 4 seconds
        # Attempt 4: Execute
        # Fails, wait 8 seconds
        # Attempt 5: Execute
        # If fails, raise exception
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: float = 0.1,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize exponential backoff retry policy.
        
        Args:
            max_attempts: Maximum number of attempts
            base_delay: Base delay for first retry (seconds)
            max_delay: Maximum delay between retries (seconds)
            multiplier: Exponential multiplier (typically 2.0)
            jitter: Random jitter as percentage (0.0-1.0)
            retryable_exceptions: List of exception types to retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        ]
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if should retry."""
        if attempt >= self.max_attempts - 1:
            return False
        
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt with exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base * multiplier^attempt
        delay = self.base_delay * (self.multiplier ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter
        if self.jitter > 0:
            jitter_amount = delay * self.jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)
    
    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """Execute with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = await func()
                return result
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    raise
                
                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception


class CustomRetryPolicy(IRetryPolicy):
    """
    Custom retry policy using user-provided function.
    
    Allows complete control over retry logic by accepting a custom retry function.
    The function receives the operation, current attempt, and last exception.
    
    Features:
        - Complete flexibility
        - Can access external state
        - Complex business logic
        - Integration with external services
    
    Usage:
        async def my_retry_logic(func, attempt, last_exception):
            if attempt >= 5:
                raise last_exception
            
            if isinstance(last_exception, RateLimitError):
                await asyncio.sleep(60)  # Wait 1 minute for rate limit
            else:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            return await func()
        
        policy = CustomRetryPolicy(my_retry_logic)
        spec.retry_policy = policy
    """
    
    def __init__(
        self,
        retry_func: Callable[[Callable[[], Awaitable[Any]], int, Optional[Exception]], Awaitable[Any]]
    ):
        """
        Initialize with custom retry function.
        
        Args:
            retry_func: Async function that implements retry logic
                       Signature: async def(func, attempt, last_exception) -> result
        
        Raises:
            TypeError: If retry_func is not callable
        """
        if not callable(retry_func):
            raise TypeError("retry_func must be callable")
        
        self.retry_func = retry_func
    
    async def execute_with_retry(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """Execute with custom retry logic."""
        attempt = 0
        last_exception = None
        
        while True:
            try:
                if attempt == 0:
                    # First attempt
                    result = await func()
                else:
                    # Retry through custom function
                    result = await self.retry_func(func, attempt, last_exception)
                
                return result
                
            except Exception as e:
                last_exception = e
                attempt += 1
                
                # Let custom function decide if should continue
                # If it raises, we stop retrying
                if attempt >= 10:  # Safety limit
                    raise


class RetryPolicyFactory:
    """
    Factory for creating retry policy instances.
    
    Built-in Policies:
        - 'none': NoRetryPolicy
        - 'fixed': FixedRetryPolicy
        - 'exponential': ExponentialBackoffRetryPolicy
    
    Usage:
        policy = RetryPolicyFactory.get_policy('exponential')
        spec.retry_policy = policy
    """
    
    _policies: Dict[str, IRetryPolicy] = {
        'none': NoRetryPolicy(),
        'fixed': FixedRetryPolicy(),
        'exponential': ExponentialBackoffRetryPolicy(),
    }
    
    @classmethod
    def get_policy(cls, name: str = 'none') -> IRetryPolicy:
        """
        Get a retry policy by name.
        
        Args:
            name: Policy name ('none', 'fixed', 'exponential')
            
        Returns:
            IRetryPolicy instance
            
        Raises:
            ValueError: If policy name not found
        """
        policy = cls._policies.get(name)
        
        if not policy:
            raise ValueError(
                f"Unknown retry policy: {name}. "
                f"Available: {', '.join(cls._policies.keys())}"
            )
        
        return policy
    
    @classmethod
    def register(cls, name: str, policy: IRetryPolicy):
        """
        Register a custom retry policy.
        
        Args:
            name: Policy name
            policy: Policy instance
        """
        cls._policies[name] = policy

