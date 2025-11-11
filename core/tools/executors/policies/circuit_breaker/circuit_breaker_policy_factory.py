"""
Factory for creating circuit breaker policy instances.
"""

from typing import Dict
from .circuit_breaker import ICircuitBreakerPolicy
from .standard_circuit_breaker_policy import StandardCircuitBreakerPolicy
from .adaptive_circuit_breaker_policy import AdaptiveCircuitBreakerPolicy
from .noop_circuit_breaker_policy import NoOpCircuitBreakerPolicy


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

