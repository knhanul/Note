"""High-level AI prompt service used by controllers and UI."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .prompt_repository import PromptRepository
from .prompt_seed_service import PromptSeedService
from .prompt_renderer import PromptRenderer

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{([A-Z_]+)\}\}")


@dataclass
class PromptRecord:
    prompt_id: str
    title: str
    description: str
    category: str
    content_md: str
    variables: list[str]
    has_override: bool
    update_available: bool
    base_version: str
    default_version: str
    enabled: bool


class PromptService:
    """Business logic for prompt listing, retrieval and override handling."""

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None):
        self._seed_service = PromptSeedService(app_data_dir, prompt_package_dir)
        self._repo: PromptRepository = self._seed_service.ensure_seeded()
        self._renderer = PromptRenderer()

    @property
    def repository(self) -> PromptRepository:
        return self._repo

    def list_prompts(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for summary in self._repo.list_prompt_summaries():
            action = summary["action"]
            default = summary.get("default")
            override = summary.get("override")
            effective = override if override else default

            if not effective:
                continue

            default_hash = default.get("content_hash") if default else ""
            override_hash = override.get("content_hash") if override else ""
            update_available = bool(default and override and default_hash and override_hash and default_hash != override_hash)

            results.append({
                "prompt_id": action["prompt_id"],
                "action_id": action["action_id"],
                "name": action["name"],
                "description": effective.get("description") or action.get("description") or "",
                "category": action.get("category") or "기본",
                "content_md": effective.get("content_md", ""),
                "variables": self._parse_variables(effective.get("variables_json"), effective.get("content_md", "")),
                "has_override": bool(override),
                "update_available": update_available,
                "base_version": override.get("base_version") if override else "",
                "default_version": default.get("version") if default else "",
                "enabled": bool(override.get("enabled", 1) if override else 1),
                "title": effective.get("title") or action["name"],
            })
        return results

    def get_prompt(self, prompt_id: str) -> str:
        record = self._get_effective_record(prompt_id)
        return record["content_md"] if record else ""

    def get_effective_prompt(self, prompt_id: str) -> str:
        return self.get_prompt(prompt_id)

    def save_override(self, prompt_id: str, content_md: str) -> bool:
        summary = self._repo.get_prompt_summary(prompt_id)
        if not summary:
            logger.warning(f"[PromptService] Prompt not found: {prompt_id}")
            return False

        action = summary["action"]
        default = summary.get("default")
        base_version = default.get("version") if default else ""
        variables = self._extract_variables(content_md)
        variables_json = json.dumps(variables, ensure_ascii=False)
        content_hash = hashlib.sha256(content_md.encode("utf-8")).hexdigest()

        self._repo.upsert_override({
            "prompt_id": prompt_id,
            "base_version": base_version,
            "title": action["name"],
            "content_md": content_md,
            "variables_json": variables_json,
            "content_hash": content_hash,
            "enabled": 1,
        })
        self._repo.insert_history(prompt_id, "override", base_version, content_md)
        return True

    def reset_to_default(self, prompt_id: str) -> bool:
        summary = self._repo.get_prompt_summary(prompt_id)
        if not summary:
            return False

        default = summary.get("default")
        if not default:
            return False

        self._repo.disable_override(prompt_id)
        self._repo.insert_history(prompt_id, "reset", default.get("version"), default.get("content_md", ""))
        return True

    def get_prompt_details(self, prompt_id: str) -> dict[str, Any] | None:
        record = self._get_effective_record(prompt_id)
        if not record:
            return None

        return {
            "prompt_id": prompt_id,
            "title": record.get("title", ""),
            "description": record.get("description", ""),
            "content_md": record.get("content_md", ""),
            "variables": self._parse_variables(record.get("variables_json"), record.get("content_md", "")),
            "has_override": bool(record.get("has_override", False)),
            "update_available": bool(record.get("update_available", False)),
            "base_version": record.get("base_version", ""),
            "default_version": record.get("default_version", ""),
            "category": record.get("category", "기본"),
            "enabled": bool(record.get("enabled", True)),
        }

    def validate_prompt_content(self, prompt_id: str, content_md: str) -> dict[str, Any]:
        details = self.get_prompt_details(prompt_id) or {}
        known_vars = set(details.get("variables", [])) | {"CONTENT", "SELECTION", "QUESTION", "TITLE", "TAGS", "CONTEXT", "USER_INPUT"}
        found_vars = set(self._extract_variables(content_md))
        unknown_vars = sorted(found_vars - known_vars)
        missing_required = sorted(self._required_variables_for_prompt(prompt_id) - found_vars)
        return {
            "unknown_variables": unknown_vars,
            "missing_required_variables": missing_required,
            "ok": not unknown_vars and not missing_required,
        }

    def _get_effective_record(self, prompt_id: str) -> dict[str, Any] | None:
        summary = self._repo.get_prompt_summary(prompt_id)
        if not summary:
            return None

        action = summary["action"]
        default = summary.get("default")
        override = summary.get("override")
        effective = override if override else default
        if not effective:
            return None

        default_hash = default.get("content_hash") if default else ""
        override_hash = override.get("content_hash") if override else ""

        return {
            "prompt_id": prompt_id,
            "title": effective.get("title") or action["name"],
            "description": effective.get("description") or action.get("description") or "",
            "content_md": effective.get("content_md", ""),
            "variables_json": effective.get("variables_json", "[]"),
            "has_override": bool(override),
            "update_available": bool(default and override and default_hash and override_hash and default_hash != override_hash),
            "base_version": override.get("base_version") if override else "",
            "default_version": default.get("version") if default else "",
            "category": action.get("category") or "기본",
            "enabled": bool(override.get("enabled", 1) if override else 1),
        }

    def _parse_variables(self, variables_json: Any, content_md: str) -> list[str]:
        if isinstance(variables_json, str) and variables_json:
            try:
                variables = json.loads(variables_json)
                if isinstance(variables, list):
                    return [str(v) for v in variables]
            except Exception:
                pass
        return self._extract_variables(content_md)

    def _extract_variables(self, content_md: str) -> list[str]:
        return sorted(set(VARIABLE_PATTERN.findall(content_md or "")))

    def _required_variables_for_prompt(self, prompt_id: str) -> set[str]:
        prompt_id = prompt_id or ""
        if prompt_id == "current_note_qa":
            return {"USER_INPUT"}
        if prompt_id == "summarize_note":
            return {"CONTENT"}
        if prompt_id == "polish_selection":
            return {"CONTENT"}
        if prompt_id == "extract_todo":
            return {"CONTENT"}
        if prompt_id == "suggest_title_tags":
            return {"CONTENT"}
        return set()
