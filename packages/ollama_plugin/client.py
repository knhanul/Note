"""Network-free Ollama client stub."""

from .settings import OllamaSettings


class OllamaClient:
    def __init__(self, settings: OllamaSettings | None = None) -> None:
        self.settings = settings or OllamaSettings()

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Ollama generate is not implemented in the stub stage.")

    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError("Ollama chat is not implemented in the stub stage.")

    def list_models(self) -> list[str]:
        return []
