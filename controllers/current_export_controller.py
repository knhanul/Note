"""Controller for exporting currently opened note from editor."""
from __future__ import annotations

import os
from typing import Dict, Any
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSlot, QVariant
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from services.current_note_export_service import CurrentNoteExportService
from services.library_service import LibraryService


class CurrentExportController(QObject):
    """QML bridge for current-note export operations."""

    def __init__(self, library_service: LibraryService, parent=None):
        super().__init__(parent)
        self._library_service = library_service
        self._service = CurrentNoteExportService()

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
