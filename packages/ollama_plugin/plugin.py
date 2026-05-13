"""Ollama assistant plugin stub."""

import logging

from packages.plugin_api import Command, SidebarPanel

from .mock_actions import mock_answer_selection, mock_summarize_document, mock_work_assist
from .client import OllamaClient
from .settings import OllamaSettings

logger = logging.getLogger(__name__)


class OllamaAssistantPlugin:
    id = "ollama.assistant"
    name = "Ollama Assistant Stub"
    version = "0.1.0"

    def __init__(self, settings: OllamaSettings | None = None) -> None:
        self.settings = settings or OllamaSettings()
        self.client = OllamaClient(base_url=self.settings.base_url, timeout_sec=self.settings.timeout_sec)
        self.activated = False

    def activate(self, context) -> None:
        self.activated = True
        logger.info(f"[OllamaAssistantPlugin] Activating plugin: {self.id} v{self.version}")

        context.register_command(
            Command(
                id="ollama.assistant.mock_summarize",
                title="Mock Summarize Document",
                handler=mock_summarize_document,
                description="Stub command that does not call Ollama.",
            )
        )
        context.register_command(
            Command(
                id="ollama.assistant.mock_answer_selection",
                title="Mock Answer Selection",
                handler=mock_answer_selection,
                description="Stub command that does not call Ollama.",
            )
        )
        context.register_command(
            Command(
                id="ollama.assistant.mock_work_assist",
                title="Mock Work Assist",
                handler=mock_work_assist,
                description="Stub command that does not call Ollama.",
            )
        )

        context.register_sidebar_panel(
            SidebarPanel(
                id="ollama.assistant.panel",
                title="AI 업무비서",
                component=None,
                factory=None,
            )
        )

        logger.info("[OllamaAssistantPlugin] Plugin activated successfully")

    def deactivate(self) -> None:
        logger.info(f"[OllamaAssistantPlugin] Deactivating plugin: {self.id}")
        self.activated = False
