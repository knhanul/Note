"""Controller for importing a directory tree of documents into the note DB."""
from __future__ import annotations

from PyQt6.QtCore import QObject, QVariant, pyqtSlot

from services.folder_import_service import FolderImportService
from services.folder_service import FolderService
from services.library_service import LibraryService
from services.note_service import NoteService


class FolderImportController(QObject):
    """QML bridge for folder-tree import operations."""

    def __init__(
        self,
        library_service: LibraryService,
        folder_controller,
        note_controller,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._library = library_service
        self._folder_ctrl = folder_controller
        self._note_ctrl = note_controller

    @pyqtSlot(str, str, result=QVariant)
    def importDirectory(self, src_dir: str, parent_folder_id: str) -> QVariant:
        """Import ``src_dir`` and mirror its folder tree into the current library.

        ``parent_folder_id`` is treated as a hint:
        - empty / smart folder id  → create at the library root
        - real folder id           → create as a child of that folder
        """
        try:
            print(f"[FolderImport] called with src_dir={src_dir!r} parent={parent_folder_id!r}")
            db = self._library.get_current_database()
            if db is None:
                raise RuntimeError("열린 서재가 없습니다.")

            folder_service = FolderService(db)
            note_service = NoteService(db)

            real_parent = None
            if parent_folder_id and not parent_folder_id.startswith("smart:"):
                if folder_service.exists(parent_folder_id):
                    real_parent = parent_folder_id

            importer = FolderImportService(folder_service, note_service)
            result = importer.import_directory(src_dir, parent_folder_id=real_parent)
            print(
                f"[FolderImport] done: notes={result.get('noteCount')} "
                f"folders={result.get('folderCount')} failed={result.get('failedCount')}"
            )

            # Refresh the UI so the sidebar/notes list show new content.
            try:
                self._folder_ctrl.foldersChanged.emit()
                self._folder_ctrl.currentFolderChanged.emit()
            except Exception:
                pass
            try:
                if hasattr(self._note_ctrl, "filteredNotesChanged"):
                    self._note_ctrl.filteredNotesChanged.emit()
                if hasattr(self._note_ctrl, "notesChanged"):
                    self._note_ctrl.notesChanged.emit()
                if hasattr(self._note_ctrl, "tagsChanged"):
                    self._note_ctrl.tagsChanged.emit()
            except Exception:
                pass

            note_count = result.get("noteCount", 0)
            folder_count = result.get("folderCount", 0)
            failed = result.get("failedCount", 0)
            label = result.get("rootLabel", "")

            message = (
                f"'{label}'에서 노트 {note_count}개, 폴더 {folder_count}개를 가져왔습니다."
            )
            if failed:
                message += f" (실패 {failed}개)"

            return QVariant({
                "ok": True,
                "message": message,
                "rootFolderId": result.get("rootFolderId", ""),
                "noteCount": note_count,
                "folderCount": folder_count,
                "failedCount": failed,
            })
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            return QVariant({
                "ok": False,
                "message": str(exc),
                "rootFolderId": "",
                "noteCount": 0,
                "folderCount": 0,
                "failedCount": 0,
            })
