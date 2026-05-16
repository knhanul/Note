"""Seed AI prompt documents and built-in action bindings."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .ai_prompt_repository import PromptRepository

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{([A-Z_]+)\}\}")


@dataclass(frozen=True)
class SeedPromptSpec:
    prompt_doc_id: str
    title: str
    description: str
    source_file: str
    required_variables: tuple[str, ...]
    sort_order: int


class PromptSeedService:
    """Seeds default prompts and built-in actions into the AI prompt database."""

    DB_FILENAME = "ai_prompts.db"
    DB_VERSION = "1"

    DEFAULT_PROMPTS: tuple[SeedPromptSpec, ...] = (
        SeedPromptSpec("summarize_note", "문서 요약", "현재 문서를 간단히 요약합니다.", "summarize_note.md", ("CONTENT",), 10),
        SeedPromptSpec("polish_selection", "문장 다듬기", "선택된 텍스트나 문서 내용을 자연스럽게 다듬습니다.", "polish_selection.md", ("CONTENT",), 20),
        SeedPromptSpec("extract_todo", "할 일 추출", "문서에서 해야 할 일을 추출합니다.", "extract_todo.md", ("CONTENT",), 30),
        SeedPromptSpec("suggest_title_tags", "제목/태그 추천", "문서에 어울리는 제목과 태그를 추천합니다.", "suggest_title_tags.md", ("CONTENT",), 40),
        SeedPromptSpec("current_note_qa", "현재 문서 질문", "현재 문서와 검색 문단을 참고해 질문에 답변합니다.", "current_note_qa.md", ("CONTEXT", "QUESTION"), 50),
    )

    DEFAULT_ACTIONS: tuple[dict, ...] = (
        {
            "action_id": "summarize_note",
            "name": "문서 요약",
            "description": "현재 문서를 간단히 요약합니다.",
            "category": "문서 처리",
            "required_variables_json": json.dumps(["CONTENT"], ensure_ascii=False),
            "enabled": 1,
            "sort_order": 10,
        },
        {
            "action_id": "polish_selection",
            "name": "문장 다듬기",
            "description": "선택된 텍스트를 자연스럽게 다듬습니다.",
            "category": "문서 처리",
            "required_variables_json": json.dumps(["CONTENT"], ensure_ascii=False),
            "enabled": 1,
            "sort_order": 20,
        },
        {
            "action_id": "extract_todo",
            "name": "할 일 추출",
            "description": "문서에서 할 일을 추출합니다.",
            "category": "문서 처리",
            "required_variables_json": json.dumps(["CONTENT"], ensure_ascii=False),
            "enabled": 1,
            "sort_order": 30,
        },
        {
            "action_id": "suggest_title_tags",
            "name": "제목/태그 추천",
            "description": "문서의 제목과 태그를 추천합니다.",
            "category": "문서 처리",
            "required_variables_json": json.dumps(["CONTENT"], ensure_ascii=False),
            "enabled": 1,
            "sort_order": 40,
        },
        {
            "action_id": "current_note_qa",
            "name": "현재 문서 질문",
            "description": "현재 문서와 검색 문단을 참고하여 답변합니다.",
            "category": "문서 질문",
            "required_variables_json": json.dumps(["CONTEXT", "QUESTION"], ensure_ascii=False),
            "enabled": 1,
            "sort_order": 50,
        },
    )

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None):
        self._app_data_dir = Path(app_data_dir)
        self._prompt_dir = self._app_data_dir / "ai"
        self._db_path = self._prompt_dir / self.DB_FILENAME
        self._package_prompt_dir = prompt_package_dir or Path(__file__).parent / "prompts"
        self._repo = PromptRepository(self._db_path)

    @property
    def repository(self) -> PromptRepository:
        return self._repo

    @property
    def db_path(self) -> Path:
        return self._db_path

    def ensure_seeded(self) -> PromptRepository:
        self._repo.ensure_schema()
        for action in self.DEFAULT_ACTIONS:
            self._repo.upsert_action(action)
        self._seed_prompt_documents()
        self._seed_bindings()
        return self._repo

    def _seed_bindings(self) -> None:
        for action in self.DEFAULT_ACTIONS:
            self._repo.reset_binding(action["action_id"])

    def _seed_prompt_documents(self) -> None:
        for prompt in self.DEFAULT_PROMPTS:
            source_path = self._package_prompt_dir / prompt.source_file
            if not source_path.exists():
                logger.warning(f"[PromptSeedService] Missing default prompt file: {source_path}")
                continue

            content_md = source_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content_md.encode("utf-8")).hexdigest()
            variables = sorted(set(VARIABLE_PATTERN.findall(content_md)))
            existing = self._repo.get_prompt_document(prompt.prompt_doc_id)

            if existing and existing.get("source_type") == "default" and existing.get("content_hash") == content_hash:
                continue

            self._repo.upsert_prompt_document({
                "prompt_doc_id": prompt.prompt_doc_id,
                "title": prompt.title,
                "description": prompt.description,
                "content_md": content_md,
                "source_type": "default",
                "readonly": 1,
                "archived": 0,
                "variables_json": json.dumps(variables, ensure_ascii=False),
                "content_hash": content_hash,
            })

    def seed_from_package_files(self) -> PromptRepository:
        return self.ensure_seeded()
