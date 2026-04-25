"""Folder import service.

Walks a source directory tree on disk, mirrors the folder hierarchy into the
current library's note DB, and creates a note record for each supported
document file (md/markdown/txt/html/htm/docx). Relative images referenced from
.md files are inlined as base64 data URLs so the imported notes render
self-contained inside the editor.
"""
from __future__ import annotations

import base64
import html as html_mod
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.folder_service import FolderService
from services.note_service import NoteService


_MD_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_HTML_BR_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
_HTML_BLOCK_CLOSE_PATTERN = re.compile(
    r"</(p|div|li|ul|ol|h[1-6]|section|article|blockquote|pre)>",
    re.IGNORECASE,
)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

_EXT_TO_MIME = {
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "gif": "gif",
    "webp": "webp",
    "bmp": "bmp",
    "svg": "svg+xml",
}


class FolderImportService:
    """Imports a directory tree of documents into the current library."""

    SUPPORTED_EXTS = {".md", ".markdown", ".txt", ".html", ".htm", ".docx"}

    def __init__(
        self,
        folder_service: FolderService,
        note_service: NoteService,
    ) -> None:
        self._folders = folder_service
        self._notes = note_service

    def import_directory(
        self,
        src_dir: str,
        parent_folder_id: Optional[str] = None,
        folder_color: str = "#3B82F6",
    ) -> Dict[str, Any]:
        if not src_dir:
            raise ValueError("가져올 폴더가 지정되지 않았습니다.")
        src = Path(src_dir)
        if not src.exists() or not src.is_dir():
            raise ValueError(f"폴더를 찾을 수 없습니다: {src_dir}")

        root_label = src.name or "가져온 폴더"
        root_folder_id = self._create_folder(root_label, parent_folder_id, folder_color)
        if not root_folder_id:
            raise RuntimeError("최상위 폴더 생성에 실패했습니다.")

        path_to_folder: Dict[Path, str] = {src.resolve(): root_folder_id}
        imported_notes: List[str] = []
        created_folders: List[str] = [root_folder_id]
        failures: List[Dict[str, str]] = []

        for current_dir, sub_dirs, files in os.walk(src):
            current_path = Path(current_dir).resolve()
            current_folder_id = path_to_folder.get(current_path)
            if current_folder_id is None:
                # Subdirectory whose creation failed earlier; skip its tree.
                sub_dirs[:] = []
                continue

            sub_dirs.sort()
            files.sort()

            # Mirror sub-folders
            kept_subs: List[str] = []
            for sub in sub_dirs:
                sub_path = (current_path / sub).resolve()
                new_id = self._create_folder(sub, current_folder_id, folder_color)
                if new_id:
                    path_to_folder[sub_path] = new_id
                    created_folders.append(new_id)
                    kept_subs.append(sub)
                else:
                    failures.append(
                        {"path": str(sub_path), "error": "폴더 생성 실패"}
                    )
            sub_dirs[:] = kept_subs

            # Import files
            for fname in files:
                fpath = current_path / fname
                ext = fpath.suffix.lower()
                if ext not in self.SUPPORTED_EXTS:
                    continue
                try:
                    title, markdown = self._read_note(fpath)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(fpath), "error": str(exc)})
                    continue

                note_id = uuid.uuid4().hex[:8]
                if self._notes.create(
                    note_id=note_id,
                    folder_id=current_folder_id,
                    title=title or fpath.stem or "무제",
                    content=markdown or "",
                    content_json="",
                ):
                    imported_notes.append(note_id)
                else:
                    failures.append({"path": str(fpath), "error": "노트 생성 실패"})

        return {
            "rootFolderId": root_folder_id,
            "rootLabel": root_label,
            "noteCount": len(imported_notes),
            "folderCount": len(created_folders),
            "failedCount": len(failures),
            "failures": failures,
        }

    # ── helpers ────────────────────────────────────────────────────────────
    def _create_folder(
        self, name: str, parent_id: Optional[str], color: str
    ) -> Optional[str]:
        clean = (name or "").strip() or "무제 폴더"
        folder_id = uuid.uuid4().hex[:8]
        ok = self._folders.create(folder_id, clean, color, parent_id)
        return folder_id if ok else None

    def _read_note(self, fpath: Path) -> Tuple[str, str]:
        ext = fpath.suffix.lower()
        title = fpath.stem
        if ext in (".md", ".markdown"):
            text = self._read_text(fpath)
            return title, self._inline_md_images(text, fpath.parent)
        if ext == ".txt":
            return title, self._read_text(fpath)
        if ext in (".html", ".htm"):
            return title, self._html_to_markdown(self._read_text(fpath))
        if ext == ".docx":
            return title, self._docx_to_markdown(fpath)
        return title, ""

    @staticmethod
    def _read_text(fpath: Path) -> str:
        for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"):
            try:
                return fpath.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        return fpath.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _inline_md_images(markdown: str, base_dir: Path) -> str:
        def _replace(match: re.Match) -> str:
            alt = match.group(1)
            src = (match.group(2) or "").strip()
            if not src or src.startswith(("data:", "http://", "https://")):
                return match.group(0)

            # Strip optional title segment: ![alt](url "title")
            url_only = src.split(" ", 1)[0]

            try:
                img_path = (base_dir / url_only).resolve()
                if not img_path.exists() or not img_path.is_file():
                    return match.group(0)
                ext = img_path.suffix.lower().lstrip(".")
                mime = _EXT_TO_MIME.get(ext)
                if not mime:
                    return match.group(0)
                data = base64.b64encode(img_path.read_bytes()).decode("ascii")
                return f"![{alt}](data:image/{mime};base64,{data})"
            except Exception:
                return match.group(0)

        return _MD_IMG_PATTERN.sub(_replace, markdown or "")

    @staticmethod
    def _html_to_markdown(raw_html: str) -> str:
        text = _HTML_BR_PATTERN.sub("\n", raw_html or "")
        text = _HTML_BLOCK_CLOSE_PATTERN.sub("\n", text)
        text = _HTML_TAG_PATTERN.sub("", text)
        text = html_mod.unescape(text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _docx_to_markdown(fpath: Path) -> str:
        try:
            from docx import Document
        except Exception:  # noqa: BLE001
            return ""

        doc = Document(str(fpath))
        blocks: List[str] = []
        for para in doc.paragraphs:
            text = (para.text or "").rstrip()
            style = (para.style.name or "").lower() if para.style else ""
            if style.startswith("heading"):
                m = re.search(r"\d+", style)
                level = max(1, min(6, int(m.group()) if m else 1))
                blocks.append(("#" * level) + " " + text)
            elif "list" in style and text.strip():
                blocks.append("- " + text)
            else:
                blocks.append(text)

        for table in doc.tables:
            rows: List[List[str]] = []
            for row in table.rows:
                rows.append(
                    [cell.text.replace("\n", " ").strip() for cell in row.cells]
                )
            if not rows:
                continue
            cols = max(len(r) for r in rows)
            rows = [r + [""] * (cols - len(r)) for r in rows]
            md_lines = ["| " + " | ".join(rows[0]) + " |"]
            md_lines.append("| " + " | ".join(["---"] * cols) + " |")
            for r in rows[1:]:
                md_lines.append("| " + " | ".join(r) + " |")
            blocks.append("\n".join(md_lines))

        joined = "\n\n".join(b for b in blocks if b is not None)
        return re.sub(r"\n{3,}", "\n\n", joined).strip()
