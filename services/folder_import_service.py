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

    SUPPORTED_EXTS = {".md", ".markdown", ".txt", ".html", ".htm", ".docx", ".hwp", ".hwpx"}

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
        include_subfolders: bool = True,
        progress_callback=None,
    ) -> Dict[str, Any]:
        if not src_dir:
            raise ValueError("가져올 폴더가 지정되지 않았습니다.")
        src = Path(src_dir)
        if not src.exists() or not src.is_dir():
            raise ValueError(f"폴더를 찾을 수 없습니다: {src_dir}")

        # When not including subfolders, import files directly to parent without creating root folder
        if not include_subfolders:
            print(f"[FolderImport] Importing files only (no folder creation)")
            imported_notes: List[str] = []
            failures: List[Dict[str, str]] = []

            # If no parent folder, create a default folder
            target_folder_id = parent_folder_id
            if not target_folder_id:
                default_name = "가져온 문서"
                default_color = "#3B82F6"
                target_folder_id = self._create_folder(default_name, None, default_color)
                if not target_folder_id:
                    raise RuntimeError("기본 폴더 생성에 실패했습니다.")
                print(f"[FolderImport] Created default folder: '{default_name}' -> {target_folder_id}")
                created_folders = [target_folder_id]
            else:
                created_folders = []

            # Process only files in the root directory
            files = sorted([f for f in src.iterdir() if f.is_file()])
            total_files = len(files)
            print(f"[FolderImport] Processing {total_files} files in root directory")
            processed = 0

            for fpath in files:
                processed += 1
                ext = fpath.suffix.lower()
                if ext not in self.SUPPORTED_EXTS:
                    print(f"[FolderImport] Skipping file (unsupported ext): {fpath.name} ({ext})")
                    if progress_callback:
                        progress_callback(processed, total_files, f"스킵: {fpath.name}")
                    continue
                print(f"[FolderImport] Processing file: {fpath.name} ({ext})")
                if progress_callback:
                    progress_callback(processed, total_files, f"읽는 중: {fpath.name}")
                try:
                    title, markdown = self._read_note(fpath)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(fpath), "error": str(exc)})
                    print(f"[FolderImport] Failed to read file {fpath.name}: {exc}")
                    if progress_callback:
                        progress_callback(processed, total_files, f"오류: {fpath.name}")
                    continue

                note_id = uuid.uuid4().hex[:8]
                if progress_callback:
                    progress_callback(processed, total_files, f"저장 중: {fpath.name}")
                if self._notes.create(
                    note_id=note_id,
                    folder_id=target_folder_id,
                    title=title or fpath.stem or "무제",
                    content=markdown or "",
                    content_json="",
                ):
                    imported_notes.append(note_id)
                    print(f"[FolderImport] Imported note: '{title or fpath.stem}' -> {note_id}")
                else:
                    failures.append({"path": str(fpath), "error": "노트 생성 실패"})
                    print(f"[FolderImport] Failed to create note: {fpath.name}")

            print(f"[FolderImport] Import complete: {len(imported_notes)} notes, 0 folders, {len(failures)} failures")
            if failures:
                print(f"[FolderImport] Failures:")
                for f in failures:
                    print(f"[FolderImport]   - {f['path']}: {f['error']}")

            return {
                "rootFolderId": target_folder_id or "",
                "rootLabel": "",
                "noteCount": len(imported_notes),
                "folderCount": 0,
                "failedCount": len(failures),
                "failures": failures,
            }

        # Original behavior with folder structure
        root_label = src.name or "가져온 폴더"
        print(f"[FolderImport] Creating root folder: '{root_label}' (include_subfolders={include_subfolders})")
        root_folder_id = self._create_folder(root_label, parent_folder_id, folder_color)
        if not root_folder_id:
            raise RuntimeError("최상위 폴더 생성에 실패했습니다.")
        print(f"[FolderImport] Root folder created: {root_folder_id}")

        path_to_folder: Dict[Path, str] = {src.resolve(): root_folder_id}
        imported_notes: List[str] = []
        created_folders: List[str] = [root_folder_id]
        failures: List[Dict[str, str]] = []

        # Count total files for progress
        total_files = 0
        for _current_dir, _sub_dirs, files in os.walk(src):
            for fname in files:
                fpath = Path(_current_dir) / fname
                if fpath.suffix.lower() in self.SUPPORTED_EXTS:
                    total_files += 1
        processed = 0

        for current_dir, sub_dirs, files in os.walk(src):
            current_path = Path(current_dir).resolve()
            current_folder_id = path_to_folder.get(current_path)
            if current_folder_id is None:
                # Subdirectory whose creation failed earlier; skip its tree.
                sub_dirs[:] = []
                continue

            sub_dirs.sort()
            files.sort()

            # If not including subfolders, skip subdirectory processing after root
            if not include_subfolders and current_path != src.resolve():
                sub_dirs[:] = []
                continue

            print(f"[FolderImport] Processing directory: {current_path} ({len(sub_dirs)} subdirs, {len(files)} files)")

            # Mirror sub-folders
            kept_subs: List[str] = []
            for sub in sub_dirs:
                sub_path = (current_path / sub).resolve()
                new_id = self._create_folder(sub, current_folder_id, folder_color)
                if new_id:
                    path_to_folder[sub_path] = new_id
                    created_folders.append(new_id)
                    kept_subs.append(sub)
                    print(f"[FolderImport] Created folder: '{sub}' -> {new_id}")
                else:
                    failures.append(
                        {"path": str(sub_path), "error": "폴더 생성 실패"}
                    )
                    print(f"[FolderImport] Failed to create folder: '{sub}'")
            sub_dirs[:] = kept_subs

            # Import files
            for fname in files:
                fpath = current_path / fname
                ext = fpath.suffix.lower()
                processed += 1
                if ext not in self.SUPPORTED_EXTS:
                    print(f"[FolderImport] Skipping file (unsupported ext): {fname} ({ext})")
                    if progress_callback:
                        progress_callback(processed, total_files, f"스킵: {fname}")
                    continue
                print(f"[FolderImport] Processing file: {fname} ({ext})")
                if progress_callback:
                    progress_callback(processed, total_files, f"읽는 중: {fname}")
                try:
                    title, markdown = self._read_note(fpath)
                except Exception as exc:  # noqa: BLE001
                    failures.append({"path": str(fpath), "error": str(exc)})
                    print(f"[FolderImport] Failed to read file {fname}: {exc}")
                    if progress_callback:
                        progress_callback(processed, total_files, f"오류: {fname}")
                    continue

                note_id = uuid.uuid4().hex[:8]
                if progress_callback:
                    progress_callback(processed, total_files, f"저장 중: {fname}")
                if self._notes.create(
                    note_id=note_id,
                    folder_id=current_folder_id,
                    title=title or fpath.stem or "무제",
                    content=markdown or "",
                    content_json="",
                ):
                    imported_notes.append(note_id)
                    print(f"[FolderImport] Imported note: '{title or fpath.stem}' -> {note_id}")
                else:
                    failures.append({"path": str(fpath), "error": "노트 생성 실패"})
                    print(f"[FolderImport] Failed to create note: {fname}")

        print(f"[FolderImport] Import complete: {len(imported_notes)} notes, {len(created_folders)} folders, {len(failures)} failures")
        if failures:
            print(f"[FolderImport] Failures:")
            for f in failures:
                print(f"[FolderImport]   - {f['path']}: {f['error']}")

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
        filename_line = f"# {fpath.stem}\n\n"
        if ext in (".md", ".markdown"):
            text = self._read_text(fpath)
            return title, filename_line + self._inline_md_images(text, fpath.parent)
        if ext == ".txt":
            return title, filename_line + self._read_text(fpath)
        if ext in (".html", ".htm"):
            return title, filename_line + self._html_to_markdown(self._read_text(fpath))
        if ext == ".docx":
            return title, filename_line + self._docx_to_markdown(fpath)
        if ext in (".hwp", ".hwpx"):
            return title, filename_line + self._hwp_to_markdown(fpath)
        return title, filename_line

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

    @staticmethod
    def _hwp_to_markdown(fpath: Path) -> str:
        try:
            import gethwp
        except Exception as exc:  # noqa: BLE001
            print(f"[FolderImport] Failed to import gethwp library: {exc}")
            return ""

        try:
            print(f"[FolderImport] Reading HWP file: {fpath}")
            ext = fpath.suffix.lower()
            if ext == ".hwp":
                text = gethwp.read_hwp(str(fpath))
            elif ext == ".hwpx":
                text = gethwp.read_hwpx(str(fpath))
            else:
                return ""

            if not text:
                print(f"[FolderImport] HWP file returned empty text")
                return ""

            # Convert plain text to markdown (preserve line breaks)
            # HWP text may contain paragraph separators
            lines = text.split('\n')
            blocks = []
            for line in lines:
                line = line.strip()
                if line:
                    blocks.append(line)

            joined = "\n\n".join(b for b in blocks if b)
            print(f"[FolderImport] HWP conversion complete: {len(blocks)} paragraphs, {len(joined)} chars")
            return re.sub(r"\n{3,}", "\n\n", joined).strip()
        except Exception as exc:  # noqa: BLE001
            print(f"[FolderImport] HWP conversion failed: {exc}")
            return ""
