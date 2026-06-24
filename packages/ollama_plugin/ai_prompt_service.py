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
from .prompt_variable_analyzer import PromptVariableAnalyzer
from .prompt_renderer import PromptRenderer

logger = logging.getLogger(__name__)

VARIABLE_PATTERN = re.compile(r"\{\{([A-Z_]+)\}\}")
ACTION_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")

RESPONSE_LENGTH_ALLOWED = {"short", "medium", "detailed", "very_detailed"}
RESPONSE_LENGTH_ALIASES = {"long": "detailed", "very_long": "very_detailed"}
DEFAULT_RESPONSE_LENGTH = "medium"


class PromptService:
    """Business logic for AI prompt documents and action-to-prompt bindings."""

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None):
        self._seed_service = PromptSeedService(app_data_dir, prompt_package_dir)
        self._repo: PromptRepository = self._seed_service.ensure_seeded()
        self._renderer = PromptRenderer()

    @property
    def repository(self) -> PromptRepository:
        return self._repo

    def _normalize_response_length(self, value: str | None) -> str:
        if not value:
            return DEFAULT_RESPONSE_LENGTH
        if value in RESPONSE_LENGTH_ALLOWED:
            return value
        if value in RESPONSE_LENGTH_ALIASES:
            return RESPONSE_LENGTH_ALIASES[value]
        return DEFAULT_RESPONSE_LENGTH

    def list_actions(self, include_archived: bool = False, enabled_only: bool = False) -> list[dict[str, Any]]:
        actions = self._repo.list_actions(include_archived=include_archived, enabled_only=enabled_only)
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
                "required_variables_json": action.get("required_variables_json", "[]"),
                "enabled": bool(action.get("enabled", 1)),
                "sort_order": int(action.get("sort_order", 0)),
                "source_type": action.get("source_type", "default"),
                "readonly": bool(action.get("readonly", 0)),
                "archived": bool(action.get("archived", 0)),
                "input_mode": action.get("input_mode", "auto"),
                "use_rag": bool(action.get("use_rag", 0)),
                "response_length": self._normalize_response_length(action.get("response_length")),
                "icon": action.get("icon", ""),
                "example_input": action.get("example_input", ""),
                "input_placeholder": action.get("input_placeholder", ""),
                "prompt_doc_id": prompt_doc_id,
                "binding_prompt_doc_id": binding.get("prompt_doc_id") if binding else prompt_doc_id,
                "binding_updated_at": binding.get("updated_at") if binding else "",
                "current_prompt": self._document_to_summary(prompt) if prompt else None,
            })
        return result

    def get_action(self, action_id: str) -> dict[str, Any] | None:
        action = self._repo.get_action(action_id)
        if not action:
            return None
        summary = self._repo.get_prompt_summary_for_action(action_id)
        prompt = summary.get("prompt") if summary else None
        binding = summary.get("binding") if summary else None
        prompt_doc_id = summary.get("prompt_doc_id") if summary else action_id
        return {
            "action_id": action["action_id"],
            "name": action.get("name", ""),
            "description": action.get("description", ""),
            "category": action.get("category", ""),
            "required_variables": self._parse_variables_json(action.get("required_variables_json")),
            "required_variables_json": action.get("required_variables_json", "[]"),
            "enabled": bool(action.get("enabled", 1)),
            "sort_order": int(action.get("sort_order", 0)),
            "source_type": action.get("source_type", "default"),
            "readonly": bool(action.get("readonly", 0)),
            "archived": bool(action.get("archived", 0)),
            "input_mode": action.get("input_mode", "auto"),
            "use_rag": bool(action.get("use_rag", 0)),
            "response_length": action.get("response_length", "medium"),
            "icon": action.get("icon", ""),
            "example_input": action.get("example_input", ""),
            "input_placeholder": action.get("input_placeholder", ""),
            "created_at": action.get("created_at", ""),
            "updated_at": action.get("updated_at", ""),
            "prompt_doc_id": prompt_doc_id,
            "binding_prompt_doc_id": binding.get("prompt_doc_id") if binding else prompt_doc_id,
            "current_prompt": self._document_to_summary(prompt) if prompt else None,
        }

    def validate_action_id(self, action_id: str) -> tuple[bool, str]:
        if not action_id:
            return False, "action_id는 필수입니다"
        if not ACTION_ID_PATTERN.match(action_id):
            return False, "action_id는 영문 소문자, 숫자, underscore만 가능합니다"
        return True, ""

    def generate_action_id(self, name: str) -> str:
        base = re.sub(r"[^a-z0-9]", "_", name.lower())
        base = re.sub(r"_+", "_", base).strip("_")
        if not base:
            base = "custom_action"
        if not self._repo.action_exists(base):
            return base
        for i in range(1, 100):
            candidate = f"{base}_{i}"
            if not self._repo.action_exists(candidate):
                return candidate
        return f"{base}_{uuid.uuid4().hex[:8]}"

    def create_action(self, data: dict[str, Any]) -> dict[str, Any] | None:
        action_id = data.get("action_id", "").strip() or self.generate_action_id(data.get("name", ""))
        name = data.get("name", "").strip()
        if not name:
            logger.warning("[PromptService] create_action: name is required")
            return None

        valid, msg = self.validate_action_id(action_id)
        if not valid:
            logger.warning(f"[PromptService] create_action: {msg}")
            return None

        if self._repo.action_exists(action_id):
            logger.warning(f"[PromptService] create_action: action_id already exists: {action_id}")
            return None

        sort_order = data.get("sort_order")
        if sort_order is None:
            sort_order = self._repo.get_next_sort_order()

        record = {
            "action_id": action_id,
            "name": name,
            "description": data.get("description", ""),
            "category": data.get("category", "user"),
            "required_variables_json": data.get("required_variables_json", "[]"),
            "enabled": data.get("enabled", 1),
            "sort_order": sort_order,
            "source_type": "user",
            "readonly": 0,
            "archived": 0,
            "input_mode": data.get("input_mode", "auto"),
            "use_rag": data.get("use_rag", 0),
            "response_length": self._normalize_response_length(data.get("response_length")),
            "icon": data.get("icon", ""),
            "example_input": data.get("example_input", ""),
            "input_placeholder": data.get("input_placeholder", ""),
        }

        if self._repo.create_action(record):
            logger.info(f"[PromptService] Created action: {action_id}")
            return self.get_action(action_id)
        return None

    def update_action(self, action_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        action = self._repo.get_action(action_id)
        if not action:
            logger.warning(f"[PromptService] update_action: action not found: {action_id}")
            return None

        if int(action.get("readonly", 0)):
            logger.warning(f"[PromptService] update_action: cannot update readonly action: {action_id}")
            return None

        record = {
            "name": data.get("name", action.get("name", "")),
            "description": data.get("description", action.get("description", "")),
            "category": data.get("category", action.get("category", "")),
            "required_variables_json": data.get("required_variables_json", action.get("required_variables_json", "[]")),
            "enabled": data.get("enabled", action.get("enabled", 1)),
            "sort_order": data.get("sort_order", action.get("sort_order", 0)),
            "source_type": action.get("source_type", "default"),
            "readonly": action.get("readonly", 0),
            "archived": action.get("archived", 0),
            "input_mode": data.get("input_mode", action.get("input_mode", "auto")),
            "use_rag": data.get("use_rag", action.get("use_rag", 0)),
            "response_length": self._normalize_response_length(data.get("response_length", action.get("response_length", DEFAULT_RESPONSE_LENGTH))),
            "icon": data.get("icon", action.get("icon", "")),
            "example_input": data.get("example_input", action.get("example_input", "")),
            "input_placeholder": data.get("input_placeholder", action.get("input_placeholder", "")),
        }

        if self._repo.update_action(action_id, record):
            logger.info(f"[PromptService] Updated action: {action_id}")
            return self.get_action(action_id)
        return None

    def duplicate_action(self, action_id: str) -> dict[str, Any] | None:
        source = self.get_action(action_id)
        if not source:
            logger.warning(f"[PromptService] duplicate_action: action not found: {action_id}")
            return None

        new_action_id = self.generate_action_id(source.get("name", "action"))
        new_name = f"{source.get('name', action_id)} (사본)"

        data = {
            "action_id": new_action_id,
            "name": new_name,
            "description": source.get("description", ""),
            "category": source.get("category", "user"),
            "required_variables_json": source.get("required_variables_json", "[]"),
            "enabled": source.get("enabled", 1),
            "input_mode": source.get("input_mode", "auto"),
            "use_rag": source.get("use_rag", 0),
            "response_length": source.get("response_length", "medium"),
            "icon": source.get("icon", ""),
        }

        new_action = self.create_action(data)
        if not new_action:
            return None

        binding = self._repo.get_binding(action_id)
        if binding:
            self._repo.set_binding(new_action_id, binding.get("prompt_doc_id", new_action_id))

        return new_action

    def archive_action(self, action_id: str) -> bool:
        action = self._repo.get_action(action_id)
        if not action:
            logger.warning(f"[PromptService] archive_action: action not found: {action_id}")
            return False

        if action.get("source_type") == "default":
            logger.warning(f"[PromptService] archive_action: cannot archive default action: {action_id}")
            return False

        if self._repo.archive_action(action_id, True):
            logger.info(f"[PromptService] Archived action: {action_id}")
            return True
        return False

    def set_action_enabled(self, action_id: str, enabled: bool) -> bool:
        action = self._repo.get_action(action_id)
        if not action:
            logger.warning(f"[PromptService] set_action_enabled: action not found: {action_id}")
            return False

        if self._repo.set_action_enabled(action_id, enabled):
            logger.info(f"[PromptService] Set action enabled: {action_id} = {enabled}")
            return True
        return False

    def move_action_up(self, action_id: str) -> bool:
        if self._repo.move_action_up(action_id):
            logger.info(f"[PromptService] Moved action up: {action_id}")
            return True
        return False

    def move_action_down(self, action_id: str) -> bool:
        if self._repo.move_action_down(action_id):
            logger.info(f"[PromptService] Moved action down: {action_id}")
            return True
        return False

    def list_prompt_documents(self, include_archived: bool = False) -> list[dict[str, Any]]:
        docs = self._repo.list_prompt_documents(include_archived=include_archived)
        docs = [doc for doc in docs if doc.get("prompt_doc_id") != "_schema_meta"]
        return [self._document_to_summary(doc, include_content=True) for doc in docs]

    def get_prompt_document(self, prompt_doc_id: str) -> dict[str, Any] | None:
        doc = self._repo.get_prompt_document(prompt_doc_id)
        if not doc or doc.get("prompt_doc_id") == "_schema_meta":
            return None
        return self._document_to_summary(doc, include_content=True)

    def get_prompt_document_by_title(self, title: str) -> dict[str, Any] | None:
        doc = self._repo.get_prompt_document_by_title(title)
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
        }, force=True)
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

    def delete_prompt_document(self, prompt_doc_id: str) -> bool:
        current = self._repo.get_prompt_document(prompt_doc_id)
        if not current:
            return False
        if int(current.get("readonly", 0)):
            return False
        self._repo.delete_prompt_document(prompt_doc_id)
        return True

    def validate_prompt_for_action(self, action_id: str, prompt_doc_id: str) -> dict[str, Any]:
        action = self._repo.get_action(action_id)
        prompt = self._repo.get_prompt_document(prompt_doc_id)
        if not action or not prompt:
            return {"ok": False, "missing_required_variables": ["ACTION_OR_PROMPT_MISSING"], "unknown_variables": []}

        required = set(self._parse_variables_json(action.get("required_variables_json")))
        analysis = PromptVariableAnalyzer.analyze_variables(prompt.get("content_md", ""))
        found = set(analysis.get("variables", []))
        missing_required = sorted(required - found)
        unknown = sorted(analysis.get("unknown_variables", []))
        inferred_input_mode = PromptVariableAnalyzer.infer_input_mode(
            prompt.get("content_md", ""),
            action.get("input_mode", "auto"),
        )
        return {
            "ok": not missing_required,
            "missing_required_variables": missing_required,
            "unknown_variables": unknown,
            "variables": sorted(found),
            "inferred_input_mode": inferred_input_mode,
            "needs_note": bool(analysis.get("needs_note", False)),
            "needs_chat": bool(analysis.get("needs_chat", False)),
            "needs_selection": bool(analysis.get("needs_selection", False)),
        }

    def get_effective_prompt(self, action_id: str) -> str:
        try:
            summary = self._repo.get_prompt_summary_for_action(action_id)
            if not summary:
                logger.warning(f"[PromptService] get_effective_prompt: no summary for {action_id}")
                return ""
            prompt = summary.get("prompt")
            if not prompt:
                logger.warning(f"[PromptService] get_effective_prompt: no prompt in summary for {action_id}")
                return ""
            content_md = prompt.get("content_md", "")
            if not content_md or not content_md.strip():
                logger.warning(f"[PromptService] get_effective_prompt: empty content_md for {action_id}")
                return ""
            return content_md
        except Exception as e:
            logger.error(f"[PromptService] get_effective_prompt error for {action_id}: {e}")
            return ""

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
