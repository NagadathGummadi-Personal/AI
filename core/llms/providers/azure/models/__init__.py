"""
Azure OpenAI Models.

Model-specific configurations and implementations for Azure OpenAI.
"""

from .gpt41_mini import GPT41MiniMetadata, GPT41MiniLLM

__all__ = [
    "GPT41MiniMetadata",
    "GPT41MiniLLM",
]

