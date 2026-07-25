from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class LlmGenerateOptions:
    model: str
    temperature: float = 0.2
    top_p: float | None = None
    max_tokens: int | None = None
    timeout_sec: float = 60.0
    on_token: Optional[Callable[[str], None]] = None


@dataclass
class LlmGenerateResult:
    text: str
    model: str
    provider: str
    raw: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)


class LlmClient:
    """Abstract LLM client interface."""

    def generate(
        self, system_prompt: str, user_prompt: str, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        raise NotImplementedError("Subclass must implement generate()")
