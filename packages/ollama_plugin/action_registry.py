"""Action registry for AI assistant actions."""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AIAction:
    """Represents an AI action configuration."""

    def __init__(
        self,
        action_id: str,
        name: str,
        version: str = "1.0.0",
        input_source: str = "current_note",
        output_format: str = "text",
        rag: bool = False,
        model_hint: str = "",
        prompt_template: str = "",
    ):
        self.id = action_id
        self.name = name
        self.version = version
        self.input_source = input_source
        self.output_format = output_format
        self.rag = rag
        self.model_hint = model_hint
        self.prompt_template = prompt_template

    @classmethod
    def from_dict(cls, data: dict) -> "AIAction":
        """Create AIAction from dictionary."""
        return cls(
            action_id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            input_source=data.get("input", "current_note"),
            output_format=data.get("output", "text"),
            rag=data.get("rag", False),
            model_hint=data.get("model_hint", ""),
            prompt_template=data.get("prompt_template", ""),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "input": self.input_source,
            "output": self.output_format,
            "rag": self.rag,
            "model_hint": self.model_hint,
            "prompt_template": self.prompt_template,
        }


class ActionRegistry:
    """Registry for managing AI actions."""

    def __init__(self, actions_dir: Path | None = None):
        if actions_dir is None:
            actions_dir = Path(__file__).parent / "actions"

        self._actions_dir = actions_dir
        self._actions: dict[str, AIAction] = {}
        self._load_actions()

    def _load_actions(self) -> None:
        """Load all action JSON files from the actions directory."""
        if not self._actions_dir.exists():
            logger.warning(f"[ActionRegistry] Actions directory not found: {self._actions_dir}")
            return

        for json_file in self._actions_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                action = AIAction.from_dict(data)
                self._actions[action.id] = action
                logger.info(f"[ActionRegistry] Loaded action: {action.id}")
            except Exception as e:
                logger.error(f"[ActionRegistry] Failed to load {json_file}: {e}")

    def get_action(self, action_id: str) -> Optional[AIAction]:
        """Get an action by ID."""
        return self._actions.get(action_id)

    def get_all_actions(self) -> list[AIAction]:
        """Get all registered actions."""
        return list(self._actions.values())

    def list_actions(self) -> list[dict]:
        """List all actions as dictionaries."""
        return [action.to_dict() for action in self._actions.values()]

    def register_action(self, action: AIAction) -> None:
        """Register a new action."""
        self._actions[action.id] = action
        logger.info(f"[ActionRegistry] Registered action: {action.id}")

    def unregister_action(self, action_id: str) -> bool:
        """Unregister an action."""
        if action_id in self._actions:
            del self._actions[action_id]
            logger.info(f"[ActionRegistry] Unregistered action: {action_id}")
            return True
        return False
