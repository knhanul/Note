"""Ollama plugin stub package for future work AI editor features."""

from .client import OllamaClient
from .plugin import OllamaAssistantPlugin
from .settings import OllamaSettings

__all__ = [
    "OllamaAssistantPlugin",
    "OllamaClient",
    "OllamaSettings",
]
