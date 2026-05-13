"""Ollama client for local LLM operations."""

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OllamaConnectionResult:
    success: bool
    message: str
    base_url: str = ""


@dataclass
class OllamaModel:
    name: str
    size: int = 0
    modified_at: str = ""


@dataclass
class OllamaModelListResult:
    success: bool
    models: list[OllamaModel]
    error: str = ""


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout_sec: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def check_connection(self) -> OllamaConnectionResult:
        """Check if Ollama server is running."""
        try:
            url = f"{self.base_url}/api/tags"
            request = urllib.request.Request(url, method="GET")
            request.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    return OllamaConnectionResult(
                        success=True,
                        message="연결됨",
                        base_url=self.base_url
                    )
                else:
                    return OllamaConnectionResult(
                        success=False,
                        message=f"연결 실패: {response.status}",
                        base_url=self.base_url
                    )
        except urllib.error.URLError as e:
            return OllamaConnectionResult(
                success=False,
                message="연결 안 됨",
                base_url=self.base_url
            )
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e}")
            return OllamaConnectionResult(
                success=False,
                message=f"오류: {str(e)}",
                base_url=self.base_url
            )

    def list_models(self) -> OllamaModelListResult:
        """List installed Ollama models."""
        try:
            url = f"{self.base_url}/api/tags"
            request = urllib.request.Request(url, method="GET")
            request.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = []
                    for model in data.get("models", []):
                        models.append(OllamaModel(
                            name=model.get("name", ""),
                            size=model.get("size", 0),
                            modified_at=model.get("modified_at", "")
                        ))
                    return OllamaModelListResult(
                        success=True,
                        models=models,
                        error=""
                    )
                else:
                    return OllamaModelListResult(
                        success=False,
                        models=[],
                        error=f"Failed to list models: {response.status}"
                    )
        except urllib.error.URLError as e:
            return OllamaModelListResult(
                success=False,
                models=[],
                error="연결 안 됨"
            )
        except Exception as e:
            logger.error(f"Ollama list models failed: {e}")
            return OllamaModelListResult(
                success=False,
                models=[],
                error=str(e)
            )

    def generate(self, prompt: str, model: str) -> str:
        """Generate text using Ollama (not implemented for stage 3)."""
        raise NotImplementedError("Generate is not implemented in stage 3.")

    def chat(self, messages: list[dict], model: str) -> str:
        """Chat with Ollama (not implemented for stage 3)."""
        raise NotImplementedError("Chat is not implemented in stage 3.")
