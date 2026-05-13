"""AI settings management for Ollama plugin."""

import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AISettings:
    """AI settings stored in JSON file."""
    base_url: str = "http://localhost:11434"
    chat_model: str = ""
    embedding_model: str = ""
    top_k: int = 3
    auto_index: bool = False
    streaming: bool = True
    performance_mode: str = "low"  # "low", "normal", "high"


class AISettingsManager:
    """Manages AI settings with file persistence."""

    DEFAULT_SETTINGS = AISettings(
        base_url="http://localhost:11434",
        chat_model="",
        embedding_model="",
        top_k=3,
        auto_index=False,
        streaming=True,
        performance_mode="low"
    )

    def __init__(self, app_data_dir: Path | None = None) -> None:
        if app_data_dir is None:
            app_data_dir = Path.cwd() / "app_data"

        self._settings_dir = app_data_dir / "ai"
        self._settings_file = self._settings_dir / "ai_settings.json"
        self._settings: AISettings | None = None

    @property
    def settings(self) -> AISettings:
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> AISettings:
        """Load settings from file or create default."""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded = AISettings(
                        base_url=data.get("base_url", self.DEFAULT_SETTINGS.base_url),
                        chat_model=data.get("chat_model", self.DEFAULT_SETTINGS.chat_model),
                        embedding_model=data.get("embedding_model", self.DEFAULT_SETTINGS.embedding_model),
                        top_k=data.get("top_k", self.DEFAULT_SETTINGS.top_k),
                        auto_index=data.get("auto_index", self.DEFAULT_SETTINGS.auto_index),
                        streaming=data.get("streaming", self.DEFAULT_SETTINGS.streaming),
                        performance_mode=data.get("performance_mode", self.DEFAULT_SETTINGS.performance_mode),
                    )
                    logger.info(f"Loaded AI settings from {self._settings_file}")
                    return loaded
            else:
                logger.info("No AI settings file found, using defaults")
                return self.DEFAULT_SETTINGS
        except Exception as e:
            logger.error(f"Failed to load AI settings: {e}")
            return self.DEFAULT_SETTINGS

    def save(self, settings: AISettings | None = None) -> bool:
        """Save settings to file."""
        try:
            self._settings_dir.mkdir(parents=True, exist_ok=True)

            settings_to_save = settings or self._settings or self.DEFAULT_SETTINGS

            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(settings_to_save), f, indent=2, ensure_ascii=False)

            self._settings = settings_to_save
            logger.info(f"Saved AI settings to {self._settings_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save AI settings: {e}")
            return False

    def update_chat_model(self, model: str) -> bool:
        """Update chat model and save."""
        self.settings.chat_model = model
        return self.save()

    def update_embedding_model(self, model: str) -> bool:
        """Update embedding model and save."""
        self.settings.embedding_model = model
        return self.save()

    def update_performance_mode(self, mode: str) -> bool:
        """Update performance mode and adjust settings."""
        self.settings.performance_mode = mode

        if mode == "low":
            self.settings.top_k = 3
            self.settings.streaming = True
        elif mode == "normal":
            self.settings.top_k = 5
            self.settings.streaming = True
        elif mode == "high":
            self.settings.top_k = 10
            self.settings.streaming = True

        return self.save()

    def get_settings_file_path(self) -> Path:
        """Get the settings file path."""
        return self._settings_file
