"""JSON-based prompt pack bootstrap service."""

import json
import hashlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromptBootstrapService:
    """Handles JSON-based prompt pack bootstrap for initial setup."""

    DEFAULT_JSON_PATH = Path(__file__).parent / "default_ai_prompts.json"
    SUPPORTED_SCHEMA_VERSION = 1
    TARGET_APP = "work_ai_editor"

    def __init__(self, json_path: Path | None = None):
        self._json_path = json_path or self.DEFAULT_JSON_PATH

    def load_json_pack(self) -> dict[str, Any] | None:
        """Load and validate the JSON prompt pack."""
        if not self._json_path.exists():
            logger.info("[PromptBootstrap] default_ai_prompts.json not found. Use built-in seed fallback.")
            return None

        try:
            with open(self._json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"[PromptBootstrap] Failed to parse JSON: {e}. Use built-in seed fallback.")
            return None

        if not isinstance(data, dict):
            logger.warning("[PromptBootstrap] JSON root must be object. Use built-in seed fallback.")
            return None

        return data

    def validate_pack(self, data: dict[str, Any]) -> str | None:
        """Validate the JSON pack structure. Returns error message or None if valid."""
        schema_version = data.get("schema_version")
        if schema_version != self.SUPPORTED_SCHEMA_VERSION:
            return f"Unsupported schema_version: {schema_version}. Expected {self.SUPPORTED_SCHEMA_VERSION}."

        target_app = data.get("target_app")
        if target_app != self.TARGET_APP:
            return f"Invalid target_app: {target_app}. Expected {self.TARGET_APP}."

        actions = data.get("actions")
        if actions is None or not isinstance(actions, list):
            return "actions must be an array."

        prompts = data.get("prompts")
        if prompts is None or not isinstance(prompts, list):
            return "prompts must be an array."

        action_ids = set()
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                return f"actions[{i}] must be an object."
            action_id = action.get("action_id")
            if not action_id:
                return f"actions[{i}] missing action_id."
            if action_id in action_ids:
                return f"Duplicate action_id: {action_id}."
            action_ids.add(action_id)

            if not action.get("title"):
                return f"actions[{i}] missing title."
            if not action.get("category"):
                return f"actions[{i}] missing category."
            if not action.get("input_mode"):
                return f"actions[{i}] missing input_mode."
            if not action.get("prompt_doc_id"):
                return f"actions[{i}] missing prompt_doc_id."

        prompt_doc_ids = set()
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                return f"prompts[{i}] must be an object."
            prompt_doc_id = prompt.get("prompt_doc_id")
            if not prompt_doc_id:
                return f"prompts[{i}] missing prompt_doc_id."
            if prompt_doc_id in prompt_doc_ids:
                return f"Duplicate prompt_doc_id: {prompt_doc_id}."
            prompt_doc_ids.add(prompt_doc_id)

            if not prompt.get("title"):
                return f"prompts[{i}] missing title."

            content_lines = prompt.get("content_lines")
            content_md = prompt.get("content_md")
            if not content_lines and not content_md:
                return f"prompts[{i}] missing content_lines or content_md."

        for i, action in enumerate(actions):
            prompt_doc_id = action.get("prompt_doc_id")
            if prompt_doc_id not in prompt_doc_ids:
                return f"actions[{i}] references non-existent prompt_doc_id: {prompt_doc_id}."

        return None

    def convert_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Convert JSON action to DB record format."""
        return {
            "action_id": action["action_id"],
            "name": action["title"],
            "description": action.get("description", ""),
            "category": action["category"],
            "input_mode": action.get("input_mode", "auto"),
            "use_rag": 1 if action.get("use_rag", False) else 0,
            "required_variables_json": json.dumps(action.get("required_variables", []), ensure_ascii=False),
            "enabled": 1 if action.get("enabled", True) else 0,
            "readonly": 1 if action.get("readonly", False) else 0,
            "archived": 1 if action.get("archived", False) else 0,
            "sort_order": action.get("sort_order", 999),
            "response_length": action.get("response_length", "medium"),
            "example_input": action.get("example_input", ""),
            "input_placeholder": action.get("input_placeholder", ""),
            "source_type": "default",
        }

    def convert_prompt(self, prompt: dict[str, Any]) -> dict[str, Any]:
        """Convert JSON prompt to DB record format."""
        content_lines = prompt.get("content_lines")
        content_md = prompt.get("content_md")
        if content_lines:
            content = "\n".join(content_lines)
        else:
            content = content_md

        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

        return {
            "prompt_doc_id": prompt["prompt_doc_id"],
            "title": prompt["title"],
            "description": prompt.get("description", ""),
            "content_md": content,
            "source_type": prompt.get("prompt_type", "default"),
            "readonly": 1 if prompt.get("readonly", False) else 0,
            "archived": 1 if prompt.get("archived", False) else 0,
            "variables_json": json.dumps(prompt.get("required_variables", []), ensure_ascii=False),
            "content_hash": content_hash,
            "body_readonly": 1 if prompt.get("body_readonly", False) else 0,
        }

    def get_bindings(self, actions: list[dict], prompts: list[dict]) -> list[tuple[str, str]]:
        """Extract bindings from actions."""
        prompt_doc_ids = {p["prompt_doc_id"] for p in prompts}
        bindings = []
        for action in actions:
            prompt_doc_id = action.get("prompt_doc_id")
            if prompt_doc_id and prompt_doc_id in prompt_doc_ids:
                bindings.append((action["action_id"], prompt_doc_id))
        return bindings
