"""Ollama server health and model availability checks."""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OllamaHealthResult:
    """Result of an Ollama health check."""

    reachable: bool
    server_ok: bool
    model_available: Optional[bool] = None
    message: str = ""
    base_url: str = ""
    details: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.reachable and self.server_ok

    @property
    def is_ready(self, model: Optional[str] = None) -> bool:
        if model and self.model_available is not None:
            return self.is_healthy and self.model_available
        return self.is_healthy


def _request_tags(base_url: str, timeout_sec: float) -> tuple[bool, dict, str]:
    """Call /api/tags and return (success, parsed_json, error_message)."""
    url = f"{base_url.rstrip('/')}/api/tags"
    request = urllib.request.Request(url, method="GET")
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            body = response.read().decode("utf-8")
            if response.status != 200:
                return False, {}, f"HTTP {response.status}: {body[:200]}"
            data = json.loads(body)
            return True, data, ""
    except urllib.error.URLError as e:
        reason = str(getattr(e, "reason", e))
        logger.warning(f"Ollama health check failed ({base_url}): {reason}")
        return False, {}, reason
    except json.JSONDecodeError as e:
        logger.warning(f"Ollama health check returned invalid JSON ({base_url}): {e}")
        return False, {}, f"Invalid JSON response: {e}"
    except TimeoutError as e:
        logger.warning(f"Ollama health check timed out ({base_url}): {e}")
        return False, {}, "Health check timed out"
    except Exception as e:
        logger.warning(f"Ollama health check unexpected error ({base_url}): {e}")
        return False, {}, f"Unexpected error: {e}"


def check_ollama_health(base_url: str = "http://localhost:11434", timeout_sec: float = 5.0) -> OllamaHealthResult:
    """Check if Ollama server is reachable and responding.

    Pings ``/api/tags`` (which is also used by ``ollama list``). If it returns
    HTTP 200 with a valid JSON body, the server is considered healthy.
    """
    success, data, error = _request_tags(base_url, timeout_sec)

    if not success:
        return OllamaHealthResult(
            reachable=False,
            server_ok=False,
            message="Ollama 서버가 실행되지 않았습니다.",
            base_url=base_url,
            details=error,
        )

    if not isinstance(data, dict) or "models" not in data:
        return OllamaHealthResult(
            reachable=True,
            server_ok=False,
            message="Ollama 서버가 응답하지만 예상치 못한 응답을 반환했습니다.",
            base_url=base_url,
            details=f"Response missing 'models' field: {json.dumps(data)[:200]}",
        )

    return OllamaHealthResult(
        reachable=True,
        server_ok=True,
        message="Ollama 서버가 정상입니다.",
        base_url=base_url,
        details=f"{len(data.get('models', []))} models available",
    )


def check_ollama_model_available(
    base_url: str, model: str, timeout_sec: float = 5.0
) -> OllamaHealthResult:
    """Check if Ollama server is reachable and a specific model is installed.

    Parses the ``/api/tags`` response and looks for ``model`` in the list of
    installed models. The comparison accepts both exact name and tag-less
    prefix (e.g. ``gemma-2b`` matches ``gemma-2b:latest``).
    """
    if not model:
        return OllamaHealthResult(
            reachable=False,
            server_ok=False,
            message="확인할 모델 이름이 없습니다.",
            base_url=base_url,
        )

    success, data, error = _request_tags(base_url, timeout_sec)

    if not success:
        return OllamaHealthResult(
            reachable=False,
            server_ok=False,
            message="Ollama 서버가 실행되지 않았습니다.",
            base_url=base_url,
            details=error,
        )

    models = data.get("models", []) if isinstance(data, dict) else []
    installed_names = [m.get("name", "") for m in models if isinstance(m, dict)]
    model_lower = model.lower()

    for name in installed_names:
        if name.lower() == model_lower:
            return OllamaHealthResult(
                reachable=True,
                server_ok=True,
                model_available=True,
                message=f"모델 '{model}'을(를) 사용할 수 있습니다.",
                base_url=base_url,
                details=f"Installed models: {installed_names}",
            )
        # Also accept prefix without tag, e.g. "llama3.2:3b" matches "llama3.2:3b:latest"
        base_name = name.split(":", 1)[0].lower()
        if base_name == model_lower.split(":", 1)[0]:
            return OllamaHealthResult(
                reachable=True,
                server_ok=True,
                model_available=True,
                message=f"모델 '{model}'을(를) 사용할 수 있습니다(실제 이름: {name}).",
                base_url=base_url,
                details=f"Installed models: {installed_names}",
            )

    return OllamaHealthResult(
        reachable=True,
        server_ok=True,
        model_available=False,
        message=f"모델 '{model}'이(가) 설치되지 않았습니다.",
        base_url=base_url,
        details=f"Installed models: {installed_names}",
    )
