"""Prompt manager for loading and managing prompt templates."""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompt templates with support for user overrides."""

    DEFAULT_PROMPTS_DIR = Path(__file__).parent / "prompts"

    def __init__(self, user_prompts_dir: Path | None = None, app_data_dir: Path | None = None):
        if user_prompts_dir is None and app_data_dir:
            user_prompts_dir = app_data_dir / "ai" / "prompts"

        self._default_prompts_dir = self.DEFAULT_PROMPTS_DIR
        self._user_prompts_dir = user_prompts_dir

    def get_prompt(self, prompt_name: str) -> str:
        """Get a prompt template, preferring user prompts over defaults."""
        user_path = None
        default_path = None

        if self._user_prompts_dir:
            user_path = self._user_prompts_dir / f"{prompt_name}.md"

        default_path = self._default_prompts_dir / f"{prompt_name}.md"

        if user_path and user_path.exists():
            logger.info(f"[PromptManager] Using user prompt: {user_path}")
            return user_path.read_text(encoding="utf-8")

        if default_path and default_path.exists():
            logger.info(f"[PromptManager] Using default prompt: {default_path}")
            return default_path.read_text(encoding="utf-8")

        logger.warning(f"[PromptManager] Prompt not found: {prompt_name}")
        return ""

    def save_user_prompt(self, prompt_name: str, content: str) -> bool:
        """Save a user prompt override."""
        if not self._user_prompts_dir:
            logger.warning("[PromptManager] User prompts directory not set")
            return False

        try:
            self._user_prompts_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = self._user_prompts_dir / f"{prompt_name}.md"
            prompt_path.write_text(content, encoding="utf-8")
            logger.info(f"[PromptManager] Saved user prompt: {prompt_path}")
            return True
        except Exception as e:
            logger.error(f"[PromptManager] Failed to save prompt: {e}")
            return False

    def list_available_prompts(self) -> list[str]:
        """List all available prompt names."""
        prompts = set()

        if self._default_prompts_dir.exists():
            for f in self._default_prompts_dir.glob("*.md"):
                prompts.add(f.stem)

        if self._user_prompts_dir and self._user_prompts_dir.exists():
            for f in self._user_prompts_dir.glob("*.md"):
                prompts.add(f.stem)

        return sorted(prompts)

    def has_user_override(self, prompt_name: str) -> bool:
        """Check if a user override exists for a prompt."""
        if not self._user_prompts_dir:
            return False

        user_path = self._user_prompts_dir / f"{prompt_name}.md"
        return user_path.exists()

    def reset_to_default(self, prompt_name: str) -> bool:
        """Remove user override to reset to default."""
        if not self._user_prompts_dir:
            return False

        user_path = self._user_prompts_dir / f"{prompt_name}.md"
        if user_path.exists():
            try:
                user_path.unlink()
                logger.info(f"[PromptManager] Reset prompt to default: {prompt_name}")
                return True
            except Exception as e:
                logger.error(f"[PromptManager] Failed to reset prompt: {e}")
                return False
        return False
