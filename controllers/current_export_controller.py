"""Controller for exporting currently opened note from editor."""
from __future__ import annotations

import os
from typing import Dict, Any
from pathlib import Path

from PyQt6.QtCore import QObject, QVariant, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from services.current_note_export_service import CurrentNoteExportService
from services.folder_export_service import FolderExportService
from services.folder_service import FolderService
from services.library_service import LibraryService
from services.note_service import NoteService


class _SingleExportWorker(QObject):
    """Worker for single-note export."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, str, str)  # ok, message, outputPath

    def __init__(self, service, title, markdown, content_json, fmt, out_dir):
        super().__init__()
        self._service = service
        self._title = title
        self._markdown = markdown
        self._content_json = content_json
        self._fmt = fmt
        self._out_dir = out_dir

    def run(self):
        try:
            print("[_SingleExportWorker] run() started")
            self.progress.emit(0, 1, "변환 중...")
            output_path = self._service.export(
                title=self._title or "",
                markdown=self._markdown or "",
                content_json=self._content_json or "",
                fmt=self._fmt or "",
                out_dir=self._out_dir or "",
            )
            self.progress.emit(1, 1, "완료")
            normalized_fmt = (self._fmt or "").lower().strip()
            message = "보내기가 완료되었습니다."
            if normalized_fmt == "hwpx":
                message = "md2hwpx 변환으로 표와 이미지가 포함된 HWPX 파일을 생성했습니다."
            print("[_SingleExportWorker] run() finished")
            self.finished.emit(1, message, output_path)
        except Exception as exc:  # noqa: BLE001
            print("[_SingleExportWorker] run() exception")
            self.finished.emit(0, str(exc), "")


class _SingleExportThread(QThread):
    """Thread that owns and runs the single export worker."""

    def __init__(self, worker: _SingleExportWorker, parent=None):
        super().__init__(parent)
        self._worker = worker
        worker.moveToThread(self)

    def run(self):
        self._worker.run()


class _BatchExportWorker(QObject):
    """Worker for batch (folder) export."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)

    def __init__(self, library_service, service, scope, folder_id, fmt, out_dir):
        super().__init__()
        self._library_service = library_service
        self._service = service
        self._scope = scope
        self._folder_id = folder_id
        self._fmt = fmt
        self._out_dir = out_dir

    def run(self):
        try:
            print("[_BatchExportWorker] run() started")
            db = self._library_service.get_current_database()
            if db is None:
                raise RuntimeError("열린 서재가 없습니다.")

            folder_service = FolderService(db)
            note_service = NoteService(db)
            batch = FolderExportService(folder_service, note_service, self._service)

            scope_lower = (self._scope or "").lower().strip()
            if scope_lower == "all":
                result = batch.export_all(
                    fmt=self._fmt, out_dir=self._out_dir,
                    progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
                )
            elif scope_lower == "favorites":
                result = batch.export_favorites(
                    fmt=self._fmt, out_dir=self._out_dir,
                    progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
                )
            else:
                result = batch.export_folder(
                    folder_id=self._folder_id, fmt=self._fmt, out_dir=self._out_dir,
                    progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
                )

            count = result.get("count", 0)
            failed = result.get("failedCount", 0)
            label = result.get("label", "폴더")
            if count == 0 and failed == 0:
                message = f"'{label}'에보낼 노트가 없습니다."
                ok = False
            else:
                message = f"'{label}' 범위에서 {count}개 노트를보냈습니다."
                if failed:
                    message += f" (실패 {failed}개)"
                ok = True

            print("[_BatchExportWorker] run() finished")
            self.finished.emit(
                1 if ok else 0,
                message,
                result.get("outputDir", ""),
                count,
                failed,
            )
        except Exception as exc:  # noqa: BLE001
            print("[_BatchExportWorker] run() exception")
            self.finished.emit(0, str(exc), "", 0, 0)


class _BatchExportThread(QThread):
    """Thread that owns and runs the batch export worker."""

    def __init__(self, worker: _BatchExportWorker, parent=None):
        super().__init__(parent)
        self._worker = worker
        worker.moveToThread(self)

    def run(self):
        self._worker.run()


