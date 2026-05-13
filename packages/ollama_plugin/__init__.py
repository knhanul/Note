"""Ollama plugin stub package for future work AI editor features."""

from .action_registry import ActionRegistry, AIAction
from .ai_controller import AIAssistantController
from .ai_settings import AISettings, AISettingsManager
from .ai_worker import AIWorker, AIWorkerManager
from .assistant_controller import AssistantController
from .client import OllamaClient, OllamaConnectionResult, OllamaModel, OllamaModelListResult
from .model_manager import ModelManager
from .plugin import OllamaAssistantPlugin
from .prompt_manager import PromptManager
from .prompt_renderer import PromptRenderer
from .settings import OllamaSettings

__all__ = [
    "OllamaAssistantPlugin",
    "OllamaClient",
    "OllamaSettings",
    "OllamaConnectionResult",
    "OllamaModel",
    "OllamaModelListResult",
    "ModelManager",
    "AISettings",
    "AISettingsManager",
    "AIAssistantController",
    "AssistantController",
    "AIWorker",
    "AIWorkerManager",
    "ActionRegistry",
    "AIAction",
    "PromptManager",
    "PromptRenderer",
]
