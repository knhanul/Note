"""Controller for exporting currently opened note from editor."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, List

from PyQt6.QtCore import QObject, QVariant, pyqtSignal, pyqtSlot, QThread, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication

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


class _PdfToImageWorker(QObject):
    """Worker that converts a generated PDF into preview page images."""

    finished = pyqtSignal(int, list, str)  # requestId, pageEntries, error

    def __init__(self, request_id: int, pdf_path: Path, images_dir: Path, zoom: float = 2.0):
        super().__init__()
        self._request_id = request_id
        self._pdf_path = Path(pdf_path)
        self._images_dir = Path(images_dir)
        self._zoom = zoom

    @pyqtSlot()
    def run(self):  # pragma: no cover - worker thread logic
        try:
            import fitz  # type: ignore
        except ImportError:
            self.finished.emit(self._request_id, [], "PyMuPDF(PyMuPDF) 라이브러리가 설치되어 있지 않습니다.")
            return

        if not self._pdf_path.exists():
            self.finished.emit(self._request_id, [], "PDF 파일을 찾을 수 없습니다.")
            return

        try:
            if self._images_dir.exists():
                shutil.rmtree(self._images_dir, ignore_errors=True)
            self._images_dir.mkdir(parents=True, exist_ok=True)

            doc = fitz.open(self._pdf_path)
            matrix = fitz.Matrix(self._zoom, self._zoom)
            page_entries: list[dict[str, Any]] = []
            current_thread = QThread.currentThread()
            cancelled = False

            for index in range(doc.page_count):
                if current_thread and current_thread.isInterruptionRequested():
                    cancelled = True
                    break
                page = doc.load_page(index)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                image_path = self._images_dir / f"page_{index + 1:03d}.png"
                pix.save(str(image_path))
                page_entries.append({
                    "path": str(image_path),
                    "width": pix.width,
                    "height": pix.height,
                    "number": index + 1,
                })

            doc.close()
            if cancelled:
                shutil.rmtree(self._images_dir, ignore_errors=True)
                self.finished.emit(self._request_id, [], "cancelled")
                return
            self.finished.emit(self._request_id, page_entries, "")
        except Exception as exc:  # noqa: BLE001
            self.finished.emit(self._request_id, [], str(exc))


class _PdfToImageThread(QThread):
    """Thread that owns and runs the PDF-to-image worker."""

    def __init__(self, worker: _PdfToImageWorker, parent=None):
        super().__init__(parent)
        self._worker = worker
        worker.moveToThread(self)

    def run(self):
        self._worker.run()


class _BatchExportWorker(QObject):
    """Worker for batch (folder) export."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, str, str, int, int)  # ok, message, outputPath, count, failedCount

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
    printPreviewStarted = pyqtSignal(int)
    printPreviewReady = pyqtSignal(int, str, list)
    printPreviewFailed = pyqtSignal(int, str)

    def __init__(self, library_service: LibraryService, parent=None):
        super().__init__(parent)
        self._library_service = library_service
        self._service = CurrentNoteExportService()
        self._thread: QThread | None = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setInterval(280)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._process_preview_queue)
        self._pending_preview_options: Dict[str, Any] | None = None
        self._preview_seq = 0
        self._preview_active_request_id = 0
        self._preview_view: QWebEngineView | None = None
        self._preview_requests: Dict[int, Dict[str, Any]] = {}
        self._preview_image_threads: Dict[int, QThread] = {}
        self._preview_root = Path(__file__).resolve().parents[1] / "app_data" / "tmp" / "print_preview"
        self._preview_root.mkdir(parents=True, exist_ok=True)
        self._preview_last_hash = ""
        self._preview_last_pdf_path = ""
        self._preview_last_request_id = 0
        self._preview_last_page_entries: List[Dict[str, Any]] = []

    @pyqtSlot(int, str, str)
    def _relaySingleExportFinished(self, ok, message, outputPath):
        """Relay 3-arg single export finished to 5-arg exportFinished."""
        self.exportFinished.emit(ok, message, outputPath, 1, 0)

    @pyqtSlot(str, result=str)
    def safeFilename(self, name: str) -> str:
        return self._service.safe_filename(name)

    @pyqtSlot(str, result=bool)
    def openDirectory(self, path: str) -> bool:
        if not path:
            return False
        qurl = QUrl.fromLocalFile(path)
        return QDesktopServices.openUrl(qurl)

    @pyqtSlot('QVariantMap')
    def requestPrintPreview(self, options: Dict[str, Any]):
        opts = dict(options or {})
        self._pending_preview_options = opts
        self._preview_timer.start()

    @pyqtSlot('QVariantMap', str, result=QVariant)
    def saveLatestPreviewPdf(self, options: Dict[str, Any], target_path: str) -> QVariant:
        if not target_path:
            return QVariant({
                "ok": False,
                "message": "저장할 경로가 없습니다.",
                "outputPath": "",
            })

        opts = dict(options or {})
        try:
            html = self._build_print_html(opts)
        except Exception as exc:  # noqa: BLE001
            return QVariant({
                "ok": False,
                "message": str(exc),
                "outputPath": "",
            })

        options_hash = self._hash_preview_options(opts)
        if (
            options_hash
            and options_hash == self._preview_last_hash
            and self._preview_last_pdf_path
            and os.path.exists(self._preview_last_pdf_path)
        ):
            try:
                shutil.copy2(self._preview_last_pdf_path, target_path)
                return QVariant({
                    "ok": True,
                    "message": "PDF 저장이 완료되었습니다.",
                    "outputPath": target_path,
                    "reusedPreview": True,
                })
            except Exception as exc:  # noqa: BLE001
                return QVariant({
                    "ok": False,
                    "message": str(exc),
                    "outputPath": "",
                })

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
                html_file.write(html)
                temp_html_path = html_file.name
        except Exception as exc:  # noqa: BLE001
            return QVariant({
                "ok": False,
                "message": f"임시 HTML 파일을 생성하지 못했습니다: {exc}",
                "outputPath": "",
            })

        try:
            ok = self._webengine_print_to_pdf(temp_html_path, target_path)
        finally:
            try:
                os.unlink(temp_html_path)
            except Exception:
                pass

        if ok:
            return QVariant({
                "ok": True,
                "message": "PDF 저장이 완료되었습니다.",
                "outputPath": target_path,
                "reusedPreview": False,
            })
        return QVariant({
            "ok": False,
            "message": "PDF 생성에 실패했습니다.",
            "outputPath": "",
        })

    def _process_preview_queue(self):
        if not self._pending_preview_options:
            return
        options = self._pending_preview_options
        self._pending_preview_options = None
        self._start_preview_request(options)

    def _cancel_pending_preview_work(self):
        if self._preview_view is not None:
            obj = self._preview_view
            self._preview_view = None
            try:
                obj.stop()
            except Exception:
                pass
            obj.deleteLater()
        for thread in list(self._preview_image_threads.values()):
            try:
                if thread.isRunning():
                    thread.requestInterruption()
            except Exception:
                pass

    def _try_emit_cached_preview(self, request_id: int, options: Dict[str, Any], options_hash: str) -> bool:
        if not (
            options_hash
            and options_hash == self._preview_last_hash
            and self._preview_last_pdf_path
            and os.path.exists(self._preview_last_pdf_path)
            and self._preview_last_page_entries
        ):
            return False

        last_request_id = self._preview_last_request_id
        if not last_request_id:
            return False

        previous_context = self._preview_requests.get(last_request_id)
        if not previous_context:
            return False

        images_dir = previous_context.get("images_dir")
        if images_dir and not os.path.exists(images_dir):
            return False

        cloned_context = dict(previous_context)
        cloned_context["options"] = options
        self._preview_requests[request_id] = cloned_context
        if last_request_id != request_id:
            self._preview_requests.pop(last_request_id, None)

        self._preview_active_request_id = request_id
        self._preview_last_request_id = request_id
        self.printPreviewStarted.emit(request_id)
        cached_entries = [dict(entry) for entry in self._preview_last_page_entries]
        self.printPreviewReady.emit(request_id, self._preview_last_pdf_path, cached_entries)
        self._cleanup_old_previews(keep_request_id=request_id)
        return True

    def _start_preview_request(self, options: Dict[str, Any]):
        request_id = self._preview_seq + 1
        self._preview_seq = request_id
        options_hash = self._hash_preview_options(options)

        if self._try_emit_cached_preview(request_id, options, options_hash):
            return

        self._preview_active_request_id = request_id
        self._cancel_pending_preview_work()

        try:
            html = self._build_print_html(options)
        except Exception as exc:  # noqa: BLE001
            self.printPreviewFailed.emit(request_id, str(exc))
            return

        html_path = self._preview_root / f"preview_{request_id}.html"
        pdf_path = self._preview_root / f"preview_{request_id}.pdf"
        images_dir = self._preview_root / f"preview_{request_id}_pages"

        try:
            if pdf_path.exists():
                pdf_path.unlink(missing_ok=True)
            if html_path.exists():
                html_path.unlink(missing_ok=True)
            if images_dir.exists():
                shutil.rmtree(images_dir, ignore_errors=True)
            html_path.write_text(html, encoding='utf-8')
        except Exception as exc:  # noqa: BLE001
            self.printPreviewFailed.emit(request_id, f"미리보기 파일을 준비하지 못했습니다: {exc}")
            return

        self._preview_requests[request_id] = {
            "options": options,
            "hash": options_hash,
            "html_path": str(html_path),
            "pdf_path": str(pdf_path),
            "images_dir": str(images_dir),
            "preview_zoom": max(1.0, min(3.0, float(options.get("previewZoom", 2.0)))),
        }

        self.printPreviewStarted.emit(request_id)
        self._run_preview_webengine(request_id, html_path, pdf_path)

    def _hash_preview_options(self, options: Dict[str, Any]) -> str:
        normalized = json.dumps(options, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _build_print_html(self, options: Dict[str, Any]) -> str:
        try:
            import markdown  # type: ignore
        except ImportError as exc:  # noqa: BLE001
            raise RuntimeError("markdown 라이브러리가 설치되어 있지 않습니다. pip install markdown 을 실행하세요.") from exc

        title = (options.get("title") or "").strip()
        markdown_text = options.get("markdown") or ""
        include_title = bool(options.get("includeTitle", True))
        include_dates = bool(options.get("includeDates", False))
        include_tags = bool(options.get("includeTags", False))
        include_page_numbers = bool(options.get("includePageNumbers", True))
        include_code_background = bool(options.get("includeCodeBackground", True))
        include_link_urls = bool(options.get("includeLinkUrls", False))
        tags = options.get("tags") or []
        created_at = (options.get("createdAt") or "").strip()
        updated_at = (options.get("updatedAt") or "").strip()

        if include_link_urls:
            markdown_text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", markdown_text)

        parts: List[str] = []
        if include_title and title:
            parts.append(f"# {title}")

        meta_lines: List[str] = []
        if include_dates and (created_at or updated_at):
            created_label = created_at or "-"
            updated_label = updated_at or "-"
            meta_lines.append(f"*작성일 {created_label}  ·  수정일 {updated_label}*")
        if include_tags and tags:
            tag_text = ", ".join(str(tag) for tag in tags if str(tag))
            if tag_text:
                meta_lines.append(f"*태그: {tag_text}*")
        if meta_lines:
            parts.append("\n".join(meta_lines))

        body_markdown = markdown_text.strip() if markdown_text and markdown_text.strip() else "*출력할 내용이 없습니다.*"
        parts.append(body_markdown)
        combined_markdown = "\n\n".join(parts)

        html_body = markdown.markdown(
            combined_markdown,
            extensions=['tables', 'fenced_code', 'codehilite']
        )

        margin_preset = (options.get("marginPreset") or "normal").lower()
        margin_map = {
            "narrow": 10,
            "wide": 25,
        }
        margin_mm = margin_map.get(margin_preset, 18)

        orientation = (options.get("orientation") or "portrait").lower()
        page_size = "A4 landscape" if orientation == "landscape" else "A4 portrait"

        scale_percent = max(50, min(200, int(options.get("scalePercent", 100))))
        font_size = round(12 * (scale_percent / 100.0), 2)

        code_background = "#f4f4f4" if include_code_background else "transparent"
        code_border = "#e0e0e0" if include_code_background else "transparent"

        page_number_css = ""
        if include_page_numbers:
            page_number_css = """
            @page {
                @bottom-center {
                    content: counter(page) " / " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }
            }
            """

        full_html = f"""
        <!DOCTYPE html>
        <html lang=\"ko\">
        <head>
            <meta charset=\"UTF-8\">
            <style>
                @page {{
                    size: {page_size};
                    margin: {margin_mm}mm;
                }}
                {page_number_css}
                body {{
                    font-family: 'Segoe UI', 'Pretendard', 'Malgun Gothic', sans-serif;
                    font-size: {font_size}pt;
                    line-height: 1.65;
                    color: #111111;
                    margin: 0;
                }}
                h1, h2, h3 {{
                    color: #111;
                    margin-top: 1.6em;
                    margin-bottom: 0.6em;
                }}
                h1 {{ font-size: {font_size + 8}pt; border-bottom: 1px solid #e5e5e5; padding-bottom: 8px; }}
                h2 {{ font-size: {font_size + 4}pt; border-bottom: 1px solid #f0f0f0; padding-bottom: 6px; }}
                h3 {{ font-size: {font_size + 2}pt; }}
                p {{ margin: 0.6em 0; }}
                blockquote {{
                    border-left: 4px solid #d0d0d0;
                    padding-left: 12px;
                    color: #555;
                    margin: 1em 0;
                }}
                pre {{
                    background-color: {code_background};
                    border: 1px solid {code_border};
                    border-radius: 6px;
                    padding: 14px;
                    overflow: auto;
                }}
                pre code {{
                    background-color: transparent;
                    font-family: 'JetBrains Mono', 'Consolas', monospace;
                    font-size: {max(8, font_size - 2)}pt;
                }}
                code {{
                    background-color: {code_background};
                    border: 1px solid {code_border};
                    border-radius: 4px;
                    padding: 2px 4px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }}
                th, td {{
                    border: 1px solid #dcdcdc;
                    padding: 8px 10px;
                    text-align: left;
                }}
                th {{
                    background-color: #fafafa;
                    font-weight: 600;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 12px 0;
                }}
                a {{ color: #0b73ff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .document {{
                    padding: 0;
                }}
            </style>
        </head>
        <body>
            <div class=\"document\">
                {html_body}
            </div>
        </body>
        </html>
        """
        return textwrap.dedent(full_html)

    def _run_preview_webengine(self, request_id: int, html_path: Path, pdf_path: Path):
        view = QWebEngineView()
        view.resize(800, 1200)
        self._preview_view = view

        timeout_timer = QTimer(self)
        timeout_timer.setSingleShot(True)
        timeout_timer.setInterval(15000)

        def cleanup_view():
            timeout_timer.stop()
            try:
                view.loadFinished.disconnect(on_load_finished)
            except Exception:
                pass
            try:
                view.page().pdfPrintingFinished.disconnect(on_pdf_finished)
            except Exception:
                pass
            view.deleteLater()
            if self._preview_view is view:
                self._preview_view = None

        def on_timeout():
            cleanup_view()
            if request_id == self._preview_active_request_id:
                self._handle_preview_failure(request_id, "미리보기 생성 시간이 초과되었습니다. 다시 시도해주세요.")

        def on_load_finished(success: bool):
            if request_id != self._preview_active_request_id:
                cleanup_view()
                return
            if not success:
                cleanup_view()
                self._handle_preview_failure(request_id, "미리보기 HTML 로드에 실패했습니다.")
                return
            view.page().printToPdf(str(pdf_path))

        def on_pdf_finished(path: str, success: bool):
            cleanup_view()
            context = self._preview_requests.get(request_id)
            html_file = Path(context.get("html_path", "")) if context else None
            if html_file and html_file.exists():
                try:
                    html_file.unlink()
                except Exception:
                    pass
            if request_id != self._preview_active_request_id:
                return
            if not success:
                self._handle_preview_failure(request_id, "미리보기 PDF 생성에 실패했습니다.")
                return
            self._start_pdf_to_image_conversion(request_id, Path(path))

        view.loadFinished.connect(on_load_finished)
        view.page().pdfPrintingFinished.connect(on_pdf_finished)
        timeout_timer.timeout.connect(on_timeout)
        timeout_timer.start()
        view.setUrl(QUrl.fromLocalFile(str(html_path)))

    def _start_pdf_to_image_conversion(self, request_id: int, pdf_path: Path):
        context = self._preview_requests.get(request_id)
        if not context:
            return

        zoom = context.get("preview_zoom", 2.0)
        images_dir = Path(context.get("images_dir", self._preview_root))
        worker = _PdfToImageWorker(request_id, pdf_path, images_dir, zoom=zoom)
        thread = _PdfToImageThread(worker, self)
        worker.finished.connect(self._handle_preview_images_finished)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        self._preview_image_threads[request_id] = thread
        thread.start()

    @pyqtSlot(int, list, str)
    def _handle_preview_images_finished(self, request_id: int, page_entries: List[dict], error: str):
        thread = self._preview_image_threads.pop(request_id, None)
        context = self._preview_requests.get(request_id)
        if request_id != self._preview_active_request_id or not context:
            return
        if error:
            self._handle_preview_failure(request_id, error)
            return

        image_entries: List[Dict[str, Any]] = []
        for entry in page_entries:
            path = entry.get("path")
            if not path:
                continue
            image_entries.append({
                "url": QUrl.fromLocalFile(str(path)).toString(),
                "width": entry.get("width", 0),
                "height": entry.get("height", 0),
                "number": entry.get("number", 0)
            })

        context["pages"] = page_entries
        self._preview_last_hash = context.get("hash", "")
        self._preview_last_pdf_path = context.get("pdf_path", "")
        self._preview_last_request_id = request_id
        self._preview_last_page_entries = [dict(entry) for entry in image_entries]
        self.printPreviewReady.emit(request_id, context.get("pdf_path", ""), image_entries)
        self._cleanup_old_previews(keep_request_id=request_id)

    def _handle_preview_failure(self, request_id: int, message: str):
        if request_id != self._preview_active_request_id:
            return
        self.printPreviewFailed.emit(request_id, message)

    def _cleanup_old_previews(self, keep_request_id: int):
        for rid, ctx in list(self._preview_requests.items()):
            if rid == keep_request_id:
                continue
            pdf_path = Path(ctx.get("pdf_path", ""))
            images_dir = Path(ctx.get("images_dir", ""))
            html_path = Path(ctx.get("html_path", ""))
            for path in [pdf_path, html_path]:
                if path.exists():
                    try:
                        path.unlink()
                    except Exception:
                        pass
            if images_dir.exists():
                shutil.rmtree(images_dir, ignore_errors=True)
            self._preview_requests.pop(rid, None)

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
        worker.finished.connect(self._relaySingleExportFinished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    @pyqtSlot(str, str, str, result=QVariant)
    def exportNoteToPdf(
        self,
        title: str,
        markdown: str,
        output_path: str,
    ) -> QVariant:
        """Export note to PDF using WebEngine rendering.
        
        This is a synchronous export for the print dialog.
        For async use, consider using exportCurrentNoteAsync with format-specific handling.
        
        Returns QVariantMap: {ok: bool, message: str, outputPath: str}
        """
        try:
            import markdown
            from PyQt6.QtCore import QTemporaryFile
            
            # Convert markdown to HTML with basic styling
            md = markdown or ""
            html_content = markdown.markdown(md, extensions=['tables', 'fenced_code', 'codehilite'])
            
            # Wrap in HTML document with print-friendly CSS
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 12pt;
                        line-height: 1.6;
                        color: #333;
                        max-width: 210mm;
                        margin: 0 auto;
                        padding: 20mm;
                    }}
                    h1, h2, h3, h4, h5, h6 {{
                        color: #1a1a1a;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }}
                    h1 {{ font-size: 24pt; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                    h2 {{ font-size: 18pt; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
                    h3 {{ font-size: 14pt; }}
                    p {{ margin: 0.5em 0; }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Consolas', 'Monaco', monospace;
                        font-size: 0.9em;
                    }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 16px;
                        border-radius: 4px;
                        overflow-x: auto;
                    }}
                    pre code {{
                        background-color: transparent;
                        padding: 0;
                    }}
                    blockquote {{
                        border-left: 4px solid #ddd;
                        margin: 1em 0;
                    padding-left: 1em;
                        color: #666;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 1em 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f5f5f5;
                        font-weight: bold;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                    }}
                    a {{ color: #0066cc; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1>{title or '무제'}</h1>
                {html_content}
            </body>
            </html>
            """
            
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(full_html)
                temp_html_path = f.name
            
            # Use WebEngine to print to PDF
            result = self._webengine_print_to_pdf(temp_html_path, output_path)
            
            # Clean up temp file
            try:
                os.unlink(temp_html_path)
            except Exception:
                pass
            
            if result:
                return QVariant({
                    "ok": True,
                    "message": "PDF 저장이 완료되었습니다.",
                    "outputPath": output_path,
                })
            else:
                return QVariant({
                    "ok": False,
                    "message": "PDF 생성에 실패했습니다.",
                    "outputPath": "",
                })
                
        except ImportError:
            return QVariant({
                "ok": False,
                "message": "markdown 라이브러리가 설치되어 있지 않습니다. pip install markdown 을 실행하세요.",
                "outputPath": "",
            })
        except Exception as exc:
            return QVariant({
                "ok": False,
                "message": str(exc),
                "outputPath": "",
            })
    
    def _webengine_print_to_pdf(self, html_path: str, pdf_path: str) -> bool:
        """Use WebEngine to print HTML to PDF.
        
        This creates a minimal WebEngineView, loads the HTML, and prints to PDF.
        Returns True on success, False on failure.
        """
        result = {'success': False, 'done': False}
        
        def on_pdf_print_finished(path, success):
            result['success'] = success
            result['done'] = True
            view.deleteLater()
        
        def on_load_finished(success):
            if success:
                view.page().printToPdf(pdf_path)
            else:
                result['done'] = True
                view.deleteLater()
        
        try:
            app = QApplication.instance()
            if app is None:
                return False
            
            view = QWebEngineView()
            view.page().pdfPrintingFinished.connect(on_pdf_print_finished)
            view.loadFinished.connect(on_load_finished)
            view.setUrl(QUrl.fromLocalFile(html_path))
            
            # Wait for the operation to complete (max 10 seconds)
            import time
            for _ in range(100):  # 10 seconds timeout
                app.processEvents()
                if result['done']:
                    break
                time.sleep(0.1)
            
            return result['success']
            
        except Exception:
            return False

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
