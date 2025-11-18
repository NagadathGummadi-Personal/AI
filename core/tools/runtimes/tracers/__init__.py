"""
Tracer implementations for the tools system.

Provides distributed tracing implementations for observability.
"""

from .noop_tracer import NoOpTracer

__all__ = [
    "NoOpTracer",
]

