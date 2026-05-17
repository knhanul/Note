"""Qt-facing controller for AI prompt documents and action bindings."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from .ai_prompt_service import PromptService

logger = logging.getLogger(__name__)


class PromptController(QObject):
    """Expose AI prompt documents, actions, and bindings to QML."""

    actionsChanged = pyqtSignal()
    promptDocumentsChanged = pyqtSignal()
    currentActionChanged = pyqtSignal()
    currentPromptDocumentChanged = pyqtSignal()
    validationChanged = pyqtSignal()
    currentPromptDocumentIdChanged = pyqtSignal()
    openPromptDocumentRequested = pyqtSignal(str)  # Emit when user wants to open prompt in main editor

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None, parent=None):
        super().__init__(parent)
        self._service = PromptService(app_data_dir, prompt_package_dir)
        self._actions: list[dict] = []
        self._prompt_documents: list[dict] = []
        self._current_action_id = ""
        self._current_action: dict = {}
        self._current_prompt_document_id = ""
        self._current_prompt_document: dict = {}
        self._validation: dict = {
            "ok": True,
            "missing_required_variables": [],
            "unknown_variables": [],
        }
        self.refresh()

    @pyqtProperty("QVariantList", notify=actionsChanged)
    def actionList(self) -> list:
        return self._actions

    @pyqtProperty("QVariantList", notify=promptDocumentsChanged)
    def promptDocumentList(self) -> list:
        return self._prompt_documents

    @pyqtProperty(str, notify=currentActionChanged)
    def currentActionId(self) -> str:
        return self._current_action_id

    @pyqtProperty("QVariantMap", notify=currentActionChanged)
    def currentAction(self) -> dict:
        return self._current_action

    @pyqtProperty(str, notify=currentPromptDocumentIdChanged)
    def currentPromptDocumentId(self) -> str:
        return self._current_prompt_document_id

    @pyqtProperty("QVariantMap", notify=currentPromptDocumentChanged)
    def currentPromptDocument(self) -> dict:
        return self._current_prompt_document

    @pyqtProperty("QVariantMap", notify=validationChanged)
    def validation(self) -> dict:
        return self._validation

    @pyqtSlot()
    def refresh(self) -> None:
        self._actions = self._service.list_actions()
        self._prompt_documents = self._service.list_prompt_documents(include_archived=False)

        if self._current_action_id:
            self._current_action = self._service.get_binding(self._current_action_id) or {}
        if self._current_prompt_document_id:
            self._current_prompt_document = self._service.get_prompt_document(self._current_prompt_document_id) or {}

        self.actionsChanged.emit()
        self.promptDocumentsChanged.emit()
        self.currentActionChanged.emit()
        self.currentPromptDocumentChanged.emit()
        self.validationChanged.emit()

    @pyqtSlot(str)
    def load_action(self, action_id: str) -> None:
        action = next((item for item in self._actions if item.get("action_id") == action_id), None)
        if not action:
            logger.warning(f"[PromptController] Action not found: {action_id}")
            return

        binding = self._service.get_binding(action_id) or {}
        prompt_doc_id = binding.get("binding_prompt_doc_id") or action.get("prompt_doc_id") or action_id

        self._current_action_id = action_id
        self._current_action = {
            "action_id": action_id,
            **binding,
            "action": action,
        }
        self._current_prompt_document_id = prompt_doc_id
        self._current_prompt_document = self._service.get_prompt_document(prompt_doc_id) or {}
        self._validation = self._service.validate_prompt_for_action(action_id, prompt_doc_id)

        self.currentActionChanged.emit()
        self.currentPromptDocumentIdChanged.emit()
        self.currentPromptDocumentChanged.emit()
        self.validationChanged.emit()

    @pyqtSlot(str)
    def load_prompt_document(self, prompt_doc_id: str) -> None:
        document = self._service.get_prompt_document(prompt_doc_id)
        if not document:
            logger.warning(f"[PromptController] Prompt document not found: {prompt_doc_id}")
            return

        self._current_prompt_document_id = prompt_doc_id
        self._current_prompt_document = document
        if self._current_action_id:
            self._validation = self._service.validate_prompt_for_action(self._current_action_id, prompt_doc_id)

        self.currentPromptDocumentIdChanged.emit()
        self.currentPromptDocumentChanged.emit()
        self.validationChanged.emit()

    @pyqtSlot(result="QVariantList")
    def list_actions(self) -> list:
        return self._actions

    @pyqtSlot(result="QVariantList")
    def list_prompt_documents(self) -> list:
        return self._prompt_documents

    @pyqtSlot(str, result="QVariantMap")
    def get_binding(self, action_id: str) -> dict:
        return self._service.get_binding(action_id) or {}

    @pyqtSlot(str, str, result=bool)
    def set_binding(self, action_id: str, prompt_doc_id: str) -> bool:
        ok = self._service.set_binding(action_id, prompt_doc_id)
        if ok:
            if self._current_action_id == action_id:
                self.load_action(action_id)
            self.refresh()
        return ok

    @pyqtSlot(str, result=bool)
    def reset_binding_to_default(self, action_id: str) -> bool:
        ok = self._service.reset_binding_to_default(action_id)
        if ok:
            if self._current_action_id == action_id:
                self.load_action(action_id)
            self.refresh()
        return ok

    @pyqtSlot(str, result="QVariantMap")
    def open_prompt_document(self, prompt_doc_id: str) -> dict:
        return self._service.open_prompt_document(prompt_doc_id) or {}

    @pyqtSlot(str, result=str)
    def create_prompt_from_default(self, action_id: str) -> str:
        doc = self._service.create_prompt_from_default(action_id)
        if not doc:
            return ""
        self.refresh()
        return doc.get("prompt_doc_id", "")

    @pyqtSlot(str, result=str)
    def copy_prompt_document(self, prompt_doc_id: str) -> str:
        doc = self._service.copy_prompt_document(prompt_doc_id)
        if not doc:
            return ""
        self.refresh()
        return doc.get("prompt_doc_id", "")

    @pyqtSlot(str, str, result="QVariantMap")
    def validate_prompt_for_action(self, action_id: str, prompt_doc_id: str) -> dict:
        return self._service.validate_prompt_for_action(action_id, prompt_doc_id)

    @pyqtSlot(str, str, str, result=bool)
    def save_prompt_document(self, prompt_doc_id: str, title: str, description: str, content_md: str) -> bool:
        ok = self._service.save_prompt_document(prompt_doc_id, title, description, content_md)
        if ok:
            self._current_prompt_document = self._service.get_prompt_document(prompt_doc_id) or {}
            if self._current_action_id:
                self._validation = self._service.validate_prompt_for_action(self._current_action_id, prompt_doc_id)
            self.currentPromptDocumentChanged.emit()
            self.validationChanged.emit()
            self.refresh()
        return ok

    @pyqtSlot(result=str)
    def getDbPath(self) -> str:
        return str(self._service.repository.db_path)

    @pyqtSlot(str)
    def requestOpenPromptDocument(self, prompt_doc_id: str) -> None:
        """Request to open a prompt document in the main editor workspace."""
        logger.info(f"[PromptController] Requesting to open prompt document: {prompt_doc_id}")
        self.openPromptDocumentRequested.emit(prompt_doc_id)
