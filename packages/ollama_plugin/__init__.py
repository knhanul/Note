"""Ollama plugin stub package for future work AI editor features.

AUTHORITATIVE RUNTIME PATH:
- Current AI execution prompt resolution uses ai_prompt_service.PromptService
- Action-to-prompt bindings are managed in ai_action_prompt_bindings table
- Prompt documents are stored in ai_prompt_documents table
- AssistantController -> ai_prompt_service -> ai_prompt_repository is the active execution path

LEGACY MODULES:
- The following legacy prompt_* modules remain as files but are no longer publicly exported
  and are NOT authoritative for current AI runtime execution:
  - prompt_service.py
  - prompt_controller.py
  - prompt_seed_service.py
  - prompt_repository.py
- DO NOT use these for new AI prompt resolution logic
"""

from .action_registry import ActionRegistry, AIAction
from .ai_controller import AIAssistantController
from .ai_prompt_controller import PromptController
from .ai_prompt_document_controller import AIPromptDocumentController
from .ai_action_controller import AIActionController
from .ai_prompt_repository import PromptRepository
from .ai_prompt_seed_service import PromptSeedService
from .ai_prompt_service import PromptService
from .ai_settings import AISettings, AISettingsManager
from .ai_worker import AIWorker, AIWorkerManager
from .assistant_controller import AssistantController
from .client import OllamaClient, OllamaConnectionResult, OllamaModel, OllamaModelListResult
from .model_manager import ModelManager
from .plugin import OllamaAssistantPlugin
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
    "PromptController",
    "AIPromptDocumentController",
    "AIActionController",
    "PromptRepository",
    "PromptSeedService",
    "PromptService",
    "PromptRenderer",
]
