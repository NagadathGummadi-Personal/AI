"""
Idempotency Key Generation Strategies.

This module provides various strategies for generating idempotency keys based on
tool arguments, context, and configuration. Different strategies can be used for
different tool types and use cases.

Strategy Pattern Implementation:
=================================
All key generators implement the IIdempotencyKeyGenerator interface, allowing
runtime selection of the appropriate strategy for each tool.

Available Strategies:
=====================
- DefaultIdempotencyKeyGenerator: Uses all args + tool ID + user/session IDs
- FieldBasedIdempotencyKeyGenerator: Uses only specified fields from config
- HashBasedIdempotencyKeyGenerator: Uses cryptographic hash of selected data
- CustomIdempotencyKeyGenerator: Accepts custom key generation function

Usage:
    from core.tools.executors.idempotency import DefaultIdempotencyKeyGenerator
    
    # Use default strategy
    generator = DefaultIdempotencyKeyGenerator()
    key = generator.generate_key(args, ctx, spec)
    
    # Use field-based strategy (specified in IdempotencyConfig)
    generator = FieldBasedIdempotencyKeyGenerator()
    key = generator.generate_key(args, ctx, spec)
    
    # Use custom function
    def custom_key_fn(args, ctx, spec):
        return f"{spec.id}:{args['user_id']}:{args['timestamp']}"
    
    generator = CustomIdempotencyKeyGenerator(custom_key_fn)
    key = generator.generate_key(args, ctx, spec)

Extending:
==========
To create a custom idempotency key generator:

1. Inherit from IIdempotencyKeyGenerator
2. Implement the generate_key method
3. Configure it in the tool spec

Example:
    class UUIDIdempotencyKeyGenerator(IIdempotencyKeyGenerator):
        def generate_key(self, args, ctx, spec):
            return str(uuid.uuid4())
    
    # Use in tool spec
    spec.idempotency_key_generator = UUIDIdempotencyKeyGenerator()
"""

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from ...constants import EMPTY_STRING, USER_ID, SESSION_ID, SEPARATOR, SHA256_HASH_ALGORITHM, DEFAULT_IDEMPOTENCY_KEY_GENERATOR, FIELD_BASED_IDEMPOTENCY_KEY_GENERATOR, HASH_BASED_IDEMPOTENCY_KEY_GENERATOR, COMMA, UNKNOWN_IDEMPOTENCY_KEY_GENERATOR, SPACE, KEY_FUNCTION_NOT_CALLABLE


class IIdempotencyKeyGenerator(ABC):
    """
    Interface for idempotency key generation strategies.
    
    This abstract base class defines the contract for all idempotency key
    generators. Each implementation can use different approaches to generate
    unique, deterministic keys based on tool arguments and context.
    
    Methods:
        generate_key: Generate an idempotency key from args, context, and spec
    
    Implementing Classes:
        DefaultIdempotencyKeyGenerator: Standard hash-based generation
        FieldBasedIdempotencyKeyGenerator: Uses specific fields only
        HashBasedIdempotencyKeyGenerator: Cryptographic hash approach
        CustomIdempotencyKeyGenerator: Custom function-based generation
    """
    
    @abstractmethod
    def generate_key(self, args: Dict[str, Any], ctx: Any, spec: Any) -> str:
        """
        Generate an idempotency key.
        
        Args:
            args: Tool execution arguments
            ctx: Tool execution context (ToolContext)
            spec: Tool specification (ToolSpec)
            
        Returns:
            str: Unique idempotency key for this specific execution
            
        Note:
            Keys should be deterministic - same inputs should always produce
            the same key to enable idempotency checking.
        """
        pass


class DefaultIdempotencyKeyGenerator(IIdempotencyKeyGenerator):
    """
    Default idempotency key generator using SHA-256 hash.
    
    This strategy generates keys by hashing a combination of:
    - Tool ID
    - User ID (if available)
    - Session ID (if available)
    - All tool arguments (unless key_fields is specified)
    
    The key is a SHA-256 hash of these components, ensuring uniqueness
    while maintaining determinism.
    
    Usage:
        generator = DefaultIdempotencyKeyGenerator()
        key = generator.generate_key(args, ctx, spec)
    
    Note:
        This is the default strategy if no generator is specified in the tool spec.
    """
    
    def generate_key(self, args: Dict[str, Any], ctx: Any, spec: Any) -> str:
        """
        Generate idempotency key using SHA-256 hash of tool ID, context, and args.
        
        Args:
            args: Tool execution arguments
            ctx: Tool context containing user_id, session_id, etc.
            spec: Tool specification containing id and idempotency config
            
        Returns:
            str: SHA-256 hash as hex string (64 characters)
        """
        # Determine which data to include in key
        if spec.idempotency.key_fields:
            key_data = {k: args.get(k) for k in spec.idempotency.key_fields if k in args}
        else:
            key_data = args
        
        # Build key components
        key_components = [
            spec.id,
            str(getattr(ctx, USER_ID, None) or EMPTY_STRING),
            str(getattr(ctx, SESSION_ID, None) or EMPTY_STRING),
            json.dumps(key_data, sort_keys=True)
        ]
        
        # Generate hash
        combined = SEPARATOR.join(key_components)
        return hashlib.sha256(combined.encode()).hexdigest()


