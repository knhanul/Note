"""Settings structures for the Ollama plugin stub."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = "http://localhost:11434"
    model_name: str = ""
    timeout_sec: int = 30
