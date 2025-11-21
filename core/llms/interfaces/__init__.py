"""
Interfaces for LLM Subsystem.

This module exports all interface protocols for the LLM subsystem.
"""

from .llm_interfaces import (
    ILLM,
    IConnector,
    IModelRegistry,
    Messages,
    Parameters,
)

__all__ = [
    "ILLM",
    "IConnector",
    "IModelRegistry",
    "Messages",
    "Parameters",
]

