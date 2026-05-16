"""High-level service for AI prompt documents and action bindings."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from .ai_prompt_repository import PromptRepository
from .ai_prompt_seed_service import PromptSeedService
from .prompt_renderer import PromptRenderer

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{([A-Z_]+)\}\}")


class PromptService:
    """Business logic for AI prompt documents and action-to-prompt bindings."""

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None):
        self._seed_service = PromptSeedService(app_data_dir, prompt_package_dir)
        self._repo: PromptRepository = self._seed_service.ensure_seeded()
        self._renderer = PromptRenderer()

    @property
    def repository(self) -> PromptRepository:
        return self._repo

    def list_actions(self) -> list[dict[str, Any]]:
        actions = self._repo.list_actions()
        result: list[dict[str, Any]] = []
        for action in actions:
            if action.get("action_id") == "_schema_meta":
                continue
            summary = self._repo.get_prompt_summary_for_action(action["action_id"])
            prompt = summary.get("prompt") if summary else None
            binding = summary.get("binding") if summary else None
            prompt_doc_id = summary.get("prompt_doc_id") if summary else action["action_id"]
            result.append({
                "action_id": action["action_id"],
                "name": action.get("name", ""),
                "description": action.get("description", ""),
                "category": action.get("category", ""),
                "required_variables": self._parse_variables_json(action.get("required_variables_json")),
                "enabled": bool(action.get("enabled", 1)),
                "sort_order": int(action.get("sort_order", 0)),
                "prompt_doc_id": prompt_doc_id,
                "binding_prompt_doc_id": binding.get("prompt_doc_id") if binding else prompt_doc_id,
                "binding_updated_at": binding.get("updated_at") if binding else "",
                "current_prompt": self._document_to_summary(prompt) if prompt else None,
            })
        return result

    def list_prompt_documents(self, include_archived: bool = False) -> list[dict[str, Any]]:
        docs = self._repo.list_prompt_documents(include_archived=include_archived)
        docs = [doc for doc in docs if doc.get("prompt_doc_id") != "_schema_meta"]
        return [self._document_to_summary(doc) for doc in docs]

    def get_prompt_document(self, prompt_doc_id: str) -> dict[str, Any] | None:
        doc = self._repo.get_prompt_document(prompt_doc_id)
        if not doc or doc.get("prompt_doc_id") == "_schema_meta":
            return None
        return self._document_to_summary(doc, include_content=True)

    def get_binding(self, action_id: str) -> dict[str, Any] | None:
        summary = self._repo.get_prompt_summary_for_action(action_id)
        if not summary:
            return None

        action = summary["action"]
        prompt = summary.get("prompt")
        binding = summary.get("binding")
        prompt_doc_id = summary.get("prompt_doc_id") or action_id
        if not prompt:
            prompt = self._repo.get_prompt_document(action_id)
            prompt_doc_id = action_id if prompt else prompt_doc_id

        return {
            "action_id": action_id,
            "action_name": action.get("name", ""),
            "action_description": action.get("description", ""),
            "category": action.get("category", ""),
            "required_variables": self._parse_variables_json(action.get("required_variables_json")),
            "prompt_doc_id": prompt_doc_id,
            "binding_prompt_doc_id": binding.get("prompt_doc_id") if binding else prompt_doc_id,
            "prompt": self._document_to_summary(prompt) if prompt else None,
            "variables_ok": True,
        }

    def set_binding(self, action_id: str, prompt_doc_id: str) -> bool:
        action = self._repo.get_action(action_id)
        prompt = self._repo.get_prompt_document(prompt_doc_id)
        if not action or not prompt:
            return False

        self._repo.set_binding(action_id, prompt_doc_id)
        return True

    def reset_binding_to_default(self, action_id: str) -> bool:
        action = self._repo.get_action(action_id)
        if not action:
            return False

        self._repo.reset_binding(action_id)
        return True

    def open_prompt_document(self, prompt_doc_id: str) -> dict[str, Any] | None:
        return self.get_prompt_document(prompt_doc_id)

    def create_prompt_from_default(self, action_id: str) -> dict[str, Any] | None:
        action = self._repo.get_action(action_id)
        if not action:
            return None

        default_doc = self._repo.get_prompt_document(action_id)
        if not default_doc:
            return None

        new_id = f"{action_id}_{uuid.uuid4().hex[:8]}"
        new_doc = {
            "prompt_doc_id": new_id,
            "title": f"{default_doc.get('title', action.get('name', action_id))} (사본)",
            "description": default_doc.get("description", ""),
            "content_md": default_doc.get("content_md", ""),
            "source_type": "user",
            "readonly": 0,
            "archived": 0,
            "variables_json": default_doc.get("variables_json", "[]"),
            "content_hash": hashlib.sha256((default_doc.get("content_md", "") or "").encode("utf-8")).hexdigest(),
        }
        self._repo.upsert_prompt_document(new_doc)
        return self.get_prompt_document(new_id)

    def copy_prompt_document(self, prompt_doc_id: str) -> dict[str, Any] | None:
        source = self._repo.get_prompt_document(prompt_doc_id)
        if not source:
            return None

        new_id = f"{prompt_doc_id}_{uuid.uuid4().hex[:8]}"
        new_doc = {
            "prompt_doc_id": new_id,
            "title": f"{source.get('title', prompt_doc_id)} (사본)",
            "description": source.get("description", ""),
            "content_md": source.get("content_md", ""),
            "source_type": "user",
            "readonly": 0,
            "archived": 0,
            "variables_json": source.get("variables_json", json.dumps(self._extract_variables(source.get("content_md", "")), ensure_ascii=False)),
            "content_hash": hashlib.sha256((source.get("content_md", "") or "").encode("utf-8")).hexdigest(),
        }
        self._repo.upsert_prompt_document(new_doc)
        return self.get_prompt_document(new_id)

    def create_prompt_document(self, title: str, content_md: str, description: str = "", source_type: str = "user", readonly: int = 0, archived: int = 0, variables_json: str | None = None, prompt_doc_id: str | None = None) -> dict[str, Any]:
        prompt_doc_id = prompt_doc_id or f"prompt_{uuid.uuid4().hex[:12]}"
        doc = {
            "prompt_doc_id": prompt_doc_id,
            "title": title,
            "description": description,
            "content_md": content_md,
            "source_type": source_type,
            "readonly": readonly,
            "archived": archived,
            "variables_json": variables_json or json.dumps(self._extract_variables(content_md), ensure_ascii=False),
            "content_hash": hashlib.sha256((content_md or "").encode("utf-8")).hexdigest(),
        }
        self._repo.upsert_prompt_document(doc)
        return self.get_prompt_document(prompt_doc_id) or doc

    def save_prompt_document(self, prompt_doc_id: str, title: str, description: str, content_md: str) -> bool:
        current = self._repo.get_prompt_document(prompt_doc_id)
        if not current:
            return False
        if int(current.get("readonly", 0)):
            return False

        variables_json = json.dumps(self._extract_variables(content_md), ensure_ascii=False)
        content_hash = hashlib.sha256((content_md or "").encode("utf-8")).hexdigest()
        self._repo.upsert_prompt_document({
            "prompt_doc_id": prompt_doc_id,
            "title": title,
            "description": description,
            "content_md": content_md,
            "source_type": current.get("source_type", "user"),
            "readonly": int(current.get("readonly", 0)),
            "archived": int(current.get("archived", 0)),
            "variables_json": variables_json,
            "content_hash": content_hash,
        })
        self._repo.insert_history(prompt_doc_id, content_md)
        return True

    def archive_prompt_document(self, prompt_doc_id: str, archived: bool = True) -> bool:
        current = self._repo.get_prompt_document(prompt_doc_id)
        if not current:
            return False
        if int(current.get("readonly", 0)) and archived:
            return False
        self._repo.archive_prompt_document(prompt_doc_id, archived=archived)
        return True

    def validate_prompt_for_action(self, action_id: str, prompt_doc_id: str) -> dict[str, Any]:
        action = self._repo.get_action(action_id)
        prompt = self._repo.get_prompt_document(prompt_doc_id)
        if not action or not prompt:
            return {"ok": False, "missing_required_variables": ["ACTION_OR_PROMPT_MISSING"], "unknown_variables": []}

        required = set(self._parse_variables_json(action.get("required_variables_json")))
        known = set(self._extract_variables(prompt.get("content_md", ""))) | {"CONTENT", "SELECTION", "QUESTION", "TITLE", "TAGS", "CONTEXT"}
        found = set(self._extract_variables(prompt.get("content_md", "")))
        missing_required = sorted(required - found)
        unknown = sorted(found - known)
        return {
            "ok": not missing_required and not unknown,
            "missing_required_variables": missing_required,
            "unknown_variables": unknown,
        }

    def get_effective_prompt(self, action_id: str) -> str:
        summary = self._repo.get_prompt_summary_for_action(action_id)
        if not summary:
            return ""
        prompt = summary.get("prompt")
        return prompt.get("content_md", "") if prompt else ""

    def render_prompt(self, action_id: str, context: dict[str, Any]) -> str:
        template = self.get_effective_prompt(action_id)
        return self._renderer.render(template, context)

    def get_prompt_content_for_action(self, action_id: str) -> str:
        return self.get_effective_prompt(action_id)

    def _extract_variables(self, content_md: str) -> list[str]:
        return sorted(set(VARIABLE_PATTERN.findall(content_md or "")))

    def _parse_variables_json(self, variables_json: Any) -> list[str]:
        if isinstance(variables_json, str) and variables_json:
            try:
                parsed = json.loads(variables_json)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass
        return []

    def _document_to_summary(self, doc: dict[str, Any] | None, include_content: bool = False) -> dict[str, Any] | None:
        if not doc:
            return None

        content_md = doc.get("content_md", "") if include_content or "content_md" in doc else ""
        variables = self._parse_variables_json(doc.get("variables_json"))
        if not variables and content_md:
            variables = self._extract_variables(content_md)

        return {
            "prompt_doc_id": doc.get("prompt_doc_id", ""),
            "title": doc.get("title", ""),
            "description": doc.get("description", ""),
            "content_md": content_md,
            "source_type": doc.get("source_type", "user"),
            "readonly": int(doc.get("readonly", 0) or 0),
            "archived": int(doc.get("archived", 0) or 0),
            "variables": variables,
            "variables_json": doc.get("variables_json", "[]"),
            "content_hash": doc.get("content_hash", ""),
            "created_at": doc.get("created_at", ""),
            "updated_at": doc.get("updated_at", ""),
        }
