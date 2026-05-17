"""Qt-facing controller for AI action management."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

from .ai_prompt_service import PromptService

logger = logging.getLogger(__name__)


class AIActionController(QObject):
    """Expose AI action CRUD and binding management to QML."""

    actionsChanged = pyqtSignal()
    currentActionChanged = pyqtSignal()
    validationChanged = pyqtSignal()
    errorOccurred = pyqtSignal(str)
    infoMessage = pyqtSignal(str)

    def __init__(self, app_data_dir: Path, prompt_package_dir: Path | None = None, parent=None):
        super().__init__(parent)
        self._service = PromptService(app_data_dir, prompt_package_dir)
        self._actions: list[dict] = []
        self._current_action_id = ""
        self._current_action: dict = {}
        self._validation: dict = {
            "ok": True,
            "missing_required_variables": [],
            "unknown_variables": [],
            "inferred_input_mode": "auto",
        }
        self.refresh()

    @pyqtProperty("QVariantList", notify=actionsChanged)
    def actionList(self) -> list:
        return self._actions

    @pyqtProperty("QVariantList", notify=actionsChanged)
    def enabledActionList(self) -> list:
        return [a for a in self._actions if a.get("enabled", True) and not a.get("archived", False)]

    @pyqtProperty("QVariantMap", notify=currentActionChanged)
    def currentAction(self) -> dict:
        return self._current_action

    @pyqtProperty(str, notify=currentActionChanged)
    def currentActionId(self) -> str:
        return self._current_action_id

    @pyqtProperty("QVariantMap", notify=validationChanged)
    def validation(self) -> dict:
        return self._validation

    @pyqtSlot()
    def refresh(self) -> None:
        self._actions = self._service.list_actions()
        if self._current_action_id:
            self._current_action = self._service.get_action(self._current_action_id) or {}
            self._update_validation()
        self.actionsChanged.emit()
        self.currentActionChanged.emit()
        self.validationChanged.emit()

    @pyqtSlot(str)
    def load_action(self, action_id: str) -> None:
        action = self._service.get_action(action_id)
        if not action:
            logger.warning(f"[AIActionController] Action not found: {action_id}")
            self.errorOccurred.emit(f"기능을 찾을 수 없습니다: {action_id}")
            return

        self._current_action_id = action_id
        self._current_action = action
        self._update_validation()
        self.currentActionChanged.emit()
        self.validationChanged.emit()

    def _update_validation(self) -> None:
        if not self._current_action:
            self._validation = {
                "ok": True,
                "missing_required_variables": [],
                "unknown_variables": [],
                "inferred_input_mode": "auto",
            }
            return

        prompt_doc_id = self._current_action.get("binding_prompt_doc_id") or self._current_action.get("action_id")
        self._validation = self._service.validate_prompt_for_action(
            self._current_action_id, prompt_doc_id
        )
        self._validation["inferred_input_mode"] = self._infer_input_mode(self._current_action)

    def _infer_input_mode(self, action: dict) -> str:
        input_mode = action.get("input_mode", "auto")
        if input_mode != "auto":
            return input_mode

        prompt = action.get("current_prompt", {})
        if not prompt:
            return "chat_only"

        content_md = prompt.get("content_md", "")
        if not content_md:
            return "chat_only"

        import re
        variables = set(re.findall(r"\{\{([A-Z_]+)\}\}", content_md))

        note_vars = {"CONTENT", "SELECTION", "TITLE", "TAGS", "CONTEXT"}
        chat_vars = {"QUESTION", "USER_INPUT", "CHAT_MESSAGE", "CHAT_HISTORY"}

        has_note = bool(variables & note_vars)
        has_chat = bool(variables & chat_vars)
        has_selection = "SELECTION" in variables

        if has_selection:
            return "selection_required"
        elif has_note and has_chat:
            return "note_and_chat"
        elif has_note:
            return "note_required"
        elif has_chat:
            return "chat_only"
        else:
            return "chat_only"

    @pyqtSlot(result="QVariantList")
    def list_actions(self) -> list:
        return self._actions

    @pyqtSlot(result="QVariantList")
    def list_enabled_actions(self) -> list:
        return self._service.list_actions(enabled_only=True)

    @pyqtSlot(str, result="QVariantMap")
    def get_action(self, action_id: str) -> dict:
        return self._service.get_action(action_id) or {}

    @pyqtSlot(str, str, str, str, str, bool, str, bool, result="QVariantMap")
    def create_action(
        self,
        name: str,
        action_id: str,
        description: str,
        category: str,
        input_mode: str,
        use_rag: bool,
        required_variables_json: str,
    ) -> dict:
        if not name:
            self.errorOccurred.emit("기능 이름은 필수입니다")
            return {}

        data = {
            "name": name,
            "action_id": action_id if action_id else None,
            "description": description,
            "category": category or "user",
            "input_mode": input_mode or "auto",
            "use_rag": 1 if use_rag else 0,
            "required_variables_json": required_variables_json or "[]",
            "enabled": 1,
        }

        result = self._service.create_action(data)
        if result:
            self.refresh()
            self.infoMessage.emit(f"'{name}' 기능이 생성되었습니다.")
            return result
        else:
            self.errorOccurred.emit("기능 생성에 실패했습니다.")
            return {}

    @pyqtSlot(str, str, str, str, str, bool, str, result="QVariantMap")
    def update_action(
        self,
        action_id: str,
        name: str,
        description: str,
        category: str,
        input_mode: str,
        use_rag: bool,
        required_variables_json: str,
    ) -> dict:
        action = self._service.get_action(action_id)
        if not action:
            self.errorOccurred.emit("기능을 찾을 수 없습니다.")
            return {}

        if action.get("readonly"):
            self.errorOccurred.emit("기본 기능은 수정할 수 없습니다.")
            return {}

        data = {
            "name": name,
            "description": description,
            "category": category,
            "input_mode": input_mode,
            "use_rag": 1 if use_rag else 0,
            "required_variables_json": required_variables_json,
        }

        result = self._service.update_action(action_id, data)
        if result:
            self.refresh()
            self.load_action(action_id)
            self.infoMessage.emit(f"'{name}' 기능이 저장되었습니다.")
            return result
        else:
            self.errorOccurred.emit("기능 저장에 실패했습니다.")
            return {}

    @pyqtSlot(str, result="QVariantMap")
    def duplicate_action(self, action_id: str) -> dict:
        result = self._service.duplicate_action(action_id)
        if result:
            self.refresh()
            self.infoMessage.emit("기능이 복사되었습니다.")
            return result
        else:
            self.errorOccurred.emit("기능 복제에 실패했습니다.")
            return {}

    @pyqtSlot(str, result=bool)
    def archive_action(self, action_id: str) -> bool:
        action = self._service.get_action(action_id)
        if not action:
            self.errorOccurred.emit("기능을 찾을 수 없습니다.")
            return False

        if action.get("source_type") == "default":
            self.errorOccurred.emit("기본 기능은 삭제할 수 없습니다.")
            return False

        if action.get("readonly"):
            self.errorOccurred.emit("읽기 전용 기능은 삭제할 수 없습니다.")
            return False

        ok = self._service.archive_action(action_id)
        if ok:
            self.refresh()
            self.infoMessage.emit("기능이 삭제되었습니다.")
        else:
            self.errorOccurred.emit("기능 삭제에 실패했습니다.")
        return ok

    @pyqtSlot(str, bool, result=bool)
    def set_action_enabled(self, action_id: str, enabled: bool) -> bool:
        ok = self._service.set_action_enabled(action_id, enabled)
        if ok:
            self.refresh()
            if self._current_action_id == action_id:
                self.load_action(action_id)
        return ok

    @pyqtSlot(str, result=bool)
    def move_action_up(self, action_id: str) -> bool:
        ok = self._service.move_action_up(action_id)
        if ok:
            self.refresh()
        return ok

    @pyqtSlot(str, result=bool)
    def move_action_down(self, action_id: str) -> bool:
        ok = self._service.move_action_down(action_id)
        if ok:
            self.refresh()
        return ok

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

    @pyqtSlot(str, str, result="QVariantMap")
    def validate_prompt_for_action(self, action_id: str, prompt_doc_id: str) -> dict:
        return self._service.validate_prompt_for_action(action_id, prompt_doc_id)

    @pyqtSlot(str, result="QVariantMap")
    def infer_input_mode(self, action_id: str) -> dict:
        action = self._service.get_action(action_id)
        if not action:
            return {"input_mode": "auto", "reason": "action_not_found"}

        input_mode = action.get("input_mode", "auto")
        if input_mode != "auto":
            return {"input_mode": input_mode, "reason": "explicit"}

        prompt = action.get("current_prompt", {})
        content_md = prompt.get("content_md", "") if prompt else ""

        import re
        variables = set(re.findall(r"\{\{([A-Z_]+)\}\}", content_md))

        note_vars = {"CONTENT", "SELECTION", "TITLE", "TAGS", "CONTEXT"}
        chat_vars = {"QUESTION", "USER_INPUT", "CHAT_MESSAGE", "CHAT_HISTORY"}

        has_note = bool(variables & note_vars)
        has_chat = bool(variables & chat_vars)
        has_selection = "SELECTION" in variables

        if has_selection:
            return {"input_mode": "selection_required", "reason": "has_selection_variable"}
        elif has_note and has_chat:
            return {"input_mode": "note_and_chat", "reason": "has_both_variables"}
        elif has_note:
            return {"input_mode": "note_required", "reason": "has_note_variables"}
        elif has_chat:
            return {"input_mode": "chat_only", "reason": "has_chat_variables"}
        else:
            return {"input_mode": "chat_only", "reason": "no_variables"}

    @pyqtSlot(str, result=bool)
    def validate_action_id(self, action_id: str) -> bool:
        valid, _ = self._service.validate_action_id(action_id)
        return valid

    @pyqtSlot(str, result=str)
    def generate_action_id(self, name: str) -> str:
        return self._service.generate_action_id(name)

    @pyqtSlot(result=str)
    def getDbPath(self) -> str:
        return str(self._service.repository.db_path)
