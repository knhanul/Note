"""Controller for importing a directory tree of documents into the note DB."""
from __future__ import annotations

from PyQt6.QtCore import QObject, QVariant, pyqtSignal, pyqtSlot, QThread

from services.folder_import_service import FolderImportService
from services.folder_service import FolderService
from services.library_service import LibraryService
from services.note_service import NoteService


class _ImportWorker(QObject):
    """Worker that runs import in a background thread."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(int, str, str, int, int, int, list)  # ok, message, rootFolderId, noteCount, folderCount, failedCount, importedNoteIds

    def __init__(self, library_service,
                 src_dir, parent_folder_id, include_subfolders):
        super().__init__()
        self._library = library_service
        self._src_dir = src_dir
        self._parent_folder_id = parent_folder_id
        self._include_subfolders = include_subfolders

    def run(self):
        try:
            print("[_ImportWorker] run() started")
            db = self._library.get_current_database()
            if db is None:
                raise RuntimeError("열린 서재가 없습니다.")

            folder_service = FolderService(db)
            note_service = NoteService(db)

            real_parent = None
            if self._parent_folder_id and not self._parent_folder_id.startswith("smart:"):
                if folder_service.exists(self._parent_folder_id):
                    real_parent = self._parent_folder_id

            importer = FolderImportService(folder_service, note_service)
            result = importer.import_directory(
                self._src_dir,
                parent_folder_id=real_parent,
                include_subfolders=self._include_subfolders,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )

            note_count = result.get("noteCount", 0)
            folder_count = result.get("folderCount", 0)
            failed = result.get("failedCount", 0)
            label = result.get("rootLabel", "")

            message = (
                f"'{label}'에서 노트 {note_count}개, 폴더 {folder_count}개를 가져왔습니다."
            )
            if failed:
                message += f" (실패 {failed}개)"

            print("[_ImportWorker] run() finished successfully, emitting finished")
            self.finished.emit(
                1,
                message,
                result.get("rootFolderId", ""),
                note_count,
                folder_count,
                failed,
                [],
            )
        except Exception as exc:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print("[_ImportWorker] run() exception, emitting finished")
            self.finished.emit(
                0,
                str(exc),
                "",
                0,
                0,
                0,
                [],
            )


class _FileImportWorker(QObject):
    """Worker that imports individual files in a background thread."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(int, str, str, int, int, int, list)  # ok, message, rootFolderId, noteCount, folderCount, failedCount, importedNoteIds

    def __init__(self, library_service, file_paths, folder_id):
        super().__init__()
        self._library = library_service
        self._file_paths = file_paths
        self._folder_id = folder_id

    def run(self):
        try:
            print("[_FileImportWorker] run() started")
            db = self._library.get_current_database()
            if db is None:
                raise RuntimeError("열린 서재가 없습니다.")

            folder_service = FolderService(db)
            note_service = NoteService(db)

            target_folder_id = self._folder_id
            if not target_folder_id or target_folder_id.startswith("smart:"):
                folders = folder_service.get_all()
                for f in folders:
                    if not f.get("is_smart"):
                        target_folder_id = f.get("id", "")
                        break
            if not target_folder_id:
                raise RuntimeError("가져갈 폴더가 없습니다. 먼저 폴더를 생성해주세요.")

            importer = FolderImportService(folder_service, note_service)
            result = importer.import_files(
                self._file_paths,
                target_folder_id,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )

            note_count = result.get("noteCount", 0)
            failed = result.get("failedCount", 0)
            imported_note_ids = result.get("importedNoteIds", [])

            message = f"노트 {note_count}개를 가져왔습니다."
            if failed:
                message += f" (실패 {failed}개)"

            print("[_FileImportWorker] run() finished, emitting finished")
            self.finished.emit(
                1, message, target_folder_id, note_count, 0, failed, imported_note_ids
            )
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print("[_FileImportWorker] run() exception, emitting finished")
            self.finished.emit(0, str(exc), "", 0, 0, 0, [])


class _ImportThread(QThread):
    """Thread that owns and runs the import worker."""

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self._worker = worker
        worker.moveToThread(self)

    def run(self):
        self._worker.run()


