"""
Circuit Breaker Policies for Tools Specification System.

This module provides pluggable circuit breaker strategies that prevent cascading
failures by "opening the circuit" after a threshold of failures.

Strategy Pattern Implementation:
=================================
All policies implement ICircuitBreakerPolicy, allowing runtime selection of
the appropriate circuit breaking strategy for each tool.

Available Strategies:
=====================
- StandardCircuitBreakerPolicy: Uses pybreaker with fixed thresholds
- AdaptiveCircuitBreakerPolicy: Adjusts thresholds based on error rates
- NoOpCircuitBreakerPolicy: Disables circuit breaking (for development/testing)

Usage:
    from core.tools.executors.policies import StandardCircuitBreakerPolicy
    
    # Configure at tool spec creation
    spec.circuit_breaker_policy = StandardCircuitBreakerPolicy(
        failure_threshold=5,
        recovery_timeout=30
    )
    
    # Or use factory
    from core.tools.executors.policies import CircuitBreakerPolicyFactory
    policy = CircuitBreakerPolicyFactory.get_policy('standard')
    spec.circuit_breaker_policy = policy

Extending:
==========
Create custom policy by implementing ICircuitBreakerPolicy:

    class RateLimitCircuitBreaker(ICircuitBreakerPolicy):
        async def execute_with_breaker(self, func, tool_name, *args, **kwargs):
            # Your logic
            pass

Note:
    Circuit breakers are stateful - they maintain failure counts and state
    across multiple executions of the same tool.
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Awaitable
from contextlib import asynccontextmanager


class ICircuitBreakerPolicy(ABC):
    """
    Interface for circuit breaker policies.
    
    Circuit breakers prevent cascading failures by stopping requests to a
    failing service after a threshold is reached.
    
    Methods:
        execute_with_breaker: Execute function with circuit breaker protection
        get_state: Get current circuit breaker state
        reset: Reset the circuit breaker
    
    States:
        CLOSED: Normal operation, requests pass through
        OPEN: Circuit is open, requests fail immediately
        HALF_OPEN: Testing if service has recovered
    """
    
    @abstractmethod
    async def execute_with_breaker(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            tool_name: Name of the tool (used for tracking state)
            
        Returns:
            Result from the function
            
        Raises:
            Exception: If circuit is open or function fails
        """
        pass
    
    @abstractmethod
    def get_state(self, tool_name: str) -> str:
        """
        Get current state of circuit breaker for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            State string: 'closed', 'open', or 'half_open'
        """
        pass
    
    @abstractmethod
    def reset(self, tool_name: str):
        """
        Reset the circuit breaker for a tool.
        
        Args:
            tool_name: Name of the tool
        """
        pass


