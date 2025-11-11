"""
Adaptive Circuit Breaker Policy.

Adjusts thresholds based on error rates and service health.
"""

import time
from typing import Any, Callable, Dict, Awaitable
from .circuit_breaker import ICircuitBreakerPolicy


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

