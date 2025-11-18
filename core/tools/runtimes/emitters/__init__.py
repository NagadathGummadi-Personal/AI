"""
Event emitters for the tools system.

Provides event emission implementations for tracking tool execution events.
"""

from .noop_emitter import NoOpEmitter

__all__ = [
    "NoOpEmitter",
]