class StandardCircuitBreakerPolicy(ICircuitBreakerPolicy):
    """
    Standard circuit breaker using pybreaker library.
    
    Uses fixed thresholds for failure detection:
    - Failure Threshold: Number of failures before opening circuit
    - Recovery Timeout: Time before attempting to close circuit
    
    Features:
        - Wraps pybreaker library
        - Per-tool circuit breakers
        - Automatic state management
        - Failure counting
    
    Usage:
        policy = StandardCircuitBreakerPolicy(
            failure_threshold=5,    # Open after 5 failures
            recovery_timeout=30     # Try recovery after 30 seconds
        )
        
        spec.circuit_breaker_policy = policy
    
    Example:
        # Circuit starts CLOSED
        result = await policy.execute_with_breaker(my_func, 'tool1')
        
        # After 5 failures, circuit OPENS
        # Subsequent calls fail immediately
        
        # After 30 seconds, circuit goes HALF_OPEN
        # One test call allowed
        
        # If test succeeds, circuit CLOSES
        # If test fails, circuit stays OPEN
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        """
        Initialize standard circuit breaker policy.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._breakers: Dict[str, Any] = {}  # tool_name -> CircuitBreaker
    
    def _get_breaker(self, tool_name: str):
        """Get or create circuit breaker for a tool."""
        if tool_name not in self._breakers:
            from utils.circuitBreaker.CircuitBreaker import CircuitBreaker
            self._breakers[tool_name] = CircuitBreaker(
                max_failures=self.failure_threshold,
                reset_timeout=self.recovery_timeout
            )
        return self._breakers[tool_name]
    
    async def execute_with_breaker(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            tool_name: Tool name for circuit tracking
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        breaker = self._get_breaker(tool_name)
        
        # Check if circuit is open
        if breaker.state.value == 'open':
            raise Exception(f"Circuit breaker is open for {tool_name}")
        
        try:
            result = await func()
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            # Check if circuit opened after this failure
            if breaker.state.value == 'open':
                raise Exception(f"Circuit breaker is open for {tool_name}") from e
            raise
    
    def get_state(self, tool_name: str) -> str:
        """Get circuit breaker state."""
        if tool_name not in self._breakers:
            return 'closed'
        breaker = self._breakers[tool_name]
        return breaker.state.value
    
    def reset(self, tool_name: str):
        """Reset circuit breaker."""
        if tool_name in self._breakers:
            self._breakers[tool_name].close()


class AdaptiveCircuitBreakerPolicy(ICircuitBreakerPolicy):
    """
    Adaptive circuit breaker that adjusts thresholds based on error rates.
    
    Unlike standard circuit breakers with fixed thresholds, this implementation
    adapts based on:
    - Recent error rate
    - Response time patterns
    - Success/failure ratio
    
    Features:
        - Dynamic threshold adjustment
        - Error rate monitoring
        - Gradual recovery
        - Configurable sensitivity
    
    Usage:
        policy = AdaptiveCircuitBreakerPolicy(
            base_threshold=5,
            max_threshold=20,
            error_rate_threshold=0.5,  # 50% error rate
            window_size=100             # Last 100 requests
        )
    
    Example:
        # Threshold starts at 5
        # If error rate < 50%, threshold increases to 20
        # If error rate > 50%, threshold decreases to 5
        # Adapts based on service behavior
    """
    
    def __init__(
        self,
        base_threshold: int = 5,
        max_threshold: int = 20,
        error_rate_threshold: float = 0.5,
        window_size: int = 100
    ):
        """
        Initialize adaptive circuit breaker.
        
        Args:
            base_threshold: Minimum failure threshold
            max_threshold: Maximum failure threshold
            error_rate_threshold: Error rate that triggers adjustment
            window_size: Number of recent requests to consider
        """
        self.base_threshold = base_threshold
        self.max_threshold = max_threshold
        self.error_rate_threshold = error_rate_threshold
        self.window_size = window_size
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def _get_state(self, tool_name: str) -> Dict[str, Any]:
        """Get or create state for a tool."""
        if tool_name not in self._states:
            self._states[tool_name] = {
                'failures': 0,
                'successes': 0,
                'recent_results': [],  # Boolean list of recent results
                'is_open': False,
                'opened_at': None,
                'current_threshold': self.base_threshold
            }
        return self._states[tool_name]
    
    def _calculate_error_rate(self, state: Dict[str, Any]) -> float:
        """Calculate current error rate."""
        recent = state['recent_results']
        if not recent:
            return 0.0
        errors = sum(1 for r in recent if not r)
        return errors / len(recent)
    
    def _adjust_threshold(self, state: Dict[str, Any]):
        """Adjust threshold based on error rate."""
        error_rate = self._calculate_error_rate(state)
        
        if error_rate < self.error_rate_threshold / 2:
            # Service is healthy, increase threshold
            state['current_threshold'] = min(
                state['current_threshold'] + 1,
                self.max_threshold
            )
        elif error_rate > self.error_rate_threshold:
            # Service is unhealthy, decrease threshold
            state['current_threshold'] = max(
                state['current_threshold'] - 1,
                self.base_threshold
            )
    
    async def execute_with_breaker(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """Execute with adaptive circuit breaker."""
        state = self._get_state(tool_name)
        
        # Check if circuit is open
        if state['is_open']:
            # Check if recovery timeout has passed
            if time.time() - state['opened_at'] > 30:  # Recovery timeout
                state['is_open'] = False
                state['failures'] = 0
            else:
                raise Exception(f"Circuit breaker is open for {tool_name}")
        
        try:
            result = await func()
            
            # Record success
            state['successes'] += 1
            state['failures'] = 0
            state['recent_results'].append(True)
            
            # Trim window
            if len(state['recent_results']) > self.window_size:
                state['recent_results'].pop(0)
            
            # Adjust threshold
            self._adjust_threshold(state)
            
            return result
            
        except Exception as e:
            # Record failure
            state['failures'] += 1
            state['recent_results'].append(False)
            
            # Trim window
            if len(state['recent_results']) > self.window_size:
                state['recent_results'].pop(0)
            
            # Check if threshold exceeded
            if state['failures'] >= state['current_threshold']:
                state['is_open'] = True
                state['opened_at'] = time.time()
            
            # Adjust threshold
            self._adjust_threshold(state)
            
            raise
    
    def get_state(self, tool_name: str) -> str:
        """Get circuit state."""
        state = self._get_state(tool_name)
        return 'open' if state['is_open'] else 'closed'
    
    def reset(self, tool_name: str):
        """Reset circuit breaker."""
        if tool_name in self._states:
            self._states[tool_name] = {
                'failures': 0,
                'successes': 0,
                'recent_results': [],
                'is_open': False,
                'opened_at': None,
                'current_threshold': self.base_threshold
            }


class NoOpCircuitBreakerPolicy(ICircuitBreakerPolicy):
    """
    No-op circuit breaker that doesn't actually break circuits.
    
    Useful for:
    - Development/testing
    - Disabling circuit breaking for specific tools
    - Gradually rolling out circuit breakers
    
    Usage:
        policy = NoOpCircuitBreakerPolicy()
        spec.circuit_breaker_policy = policy
        
        # All requests pass through, no circuit breaking
    """
    
    async def execute_with_breaker(
        self,
        func: Callable[[], Awaitable[Any]],
        tool_name: str
    ) -> Any:
        """Execute without circuit breaking."""
        return await func()
    
    def get_state(self, tool_name: str) -> str:
        """Always returns 'closed'."""
        return 'closed'
    
    def reset(self, tool_name: str):
        """No-op reset."""
        pass


class CircuitBreakerPolicyFactory:
    """
    Factory for creating circuit breaker policy instances.
    
    Built-in Policies:
        - 'standard': StandardCircuitBreakerPolicy
        - 'adaptive': AdaptiveCircuitBreakerPolicy
        - 'noop': NoOpCircuitBreakerPolicy
    
    Usage:
        policy = CircuitBreakerPolicyFactory.get_policy('standard')
        spec.circuit_breaker_policy = policy
    """
    
    _policies: Dict[str, ICircuitBreakerPolicy] = {
        'standard': StandardCircuitBreakerPolicy(),
        'adaptive': AdaptiveCircuitBreakerPolicy(),
        'noop': NoOpCircuitBreakerPolicy(),
    }
    
    @classmethod
    def get_policy(cls, name: str = 'standard') -> ICircuitBreakerPolicy:
        """
        Get a circuit breaker policy by name.
        
        Args:
            name: Policy name ('standard', 'adaptive', 'noop')
            
        Returns:
            ICircuitBreakerPolicy instance
            
        Raises:
            ValueError: If policy name not found
        """
        policy = cls._policies.get(name)
        
        if not policy:
            raise ValueError(
                f"Unknown circuit breaker policy: {name}. "
                f"Available: {', '.join(cls._policies.keys())}"
            )
        
        return policy
    
    @classmethod
    def register(cls, name: str, policy: ICircuitBreakerPolicy):
        """
        Register a custom circuit breaker policy.
        
        Args:
            name: Policy name
            policy: Policy instance
        """
        cls._policies[name] = policy