class CurrentExportController(QObject):
    """QML bridge for current-note export operations."""

    exportProgress = pyqtSignal(int, int, str)  # current, total, message
    exportFinished = pyqtSignal(int, str, str, int, int)  # ok, message, outputPath, count, failedCount

    def __init__(self, library_service: LibraryService, parent=None):
        super().__init__(parent)
        self._library_service = library_service
        self._service = CurrentNoteExportService()
        self._thread: QThread | None = None

    @pyqtSlot(str, result=str)
    def safeFilename(self, name: str) -> str:
        return self._service.safe_filename(name)

    @pyqtSlot(str, result=bool)
    def openDirectory(self, path: str) -> bool:
        if not path:
            return False
        qurl = QUrl.fromLocalFile(path)
        return QDesktopServices.openUrl(qurl)

    @pyqtSlot(str, str, str, str, str, result=QVariant)
    def exportCurrentNote(
        self,
        title: str,
        markdown: str,
        content_json: str,
        fmt: str,
        out_dir: str,
    ) -> QVariant:
        """Export currently opened note content to requested format.

        Returns QVariantMap: {ok: bool, message: str, outputPath: str}
        """
        try:
            output_path = self._service.export(
                title=title or "",
                markdown=markdown or "",
                content_json=content_json or "",
                fmt=fmt or "",
                out_dir=out_dir or "",
            )
            normalized_fmt = (fmt or "").lower().strip()
            message = "내보내기가 완료되었습니다."
            if normalized_fmt == "hwpx":
                message = "md2hwpx 변환으로 표와 이미지가 포함된 HWPX 파일을 생성했습니다."
            return QVariant({
                "ok": True,
                "message": message,
                "outputPath": output_path,
            })
        except Exception as exc:  # noqa: BLE001
            return QVariant({
                "ok": False,
                "message": str(exc),
                "outputPath": "",
            })

    @pyqtSlot(str, str, str, str, str)
    def exportCurrentNoteAsync(self, title, markdown, content_json, fmt, out_dir):
        """Start async single-note export."""
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)
            self._thread = None

        worker = _SingleExportWorker(self._service, title, markdown, content_json, fmt, out_dir)
        self._thread = _SingleExportThread(worker, self)

        worker.progress.connect(self.exportProgress)
        worker.finished.connect(self.exportFinished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    @pyqtSlot(str, str, str, str, result=QVariant)
    def exportFolderNotes(
        self,
        scope: str,
        folder_id: str,
        fmt: str,
        out_dir: str,
    ) -> QVariant:
        """Bulk-export notes for the given scope.

        scope: "folder" | "all" | "favorites"
        folder_id: only used when scope == "folder"
        Returns QVariantMap: {ok, message, outputPath, count, failedCount}
        """
        try:
            db = self._library_service.get_current_database()
            if db is None:
                raise RuntimeError("열린 서재가 없습니다.")

            folder_service = FolderService(db)
            note_service = NoteService(db)
            batch = FolderExportService(folder_service, note_service, self._service)

            scope_lower = (scope or "").lower().strip()
            if scope_lower == "all":
                result = batch.export_all(fmt=fmt, out_dir=out_dir)
            elif scope_lower == "favorites":
                result = batch.export_favorites(fmt=fmt, out_dir=out_dir)
            else:
                result = batch.export_folder(folder_id=folder_id, fmt=fmt, out_dir=out_dir)

            count = result.get("count", 0)
            failed = result.get("failedCount", 0)
            label = result.get("label", "폴더")
            if count == 0 and failed == 0:
                message = f"'{label}'에 내보낼 노트가 없습니다."
                ok = False
            else:
                message = f"'{label}' 범위에서 {count}개 노트를 내보냈습니다."
                if failed:
                    message += f" (실패 {failed}개)"
                ok = True

            return QVariant({
                "ok": ok,
                "message": message,
                "outputPath": result.get("outputDir", ""),
                "count": count,
                "failedCount": failed,
            })
        except Exception as exc:  # noqa: BLE001
            return QVariant({
                "ok": False,
                "message": str(exc),
                "outputPath": "",
                "count": 0,
                "failedCount": 0,
            })

    @pyqtSlot(str, str, str, str)
    def exportFolderNotesAsync(self, scope, folder_id, fmt, out_dir):
        """Start async batch export."""
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(3000)
            self._thread = None

        worker = _BatchExportWorker(
            self._library_service, self._service, scope, folder_id, fmt, out_dir
        )
        self._thread = _BatchExportThread(worker, self)

        worker.progress.connect(self.exportProgress)
        worker.finished.connect(self.exportFinished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()
