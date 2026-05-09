"""Ollama assistant plugin stub."""

from packages.plugin_api import Command

from .actions import mock_answer_selection, mock_summarize_document, mock_work_assist
from .client import OllamaClient
from .settings import OllamaSettings


class OllamaAssistantPlugin:
    id = "ollama.assistant"
    name = "Ollama Assistant Stub"
    version = "0.1.0"

    def __init__(self, settings: OllamaSettings | None = None) -> None:
        self.settings = settings or OllamaSettings()
        self.client = OllamaClient(self.settings)
        self.activated = False

    def activate(self, context) -> None:
        self.activated = True
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

    def deactivate(self) -> None:
        self.activated = False
