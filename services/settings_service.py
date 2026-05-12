"""Simple JSON-based settings persistence service."""
import json
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSlot


class SettingsService(QObject):
    """Stores/retrieves app settings in a JSON file in the app directory."""

    def __init__(self, settings_path: Optional[str] = None, parent=None):
        super().__init__(parent)
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

    def get_ui_scale(self) -> float:
        return self._data.get("ui_scale", 1.0)

    @pyqtSlot(float)
    def set_ui_scale(self, scale: float):
        self.set("ui_scale", scale)

    def get_expanded_folders(self) -> list:
        """Get list of expanded folder IDs."""
        return self._data.get("expanded_folders", [])

    def set_expanded_folders(self, folder_ids: list):
        """Set list of expanded folder IDs."""
        self.set("expanded_folders", folder_ids)

    def get_include_subfolders(self) -> bool:
        """Get include subfolders setting for note list view."""
        return self._data.get("include_subfolders", False)

    @pyqtSlot(bool)
    def set_include_subfolders(self, include: bool):
        """Set include subfolders setting for note list view."""
        self.set("include_subfolders", include)