class FolderImportController(QObject):
    """QML bridge for folder-tree import operations."""

    importProgress = pyqtSignal(int, int, str)  # current, total, message
    importFinished = pyqtSignal(int, str, str, int, int, int, list)  # ok, message, rootFolderId, noteCount, folderCount, failedCount, importedNoteIds

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
        self._thread: _ImportThread | None = None

    @pyqtSlot(str, str, bool, result=QVariant)
    def importDirectory(self, src_dir: str, parent_folder_id: str, include_subfolders: bool) -> QVariant:
        """Import ``src_dir`` and mirror its folder tree into the current library.

        ``parent_folder_id`` is treated as a hint:
        - empty / smart folder id  → create at the library root
        - real folder id           → create as a child of that folder

        ``include_subfolders`` controls whether to recursively import subdirectories.
        """
        try:
            print(f"[FolderImport] called with src_dir={src_dir!r} parent={parent_folder_id!r} include_subfolders={include_subfolders}")
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
            result = importer.import_directory(src_dir, parent_folder_id=real_parent, include_subfolders=include_subfolders)
            print(
                f"[FolderImport] done: notes={result.get('noteCount')} "
                f"folders={result.get('folderCount')} failed={result.get('failedCount')}"
            )

            # Refresh the UI so the sidebar/notes list show new content.
            root_folder_id = result.get("rootFolderId", "")
            try:
                self._folder_ctrl.foldersChanged.emit()
                # Select the created folder to show imported notes
                if root_folder_id:
                    self._folder_ctrl.selectFolder(root_folder_id)
                else:
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

    @pyqtSlot(str, str, bool)
    def importDirectoryAsync(self, src_dir: str, parent_folder_id: str, include_subfolders: bool) -> None:
        """Start async import in a background thread."""
        print(f"[FolderImportController] importDirectoryAsync called")
        # Clean up previous thread if any
        if self._thread is not None:
            print(f"[FolderImportController] cleaning up previous thread")
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait(10000)
            self._thread = None

        worker = _ImportWorker(
            self._library,
            src_dir, parent_folder_id, include_subfolders
        )
        self._thread = _ImportThread(worker, self)

        worker.progress.connect(self.importProgress)
        worker.finished.connect(self._onImportFinished)
        worker.finished.connect(self.importFinished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        print(f"[FolderImportController] starting thread")
        self._thread.start()

    @pyqtSlot(str, str)
    def importFilesAsync(self, file_paths_json: str, folder_id: str) -> None:
        """Start async file import in a background thread.

        ``file_paths_json`` is a JSON array of file path strings.
        ``folder_id`` is the target folder ID (must be a real folder).
        """
        import json as json_mod
        paths = json_mod.loads(file_paths_json) if file_paths_json else []
        if not paths:
            self.importFinished.emit(0, "가져올 파일이 선택되지 않았습니다.", "", 0, 0, 0, [])
            return

        if self._thread is not None:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait(10000)
            self._thread = None

        worker = _FileImportWorker(
            self._library, paths, folder_id
        )
        self._thread = _ImportThread(worker, self)

        worker.progress.connect(self.importProgress)
        worker.finished.connect(self._onImportFinished)
        worker.finished.connect(self.importFinished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        print(f"[FolderImportController] starting file import thread")
        self._thread.start()

    def _get_first_regular_folder(self, folder_service: FolderService) -> str:
        """Get the first non-smart folder ID, or empty string."""
        folders = folder_service.get_all()
        for f in folders:
            if not f.get("is_smart"):
                return f.get("id", "")
        return ""

    def _refresh_ui(self, root_folder_id: str = "") -> None:
        """Refresh folder and note lists after import."""
        try:
            self._folder_ctrl.foldersChanged.emit()
            if root_folder_id:
                self._folder_ctrl.selectFolder(root_folder_id)
            else:
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

    def _onImportFinished(self, ok, message, rootFolderId, noteCount, folderCount, failedCount, importedNoteIds=None):
        """Handle import completion - clear thread ref. UI refresh is handled by QML."""
        print(f"[FolderImportController] _onImportFinished called")
        self._thread = None
