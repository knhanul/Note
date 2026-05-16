"""Qt-facing prompt controller for QML prompt management UI."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class PromptController(QObject):
    """Expose AI prompt data and editing actions to QML."""

    promptsChanged = pyqtSignal()
    currentPromptChanged = pyqtSignal()
    currentPromptIdChanged = pyqtSignal()
    validationChanged = pyqtSignal()

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None, parent=None):
        super().__init__(parent)
        self._service = PromptService(app_data_dir, prompt_package_dir)
        self._prompt_list = []
        self._current_prompt_id = ""
        self._current_prompt = {}
        self._validation = {
            "unknown_variables": [],
            "missing_required_variables": [],
            "ok": True,
        }
        self.refresh()

    @pyqtProperty('QVariantList', notify=promptsChanged)
    def promptList(self) -> list:
        return self._prompt_list

    @pyqtProperty(str, notify=currentPromptIdChanged)
    def currentPromptId(self) -> str:
        return self._current_prompt_id

    @pyqtProperty('QVariantMap', notify=currentPromptChanged)
    def currentPrompt(self) -> dict:
        return self._current_prompt

    @pyqtProperty('QVariantMap', notify=validationChanged)
    def validation(self) -> dict:
        return self._validation

    @pyqtSlot()
    def refresh(self) -> None:
        self._prompt_list = self._service.list_prompts()
        if self._current_prompt_id:
            self._current_prompt = self._service.get_prompt_details(self._current_prompt_id) or {}
            self._validation = self._service.validate_prompt_content(
                self._current_prompt_id,
                self._current_prompt.get("content_md", ""),
            ) if self._current_prompt else {"unknown_variables": [], "missing_required_variables": [], "ok": True}
        self.promptsChanged.emit()
        self.currentPromptChanged.emit()
        self.validationChanged.emit()

    @pyqtSlot(str)
    def loadPrompt(self, prompt_id: str) -> None:
        details = self._service.get_prompt_details(prompt_id)
        if not details:
            logger.warning(f"[PromptController] Prompt not found: {prompt_id}")
            return

        self._current_prompt_id = prompt_id
        self._current_prompt = details
        self._validation = self._service.validate_prompt_content(prompt_id, details.get("content_md", ""))
        self.currentPromptIdChanged.emit()
        self.currentPromptChanged.emit()
        self.validationChanged.emit()

    @pyqtSlot(str, result=bool)
    def saveOverride(self, content_md: str) -> bool:
        if not self._current_prompt_id:
            return False

        validation = self._service.validate_prompt_content(self._current_prompt_id, content_md)
        self._validation = validation
        self.validationChanged.emit()

        success = self._service.save_override(self._current_prompt_id, content_md)
        if success:
            self._current_prompt = self._service.get_prompt_details(self._current_prompt_id) or {}
            self.currentPromptChanged.emit()
            self.refresh()
        return success

    @pyqtSlot(result=bool)
    def resetToDefault(self) -> bool:
        if not self._current_prompt_id:
            return False

        success = self._service.reset_to_default(self._current_prompt_id)
        if success:
            self._current_prompt = self._service.get_prompt_details(self._current_prompt_id) or {}
            self.currentPromptChanged.emit()
            self.refresh()
        return success

    @pyqtSlot(str, result=str)
    def getEffectivePrompt(self, prompt_id: str) -> str:
        return self._service.get_effective_prompt(prompt_id)

    @pyqtSlot(str, result='QVariantMap')
    def getPrompt(self, prompt_id: str) -> dict:
        return self._service.get_prompt_details(prompt_id) or {}

    @pyqtSlot(str, result='QVariantMap')
    def validateContent(self, content_md: str) -> dict:
        if not self._current_prompt_id:
            return {"unknown_variables": [], "missing_required_variables": [], "ok": True}
        return self._service.validate_prompt_content(self._current_prompt_id, content_md)

    @pyqtSlot(result=str)
    def getDbPath(self) -> str:
        return str(self._service.repository.db_path)
