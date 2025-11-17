"""
Validator Factory for Tools Specification System.

Provides a centralized way to create and register validators by name.
"""

from typing import Dict

from .validator import IValidator
from .basic_validator import BasicValidator
from .noop_validator import NoOpValidator

from ...constants import (
    BASIC,
    NOOP,
    UNKNOWN_VALIDATOR_ERROR,
    COMMA,
    SPACE
)


class ValidatorFactory:
    """
    Factory for creating validator instances.
    
    Built-in Validators:
        - 'basic': BasicValidator - Comprehensive parameter validation
        - 'noop': NoOpValidator - No validation (for testing/development)
    
    Usage:
        # Get built-in validator
        validator = ValidatorFactory.get_validator('basic')
        
        # Register custom validator
        ValidatorFactory.register('my_custom', MyCustomValidator())
        validator = ValidatorFactory.get_validator('my_custom')
    """
    
    _validators: Dict[str, IValidator] = {
        BASIC: BasicValidator(),
        NOOP: NoOpValidator(),
    }
    
    @classmethod
    def get_validator(cls, name: str = BASIC) -> IValidator:
        """
        Get a validator by name.
        
        Args:
            name: Validator name ('basic', 'noop', etc.)
            
        Returns:
            IValidator instance
            
        Raises:
            ValueError: If validator name is not registered
        """
        validator = cls._validators.get(name)
        
        if not validator:
            available = (COMMA + SPACE).join(cls._validators.keys())
            raise ValueError(
                UNKNOWN_VALIDATOR_ERROR.format(VALIDATOR_NAME=name, AVAILABLE_VALIDATORS=available)
            )
        
        return validator
    
    @classmethod
    def register(cls, name: str, validator: IValidator):
        """
        Register a custom validator.
        
        Args:
            name: Name to register the validator under
            validator: Validator instance implementing IValidator
        
        Example:
            class MyValidator:
                async def validate(self, args, spec):
                    # Custom validation logic
                    pass
            
            ValidatorFactory.register('my_validator', MyValidator())
        """
        cls._validators[name] = validator

