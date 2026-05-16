"""Seed service for bootstrapping AI prompts and actions into SQLite."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .prompt_repository import PromptRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeedPromptSpec:
    prompt_id: str
    title: str
    description: str
    version: str
    source_file: str
    variables: list[str]


class PromptSeedService:
    """Seeds default prompts and built-in actions into the prompt database."""

    DB_FILENAME = "ai_prompts.db"
    DB_VERSION = "1"

    DEFAULT_PROMPTS: tuple[SeedPromptSpec, ...] = (
        SeedPromptSpec("summarize_note", "문서 요약", "현재 문서를 간단히 요약합니다.", "1.0.0", "summarize_note.md", ["CONTENT"]),
        SeedPromptSpec("polish_selection", "문장 다듬기", "선택된 텍스트나 문서 내용을 자연스럽게 다듬습니다.", "1.0.0", "polish_selection.md", ["CONTENT"]),
        SeedPromptSpec("extract_todo", "할 일 추출", "문서에서 해야 할 일을 추출합니다.", "1.0.0", "extract_todo.md", ["CONTENT"]),
        SeedPromptSpec("suggest_title_tags", "제목/태그 추천", "문서에 어울리는 제목과 태그를 추천합니다.", "1.0.0", "suggest_title_tags.md", ["CONTENT"]),
        SeedPromptSpec("current_note_qa", "현재 문서 질문", "현재 문서와 검색 문단을 참고해 질문에 답변합니다.", "1.0.0", "current_note_qa.md", ["CONTEXT", "QUESTION"]),
    )

    DEFAULT_ACTIONS: tuple[dict, ...] = (
        {
            "action_id": "summarize_note",
            "name": "문서 요약",
            "description": "현재 문서를 간단히 요약합니다.",
            "category": "문서 처리",
            "prompt_id": "summarize_note",
            "input_scope": "current_note",
            "output_mode": "text",
            "enabled": 1,
            "built_in": 1,
            "sort_order": 10,
        },
        {
            "action_id": "polish_selection",
            "name": "문장 다듬기",
            "description": "선택된 텍스트를 자연스럽게 다듬습니다.",
            "category": "문서 처리",
            "prompt_id": "polish_selection",
            "input_scope": "current_note",
            "output_mode": "text",
            "enabled": 1,
            "built_in": 1,
            "sort_order": 20,
        },
        {
            "action_id": "extract_todo",
            "name": "할 일 추출",
            "description": "문서에서 할 일을 추출합니다.",
            "category": "문서 처리",
            "prompt_id": "extract_todo",
            "input_scope": "current_note",
            "output_mode": "markdown_checklist",
            "enabled": 1,
            "built_in": 1,
            "sort_order": 30,
        },
        {
            "action_id": "suggest_title_tags",
            "name": "제목/태그 추천",
            "description": "문서의 제목과 태그를 추천합니다.",
            "category": "문서 처리",
            "prompt_id": "suggest_title_tags",
            "input_scope": "current_note",
            "output_mode": "structured",
            "enabled": 1,
            "built_in": 1,
            "sort_order": 40,
        },
        {
            "action_id": "current_note_qa",
            "name": "현재 문서 질문",
            "description": "현재 문서와 검색 문단을 참고하여 답변합니다.",
            "category": "문서 질문",
            "prompt_id": "current_note_qa",
            "input_scope": "current_note_with_query",
            "output_mode": "text",
            "enabled": 1,
            "built_in": 1,
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
        self._repo.set_meta("schema_version", self.DB_VERSION)
        self._seed_actions()
        self._seed_prompts()
        return self._repo

    def _seed_actions(self) -> None:
        for action in self.DEFAULT_ACTIONS:
            existing = self._repo.get_action(action["action_id"])
            if not existing:
                self._repo.upsert_action(action)
                continue

            if existing.get("prompt_id") != action["prompt_id"] or existing.get("name") != action["name"]:
                self._repo.upsert_action(action)

    def _seed_prompts(self) -> None:
        for prompt in self.DEFAULT_PROMPTS:
            source_path = self._package_prompt_dir / prompt.source_file
            if not source_path.exists():
                logger.warning(f"[PromptSeedService] Missing default prompt file: {source_path}")
                continue

            content_md = source_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content_md.encode("utf-8")).hexdigest()
            variables_json = json.dumps(prompt.variables, ensure_ascii=False)

            current_default = self._repo.get_active_default(prompt.prompt_id)
            if current_default and current_default.get("content_hash") == content_hash:
                continue

            default_versions = self._repo.list_default_versions(prompt.prompt_id)
            existing_versions = {row.get("version") for row in default_versions}
            version_to_use = prompt.version

            if version_to_use in existing_versions:
                version_to_use = f"{prompt.version}+{content_hash[:8]}"

            self._repo.insert_default_version(
                {
                    "prompt_id": prompt.prompt_id,
                    "version": version_to_use,
                    "title": prompt.title,
                    "description": prompt.description,
                    "content_md": content_md,
                    "variables_json": variables_json,
                    "content_hash": content_hash,
                    "is_active": 1,
                },
                active=True,
            )

    def seed_from_package_files(self) -> PromptRepository:
        return self.ensure_seeded()
