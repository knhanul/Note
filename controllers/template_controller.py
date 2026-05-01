"""Template controller for managing note templates with QML integration."""
from pathlib import Path
import sys
from typing import Optional
import uuid

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QVariant

try:
    from services.library_service import LibraryService
    from services.template_service import TemplateService
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    from services.library_service import LibraryService
    from services.template_service import TemplateService


class TemplateController(QObject):
    """Controller for template CRUD and QML exposure."""

    templatesChanged = pyqtSignal()
    templateAdded = pyqtSignal(str)
    templateUpdated = pyqtSignal(str)
    templateRemoved = pyqtSignal(str)

    def __init__(self, library_service: LibraryService, folder_controller=None, parent=None):
        super().__init__(parent)
        self._library_service = library_service
        self._folder_controller = folder_controller
        self._template_service: Optional[TemplateService] = None

        self._library_service.currentLibraryChanged.connect(self._on_library_changed)
        self._on_library_changed()

    def _on_library_changed(self):
        db = self._library_service.get_current_database()
        self._template_service = TemplateService(db) if db else None
        self.templatesChanged.emit()

    @pyqtProperty(list, notify=templatesChanged)
    def templates(self):
        if not self._template_service:
            return []
        return self._template_service.get_all()

    @pyqtSlot(str, result=QVariant)
    def getTemplate(self, template_id: str) -> QVariant:
        if not template_id or not self._template_service:
            return QVariant()
        template = self._template_service.get_by_id(template_id)
        return QVariant(template) if template else QVariant()

    @pyqtSlot(str, str, str, result=QVariant)
    def renderTemplate(self, template_id: str, folder_id: str = "", folder_name: str = "") -> QVariant:
        if not template_id or not self._template_service:
            return QVariant()

        template = self._template_service.get_by_id(template_id)
        if not template:
            return QVariant()

        rendered = self._template_service.render_template_fields(
            template.get("title", ""),
            template.get("content", ""),
            folder_id or "",
            folder_name or "",
        )
        result = dict(template)
        result.update(rendered)
        return QVariant(result)

    @pyqtSlot(result=QVariant)
    def getDefaultExampleTemplate(self) -> QVariant:
        return QVariant({
            "title": TemplateService.DEFAULT_EXAMPLE_TITLE,
            "content": TemplateService.DEFAULT_EXAMPLE_CONTENT,
        })

    @pyqtSlot(str, str, str, result=str)
    def createTemplate(self, name: str, title: str = "", content: str = "") -> str:
        if not self._template_service:
            return ""
        clean_name = (name or "").strip()
        if not clean_name:
            return ""

        template_id = str(uuid.uuid4())[:8]
        if self._template_service.create(template_id, clean_name, title or "", content or ""):
            self.templatesChanged.emit()
            self.templateAdded.emit(template_id)
            return template_id
        return ""

    @pyqtSlot(str, str, str, str, result=bool)
    def updateTemplate(self, template_id: str, name: str, title: str = "", content: str = "") -> bool:
        if not template_id or not self._template_service:
            return False
        clean_name = (name or "").strip()
        if not clean_name:
            return False

        ok = self._template_service.update(
            template_id,
            name=clean_name,
            title=title or "",
            content=content or "",
        )
        if ok:
            self.templatesChanged.emit()
            self.templateUpdated.emit(template_id)
        return ok

    @pyqtSlot(str, result=bool)
    def deleteTemplate(self, template_id: str) -> bool:
        if not template_id or not self._template_service:
            return False

        ok = self._template_service.delete(template_id)
        if ok:
            self.templatesChanged.emit()
            self.templateRemoved.emit(template_id)
            if self._folder_controller:
                self._folder_controller.foldersChanged.emit()
                self._folder_controller.currentFolderChanged.emit()
        return ok
