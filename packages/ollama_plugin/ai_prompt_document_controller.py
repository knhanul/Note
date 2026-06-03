"""Controller for AI prompt documents in the main editor workspace."""

import json
import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant

from .ai_prompt_service import PromptService

logger = logging.getLogger(__name__)


class AIPromptDocumentController(QObject):
    """Controller for AI prompt documents in the main editor workspace.

    This controller is separate from PromptController (which handles settings/binding).
    This controller focuses on workspace UI: listing, selecting, and loading prompt docs
    into the main editor.
    """

    promptDocumentsChanged = pyqtSignal()
    currentPromptDocumentChanged = pyqtSignal()
    selectedPromptDocIdChanged = pyqtSignal()
    saveStateChanged = pyqtSignal(str)  # "saving", "saved", "error"
    errorOccurred = pyqtSignal(str)
    infoMessage = pyqtSignal(str)

    def __init__(self, app_data_dir: Path, prompt_service: PromptService | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._app_data_dir = Path(app_data_dir)
        self._prompt_service = prompt_service if prompt_service else PromptService(self._app_data_dir / "ai")
        self._prompt_documents: list[dict[str, Any]] = []
        self._selected_prompt_doc_id: str = ""
        self._current_prompt_document: dict[str, Any] | None = None

    @pyqtProperty("QVariantList", notify=promptDocumentsChanged)
    def promptDocumentList(self) -> list:
        """List of all prompt documents for the note list pane."""
        return self._prompt_documents

    @pyqtProperty("QVariantMap", notify=currentPromptDocumentChanged)
    def currentPromptDocument(self) -> dict:
        """Currently selected prompt document for the editor."""
        return self._current_prompt_document if self._current_prompt_document else {}

    @pyqtProperty(str, notify=selectedPromptDocIdChanged)
    def selectedPromptDocId(self) -> str:
        """ID of the currently selected prompt document."""
        return self._selected_prompt_doc_id

    @pyqtSlot(str, result=bool)
    def selectPromptDocument(self, prompt_doc_id: str) -> bool:
        """Select a prompt document by ID."""
        if not prompt_doc_id:
            self._selected_prompt_doc_id = ""
            self._current_prompt_document = None
            self.selectedPromptDocIdChanged.emit()
            self.currentPromptDocumentChanged.emit()
            return False

        doc = self._prompt_service.get_prompt_document(prompt_doc_id)
        if doc:
            self._selected_prompt_doc_id = prompt_doc_id
            self._current_prompt_document = doc
            self.selectedPromptDocIdChanged.emit()
            self.currentPromptDocumentChanged.emit()
            logger.info(f"[AIPromptDocumentController] Selected prompt document: {prompt_doc_id}")
            return True
        else:
            logger.warning(f"[AIPromptDocumentController] Prompt document not found: {prompt_doc_id}")
            return False

    @pyqtSlot(str, result="QVariantMap")
    def getPromptDocument(self, prompt_doc_id: str) -> dict:
        """Get a single prompt document by ID."""
        doc = self._prompt_service.get_prompt_document(prompt_doc_id)
        return doc if doc else {}

    @pyqtSlot()
    def loadPromptDocuments(self) -> None:
        """Load all prompt documents from the database."""
        try:
            docs = self._prompt_service.list_prompt_documents(include_archived=False)
            self._prompt_documents = docs
            self.promptDocumentsChanged.emit()
            logger.info(f"[AIPromptDocumentController] Loaded {len(docs)} prompt documents")
        except Exception as e:
            logger.error(f"[AIPromptDocumentController] Failed to load prompt documents: {e}")
            self._prompt_documents = []
            self.promptDocumentsChanged.emit()

    @pyqtSlot()
    def refresh(self) -> None:
        """Refresh the prompt document list."""
        self.loadPromptDocuments()

    @pyqtSlot(str, result=bool)
    def duplicatePromptDocument(self, prompt_doc_id: str) -> bool:
        """Duplicate a prompt document to create a user-editable copy."""
        if not prompt_doc_id:
            logger.warning("[AIPromptDocumentController] duplicatePromptDocument: no prompt_doc_id")
            return False

        try:
            new_doc = self._prompt_service.copy_prompt_document(prompt_doc_id)
            if new_doc:
                logger.info(f"[AIPromptDocumentController] Duplicated prompt document: {prompt_doc_id} -> {new_doc.get('prompt_doc_id')}")
                # Refresh the list to show the new document
                self.loadPromptDocuments()
                # Select the new document
                self.selectPromptDocument(new_doc.get("prompt_doc_id", ""))
                self.infoMessage.emit("프롬프트 복사본이 생성되었습니다.")
                return True
            else:
                logger.error(f"[AIPromptDocumentController] Failed to duplicate prompt document: {prompt_doc_id}")
                self.errorOccurred.emit("프롬프트 복사에 실패했습니다.")
                return False
        except Exception as e:
            logger.error(f"[AIPromptDocumentController] Error duplicating prompt document: {e}")
            self.errorOccurred.emit(f"프롬프트 복사 중 오류가 발생했습니다: {e}")
            return False

    @pyqtSlot(str, str, str, result=bool)
    def savePromptDocument(self, prompt_doc_id: str, title: str, content_md: str) -> bool:
        """Save a prompt document (only for user-editable prompts)."""
        if not prompt_doc_id:
            logger.warning("[AIPromptDocumentController] savePromptDocument: no prompt_doc_id")
            return False

        try:
            self.saveStateChanged.emit("saving")
            current = self._current_prompt_document or self._prompt_service.get_prompt_document(prompt_doc_id)
            if not current:
                logger.error(f"[AIPromptDocumentController] savePromptDocument: document not found: {prompt_doc_id}")
                self.errorOccurred.emit("프롬프트 문서를 찾을 수 없습니다.")
                self.saveStateChanged.emit("error")
                return False

            # Check if readonly
            if int(current.get("readonly", 0)):
                logger.warning(f"[AIPromptDocumentController] savePromptDocument: attempt to save readonly document: {prompt_doc_id}")
                self.errorOccurred.emit("읽기 전용 프롬프트는 저장할 수 없습니다.")
                self.saveStateChanged.emit("error")
                return False

            # Save using PromptService
            description = current.get("description", "")
            success = self._prompt_service.save_prompt_document(prompt_doc_id, title, description, content_md)

            if success:
                logger.info(f"[AIPromptDocumentController] Saved prompt document: {prompt_doc_id}")
                # Refresh current document
                updated = self._prompt_service.get_prompt_document(prompt_doc_id)
                if updated:
                    self._current_prompt_document = updated
                    self.currentPromptDocumentChanged.emit()
                # Refresh the list
                self.loadPromptDocuments()
                self.saveStateChanged.emit("saved")
                return True
            else:
                logger.error(f"[AIPromptDocumentController] Failed to save prompt document: {prompt_doc_id}")
                self.errorOccurred.emit("프롬프트 저장에 실패했습니다.")
                self.saveStateChanged.emit("error")
                return False
        except Exception as e:
            logger.error(f"[AIPromptDocumentController] Error saving prompt document: {e}")
            self.errorOccurred.emit(f"프롬프트 저장 중 오류가 발생했습니다: {e}")
            self.saveStateChanged.emit("error")
            return False

    @pyqtSlot(result=bool)
    def isCurrentPromptReadonly(self) -> bool:
        """Check if the current prompt document is readonly."""
        if not self._current_prompt_document:
            return True
        return bool(int(self._current_prompt_document.get("readonly", 0)))

    @pyqtSlot(str, str, str, result="QVariantMap")
    def createPromptDocument(self, title: str, content_md: str, description: str = "") -> dict:
        """Create a new user prompt document."""
        if not title:
            title = "새 AI 프롬프트"

        default_content = content_md or """# 새 AI 프롬프트

아래 입력을 참고하여 답변해주세요.

## 입력

{{USER_INPUT}}

## 답변

"""

        try:
            new_doc = self._prompt_service.create_prompt_document(
                title=title,
                content_md=default_content,
                description=description,
                source_type="user",
                readonly=0,
                archived=0,
            )
            if new_doc:
                logger.info(f"[AIPromptDocumentController] Created new prompt document: {new_doc.get('prompt_doc_id')}")
                self.loadPromptDocuments()
                self.selectPromptDocument(new_doc.get("prompt_doc_id", ""))
                self.infoMessage.emit("새 프롬프트가 생성되었습니다.")
                return new_doc
            else:
                logger.error("[AIPromptDocumentController] Failed to create prompt document")
                self.errorOccurred.emit("프롬프트 생성에 실패했습니다.")
                return {}
        except Exception as e:
            logger.error(f"[AIPromptDocumentController] Error creating prompt document: {e}")
            self.errorOccurred.emit(f"프롬프트 생성 중 오류가 발생했습니다: {e}")
            return {}

    @pyqtSlot(str, result=bool)
    def archivePromptDocument(self, prompt_doc_id: str) -> bool:
        """Archive a user prompt document (soft delete)."""
        if not prompt_doc_id:
            logger.warning("[AIPromptDocumentController] archivePromptDocument: no prompt_doc_id")
            return False

        doc = self._prompt_service.get_prompt_document(prompt_doc_id)
        if not doc:
            logger.warning(f"[AIPromptDocumentController] archivePromptDocument: document not found: {prompt_doc_id}")
            return False

        if doc.get("source_type") == "default" or int(doc.get("readonly", 0)):
            logger.warning(f"[AIPromptDocumentController] archivePromptDocument: cannot archive default or readonly: {prompt_doc_id}")
            self.errorOccurred.emit("기본 프롬프트는 삭제할 수 없습니다.")
            return False

        try:
            success = self._prompt_service.archive_prompt_document(prompt_doc_id, archived=True)
            if success:
                logger.info(f"[AIPromptDocumentController] Archived prompt document: {prompt_doc_id}")
                self.loadPromptDocuments()
                self.infoMessage.emit("프롬프트가 삭제되었습니다.")
                if self._selected_prompt_doc_id == prompt_doc_id:
                    self._selected_prompt_doc_id = ""
                    self._current_prompt_document = None
                    self.selectedPromptDocIdChanged.emit()
                    self.currentPromptDocumentChanged.emit()
                return True
            else:
                logger.error(f"[AIPromptDocumentController] Failed to archive prompt document: {prompt_doc_id}")
                self.errorOccurred.emit("프롬프트 삭제에 실패했습니다.")
                return False
        except Exception as e:
            logger.error(f"[AIPromptDocumentController] Error archiving prompt document: {e}")
            self.errorOccurred.emit(f"프롬프트 삭제 중 오류가 발생했습니다: {e}")
            return False

    @pyqtSlot(str, result=bool)
    def deletePromptDocument(self, prompt_doc_id: str) -> bool:
        """Permanently delete a prompt document."""
        if not prompt_doc_id:
            logger.warning("[AIPromptDocumentController] deletePromptDocument: no prompt_doc_id")
            return False

        doc = self._prompt_service.get_prompt_document(prompt_doc_id)
        if not doc:
            logger.warning(f"[AIPromptDocumentController] deletePromptDocument: document not found: {prompt_doc_id}")
            return False

        if doc.get("source_type") == "default" or int(doc.get("readonly", 0)):
            logger.warning(f"[AIPromptDocumentController] deletePromptDocument: cannot delete default or readonly: {prompt_doc_id}")
            self.errorOccurred.emit("기본 프롬프트는 삭제할 수 없습니다.")
            return False

        try:
            success = self._prompt_service.delete_prompt_document(prompt_doc_id)
            if success:
                logger.info(f"[AIPromptDocumentController] Permanently deleted prompt document: {prompt_doc_id}")
                self.loadPromptDocuments()
                self.infoMessage.emit("프롬프트가 삭제되었습니다.")
                if self._selected_prompt_doc_id == prompt_doc_id:
                    self._selected_prompt_doc_id = ""
                    self._current_prompt_document = None
                    self.selectedPromptDocIdChanged.emit()
                    self.currentPromptDocumentChanged.emit()
                return True
            else:
                logger.error(f"[AIPromptDocumentController] Failed to delete prompt document: {prompt_doc_id}")
                self.errorOccurred.emit("프롬프트 삭제에 실패했습니다.")
                return False
        except Exception as e:
            logger.error(f"[AIPromptDocumentController] Error deleting prompt document: {e}")
            self.errorOccurred.emit(f"프롬프트 삭제 중 오류가 발생했습니다: {e}")
            return False

    @pyqtSlot(str, result=int)
    def countBindingsForPrompt(self, prompt_doc_id: str) -> int:
        """Count how many AI actions are bound to this prompt."""
        if not prompt_doc_id:
            return 0
        return self._prompt_service.repository.count_bindings_for_prompt(prompt_doc_id)

    @pyqtSlot(str, result="QVariantList")
    def listActionsBoundToPrompt(self, prompt_doc_id: str) -> list:
        """List AI actions bound to this prompt."""
        if not prompt_doc_id:
            return []
        return self._prompt_service.repository.list_actions_bound_to_prompt(prompt_doc_id)

    @pyqtSlot(str, result=bool)
    def isDefaultPrompt(self, prompt_doc_id: str) -> bool:
        """Check if a prompt is a default (readonly) prompt."""
        doc = self._prompt_service.get_prompt_document(prompt_doc_id)
        if not doc:
            return False
        return doc.get("source_type") == "default" or int(doc.get("readonly", 0)) == 1

    def _initialize(self) -> None:
        """Initialize the controller and load initial data."""
        self.loadPromptDocuments()