class FieldBasedIdempotencyKeyGenerator(IIdempotencyKeyGenerator):
    """
    Field-based idempotency key generator.
    
    This strategy uses only specified fields from the tool arguments to generate
    the key. If key_fields is defined in IdempotencyConfig, only those fields
    are used. This is useful when you want idempotency based on specific
    business logic fields rather than all arguments.
    
    Features:
        - Uses only specified key_fields from config
        - Falls back to all args if no key_fields specified
        - Includes tool ID for isolation
        - Does NOT include user/session IDs (can be added via key_fields)
    
    Usage:
        # In tool spec
        spec.idempotency.key_fields = ['order_id', 'payment_id']
        spec.idempotency_key_generator = FieldBasedIdempotencyKeyGenerator()
        
        # Key will only be based on order_id and payment_id
    
    Use Cases:
        - Payment processing (key by transaction ID)
        - Order fulfillment (key by order ID)
        - User registration (key by email or username)
        - API requests with unique request IDs
    """
    
    def generate_key(self, args: Dict[str, Any], ctx: Any, spec: Any) -> str:
        """
        Generate idempotency key using only specified fields.
        
        Args:
            args: Tool execution arguments
            ctx: Tool context (may be ignored depending on key_fields)
            spec: Tool specification with idempotency.key_fields
            
        Returns:
            str: SHA-256 hash based on specified fields only
        """
        # Extract only specified fields
        if spec.idempotency.key_fields:
            key_data = {k: args.get(k) for k in spec.idempotency.key_fields if k in args}
        else:
            # No fields specified, use all args
            key_data = args
        
        # Build key components (tool ID + field data only)
        key_components = [
            spec.id,
            json.dumps(key_data, sort_keys=True)
        ]
        
        # Generate hash
        combined = SEPARATOR.join(key_components)
        return hashlib.sha256(combined.encode()).hexdigest()


class HashBasedIdempotencyKeyGenerator(IIdempotencyKeyGenerator):
    """
    Hash-based idempotency key generator with configurable algorithm.
    
    This strategy allows selection of different hash algorithms and
    provides more control over what gets included in the hash.
    
    Features:
        - Configurable hash algorithm (sha256, sha512, md5, etc.)
        - Option to include/exclude user context
        - Option to include/exclude session context
        - Deterministic ordering for consistent results
    
    Usage:
        generator = HashBasedIdempotencyKeyGenerator(
            algorithm='sha512',
            include_user_context=True,
            include_session_context=False
        )
        key = generator.generate_key(args, ctx, spec)
    
    Use Cases:
        - High-security scenarios (use SHA-512)
        - Performance-critical scenarios (use MD5, but less secure)
        - Multi-tenant systems (include user context)
        - Stateless APIs (exclude session context)
    """
    
    def __init__(
        self,
        algorithm: str = SHA256_HASH_ALGORITHM,
        include_user_context: bool = True,
        include_session_context: bool = True
    ):
        """
        Initialize hash-based generator with configuration.
        
        Args:
            algorithm: Hash algorithm name ('sha256', 'sha512', 'md5', etc.)
            include_user_context: Whether to include user_id in key
            include_session_context: Whether to include session_id in key
        """
        self.algorithm = algorithm
        self.include_user_context = include_user_context
        self.include_session_context = include_session_context
    
    def generate_key(self, args: Dict[str, Any], ctx: Any, spec: Any) -> str:
        """
        Generate idempotency key using configured hash algorithm.
        
        Args:
            args: Tool execution arguments
            ctx: Tool context
            spec: Tool specification
            
        Returns:
            str: Hash digest as hex string
        """
        # Determine which data to include
        if spec.idempotency.key_fields:
            key_data = {k: args.get(k) for k in spec.idempotency.key_fields if k in args}
        else:
            key_data = args
        
        # Build key components based on configuration
        key_components = [spec.id]
        
        if self.include_user_context:
            key_components.append(str(getattr(ctx, USER_ID, None) or EMPTY_STRING))
        
        if self.include_session_context:
            key_components.append(str(getattr(ctx, SESSION_ID, None) or EMPTY_STRING))
        
        key_components.append(json.dumps(key_data, sort_keys=True))
        
        # Generate hash using specified algorithm
        combined = SEPARATOR.join(key_components)
        hash_obj = hashlib.new(self.algorithm, combined.encode())
        return hash_obj.hexdigest()


