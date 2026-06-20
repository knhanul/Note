import json
import logging
import urllib.request
import urllib.error
from typing import Any

from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_prompt_builder import RagPromptPayload
from services.ollama_health import (
    OllamaHealthResult,
    check_ollama_health,
    check_ollama_model_available,
)

logger = logging.getLogger(__name__)


class OllamaLlmClient(LlmClient):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.2:3b",
        health_timeout_sec: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.health_timeout_sec = health_timeout_sec

    def check_health(self) -> OllamaHealthResult:
        """Check if Ollama server is reachable and responding."""
        return check_ollama_health(self.base_url, timeout_sec=self.health_timeout_sec)

    def check_model(self, model: str) -> OllamaHealthResult:
        """Check if the given model is installed on the Ollama server."""
        return check_ollama_model_available(
            self.base_url, model, timeout_sec=self.health_timeout_sec
        )

    def generate(
        self, system_prompt: str, user_prompt: str, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        if options is None:
            options = LlmGenerateOptions(model=self.default_model)

        payload: dict[str, Any] = {
            "model": options.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
        }

        if options.temperature is not None:
            payload.setdefault("options", {})["temperature"] = options.temperature

        if options.top_p is not None:
            payload.setdefault("options", {})["top_p"] = options.top_p

        if options.max_tokens is not None:
            payload.setdefault("options", {})["num_predict"] = options.max_tokens

        warnings: list[str] = []
        raw_response: dict[str, Any] | None = None

        try:
            url = f"{self.base_url}/api/generate"
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                url, data=data, method="POST", headers={"Content-Type": "application/json"}
            )

            timeout = options.timeout_sec if options.timeout_sec is not None else 60.0
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
                text = raw_response.get("response", "")

                if not text:
                    warnings.append("[OLLAMA_EMPTY_RESPONSE]")

                model_name = raw_response.get("model", options.model)

                return LlmGenerateResult(
                    text=text,
                    model=model_name,
                    provider="ollama",
                    raw=raw_response,
                    warnings=warnings,
                )

        except urllib.error.URLError as e:
            logger.error(f"[OllamaLlmClient] URLError during generation: {e}")
            warnings.append("[OLLAMA_CONNECTION_FAILED]")
            warnings.append("Ollama 서버가 실행되지 않았습니다.")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

        except TimeoutError as e:
            logger.error(f"[OllamaLlmClient] Timeout during generation: {e}")
            warnings.append("[OLLAMA_TIMEOUT]")
            warnings.append("AI 응답 시간이 초과되었습니다. 더 가벼운 모델을 선택하거나 입력 길이를 줄여 다시 시도해보세요.")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

        except json.JSONDecodeError as e:
            logger.error(f"[OllamaLlmClient] Invalid JSON response: {e}")
            warnings.append("[OLLAMA_INVALID_JSON]")
            warnings.append("Ollama 서버의 응답을 해석할 수 없습니다.")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"[OllamaLlmClient] Unexpected error during generation: {e}")
            warnings.append("[OLLAMA_GENERATE_FAILED]")
            warnings.append(f"Ollama 호출 중 오류가 발생했습니다: {e}")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

    def generate_from_payload(
        self, payload: RagPromptPayload, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        return self.generate(payload.system_prompt, payload.user_prompt, options)
