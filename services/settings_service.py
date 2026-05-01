"""Simple JSON-based settings persistence service."""
import json
import os
from pathlib import Path
from typing import Optional


class SettingsService:
    """Stores/retrieves app settings in a JSON file in the app directory."""

    def __init__(self, settings_path: Optional[str] = None):
        if settings_path is None:
            prog_dir = Path(__file__).parent.parent
            settings_path = prog_dir / "nuni_note_settings.json"
        self._settings_path = str(settings_path)
        self._data = self._load()

    def _load(self) -> dict:
        try:
            with open(self._settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self):
        with open(self._settings_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def get_last_library_id(self) -> Optional[str]:
        return self._data.get("last_library_id")

    def set_last_library_id(self, library_id: str):
        self.set("last_library_id", library_id)

    def get_last_folder_id(self) -> Optional[str]:
        return self._data.get("last_folder_id")

    def set_last_folder_id(self, folder_id: str):
        self.set("last_folder_id", folder_id)