class CustomIdempotencyKeyGenerator(IIdempotencyKeyGenerator):
    """
    Custom idempotency key generator using user-provided function.
    
    This strategy allows complete control over key generation by accepting
    a custom function. The function receives args, context, and spec, and
    returns a string key.
    
    Features:
        - Complete flexibility in key generation
        - Can access any data from args, context, or spec
        - Can use external services or databases
        - Can implement complex business logic
    
    Usage:
        def my_custom_key(args, ctx, spec):
            # Custom logic here
            timestamp = args.get('timestamp', '')
            user_id = ctx.user_id or 'anonymous'
            return f"{spec.id}:{user_id}:{timestamp}"
        
        generator = CustomIdempotencyKeyGenerator(my_custom_key)
        key = generator.generate_key(args, ctx, spec)
    
    Use Cases:
        - Complex business rules for key generation
        - Integration with external ID generation services
        - Time-based keys with custom expiry logic
        - Geographic or tenant-based key partitioning
    
    Warning:
        The custom function must return deterministic keys (same inputs
        produce same output) for idempotency to work correctly.
    """
    
    def __init__(self, key_function: Callable[[Dict[str, Any], Any, Any], str]):
        """
        Initialize with custom key generation function.
        
        Args:
            key_function: Function that takes (args, ctx, spec) and returns str
        
        Raises:
            TypeError: If key_function is not callable
        """
        if not callable(key_function):
            raise TypeError(KEY_FUNCTION_NOT_CALLABLE)
        
        self.key_function = key_function
    
    def generate_key(self, args: Dict[str, Any], ctx: Any, spec: Any) -> str:
        """
        Generate idempotency key using custom function.
        
        Args:
            args: Tool execution arguments
            ctx: Tool context
            spec: Tool specification
            
        Returns:
            str: Key generated by custom function
            
        Raises:
            Exception: Any exception raised by the custom function
        """
        return self.key_function(args, ctx, spec)


class IdempotencyKeyGeneratorFactory:
    """
    Factory for creating idempotency key generator instances.
    
    This factory provides a centralized way to create and register
    idempotency key generators by name.
    
    Built-in Generators:
        - 'default': DefaultIdempotencyKeyGenerator
        - 'field_based': FieldBasedIdempotencyKeyGenerator
        - 'hash_based': HashBasedIdempotencyKeyGenerator
    
    Usage:
        # Get built-in generator
        generator = IdempotencyKeyGeneratorFactory.get_generator('default')
        
        # Register custom generator
        IdempotencyKeyGeneratorFactory.register('my_custom', MyCustomGenerator())
        generator = IdempotencyKeyGeneratorFactory.get_generator('my_custom')
    """
    
    _generators: Dict[str, IIdempotencyKeyGenerator] = {
        DEFAULT_IDEMPOTENCY_KEY_GENERATOR: DefaultIdempotencyKeyGenerator(),
        FIELD_BASED_IDEMPOTENCY_KEY_GENERATOR: FieldBasedIdempotencyKeyGenerator(),
        HASH_BASED_IDEMPOTENCY_KEY_GENERATOR: HashBasedIdempotencyKeyGenerator(),
    }
    
    @classmethod
    def get_generator(cls, name: str = DEFAULT_IDEMPOTENCY_KEY_GENERATOR) -> IIdempotencyKeyGenerator:
        """
        Get an idempotency key generator by name.
        
        Args:
            name: Generator name ('default', 'field_based', 'hash_based', etc.)
            
        Returns:
            IIdempotencyKeyGenerator instance
            
        Raises:
            ValueError: If generator name is not registered
        """
        generator = cls._generators.get(name)
        
        if not generator:
            raise ValueError(
                UNKNOWN_IDEMPOTENCY_KEY_GENERATOR.format(GENERATOR_NAME=name, AVAILABLE_GENERATORS=((COMMA+SPACE).join(cls._generators.keys())))
            )
        
        return generator
    
    @classmethod
    def register(cls, name: str, generator: IIdempotencyKeyGenerator):
        """
        Register a custom idempotency key generator.
        
        Args:
            name: Name to register the generator under
            generator: Generator instance implementing IIdempotencyKeyGenerator
        
        Example:
            class MyGenerator(IIdempotencyKeyGenerator):
                def generate_key(self, args, ctx, spec):
                    return f"custom-{args['id']}"
            
            IdempotencyKeyGeneratorFactory.register('my_gen', MyGenerator())
        """
        cls._generators[name] = generator

