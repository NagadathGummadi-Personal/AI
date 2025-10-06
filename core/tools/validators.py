"""
Validator Implementations for Tools Specification System

This module provides concrete implementations of the IToolValidator interface,
including the BasicValidator with comprehensive parameter validation.
"""

import json
import re
from typing import Any, Dict
from .tool_types import ToolSpec
#Tool Parameters
from .tool_parameters import ToolParameter, StringParameter, NumericParameter, BooleanParameter, ArrayParameter, ObjectParameter
#Tool Errors
from .tool_result import ToolError


class BasicValidator:
    """Basic implementation of IToolValidator with comprehensive validation"""

    PY_TYPES = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": (list, tuple),
        "object": dict,
    }

    async def validate(self, args: Dict[str, Any], spec: ToolSpec) -> None:
        """Validate tool arguments against the specification"""
        allowed_names = {p.name for p in spec.parameters}
        unknown = set(args.keys()) - allowed_names
        if unknown:
            raise ToolError(f"Unknown parameter(s): {sorted(unknown)}", retryable=False, code="VALIDATION_ERROR")

        for p in spec.parameters:
            if p.required and p.name not in args:
                raise ToolError(f"Missing required parameter: {p.name}", retryable=False, code="VALIDATION_ERROR")
            if p.name in args:
                value = args[p.name]
                if not self._validate_param(value, p):
                    raise ToolError(f"Parameter '{p.name}' failed validation", retryable=False, code="VALIDATION_ERROR")

    def _validate_param(self, value: Any, p: ToolParameter) -> bool:
        """Validate a single parameter value"""
        # Handle different parameter types
        if isinstance(p, StringParameter):
            return self._validate_string_param(value, p)
        elif isinstance(p, NumericParameter):
            return self._validate_numeric_param(value, p)
        elif isinstance(p, BooleanParameter):
            return self._validate_boolean_param(value, p)
        elif isinstance(p, ArrayParameter):
            return self._validate_array_param(value, p)
        elif isinstance(p, ObjectParameter):
            return self._validate_object_param(value, p)
        else:
            # Fallback for base ToolParameter
            return True

    def _validate_string_param(self, value: Any, p: StringParameter) -> bool:
        """Validate string parameter"""
        # Enum validation
        if p.enum is not None and value not in p.enum:
            return False

        # Type coercion and validation
        if not isinstance(value, str):
            if p.coerce:
                try:
                    str(value)  # Try to coerce to string
                except (ValueError, TypeError):
                    return False
            else:
                return False

        s = str(value)

        # Length constraints
        if p.min_length is not None and len(s) < p.min_length:
            return False
        if p.max_length is not None and len(s) > p.max_length:
            return False

        # Pattern validation
        if p.pattern and not re.fullmatch(p.pattern, s):
            return False

        return True

    def _validate_numeric_param(self, value: Any, p: NumericParameter) -> bool:
        """Validate numeric parameter"""
        # Type validation
        if not isinstance(value, (int, float)):
            return False

        fval = float(value)

        # Range constraints
        if p.min is not None and fval < p.min:
            return False
        if p.max is not None and fval > p.max:
            return False

        return True

    def _validate_boolean_param(self, value: Any, p: BooleanParameter) -> bool:
        """Validate boolean parameter"""
        return isinstance(value, bool)

    def _validate_array_param(self, value: Any, p: ArrayParameter) -> bool:
        """Validate array parameter"""
        if not isinstance(value, (list, tuple)):
            return False

        # Length constraints
        if p.min_items is not None and len(value) < p.min_items:
            return False
        if p.max_items is not None and len(value) > p.max_items:
            return False

        # Unique items
        if p.unique_items and len(set(map(json.dumps, value))) != len(value):
            return False

        # Item validation
        if p.items:
            return all(self._validate_param(v, p.items) for v in value)

        return True

    def _validate_object_param(self, value: Any, p: ObjectParameter) -> bool:
        """Validate object parameter"""
        if not isinstance(value, dict):
            return False

        # Additional object validation could be added here
        # For now, we just check the basic type
        return True

    def _try_coerce(self, value: Any, target_type: str) -> Any | None:
        """Attempt to coerce a value to the target type"""
        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                if isinstance(value, str):
                    return int(float(value))  # Handle "123.0" -> 123
                return int(value)
            elif target_type == "number":
                return float(value)
            elif target_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
        except (ValueError, TypeError):
            return None
        return None
