import json
import urllib.request
import urllib.error
from typing import Any

from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_prompt_builder import RagPromptPayload


class OllamaLlmClient(LlmClient):
    def __init__(
        self, base_url: str = "http://localhost:11434", default_model: str = "llama3.2:3b"
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

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

            with urllib.request.urlopen(request, timeout=options.timeout_sec) as response:
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
            warnings.append("[OLLAMA_CONNECTION_FAILED]")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

        except TimeoutError as e:
            warnings.append("[OLLAMA_TIMEOUT]")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

        except json.JSONDecodeError as e:
            warnings.append("[OLLAMA_INVALID_JSON]")
            return LlmGenerateResult(
                text="",
                model=options.model,
                provider="ollama",
                raw=raw_response,
                warnings=warnings,
            )

        except Exception as e:
            warnings.append("[OLLAMA_GENERATE_FAILED]")
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
