"""Folder-level batch export service.

Reuses :class:`CurrentNoteExportService` per note so that every supported
non-PDF format (md/txt/docx/hwpx) shares the exact same conversion path as the
single-note export feature. PDF is intentionally excluded because the
single-note PDF path is implemented through QML WebEngine print, not Python.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.current_note_export_service import CurrentNoteExportService
from services.folder_service import FolderService
from services.note_service import NoteService


class FolderExportService:
    """Bulk-export notes within a folder hierarchy or library-wide scope."""

    SUPPORTED_FORMATS = ("md", "txt", "hwpx", "docx")

    def __init__(
        self,
        folder_service: FolderService,
        note_service: NoteService,
        note_export_service: Optional[CurrentNoteExportService] = None,
    ) -> None:
        self._folders = folder_service
        self._notes = note_service
        self._exporter = note_export_service or CurrentNoteExportService()

    # ── Public entry points ────────────────────────────────────────────────
    def export_folder(self, folder_id: str, fmt: str, out_dir: str, progress_callback=None) -> Dict[str, Any]:
        return self._run("folder", fmt=fmt, out_dir=out_dir, folder_id=folder_id, progress_callback=progress_callback)

    def export_all(self, fmt: str, out_dir: str, root_label: str = "전체 노트", progress_callback=None) -> Dict[str, Any]:
        return self._run("all", fmt=fmt, out_dir=out_dir, root_label=root_label, progress_callback=progress_callback)

    def export_favorites(
        self, fmt: str, out_dir: str, root_label: str = "즐겨 찾기", progress_callback=None
    ) -> Dict[str, Any]:
        return self._run("favorites", fmt=fmt, out_dir=out_dir, root_label=root_label, progress_callback=progress_callback)

    # ── Core orchestration ─────────────────────────────────────────────────
    def _run(
        self,
        scope: str,
        *,
        fmt: str,
        out_dir: str,
        folder_id: Optional[str] = None,
        root_label: str = "",
        progress_callback=None,
    ) -> Dict[str, Any]:
        fmt = (fmt or "").lower().strip()
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"폴더 일괄 내보내기에서 지원하지 않는 포맷입니다: {fmt or '(없음)'}"
            )
        if not out_dir:
            raise ValueError("출력 폴더가 지정되지 않았습니다.")

        target_root = Path(out_dir)
        target_root.mkdir(parents=True, exist_ok=True)

        if scope == "folder":
            folder = self._folders.get_by_id(folder_id) if folder_id else None
            if not folder:
                raise ValueError("선택된 폴더를 찾을 수 없습니다.")
            label = folder.get("name") or "폴더"
            base_dir = target_root / self._safe_dir_name(label)
            base_dir.mkdir(parents=True, exist_ok=True)

            folder_ids = [folder_id] + self._folders.get_descendant_ids(folder_id)
            return self._export_tree(folder_ids, base_dir, fmt, label, root_id=folder_id, progress_callback=progress_callback)

        if scope == "favorites":
            label = root_label or "즐겨 찾기"
            base_dir = target_root / self._safe_dir_name(label)
            base_dir.mkdir(parents=True, exist_ok=True)
            notes = self._notes.get_pinned()
            files, failures = self._export_flat(notes, base_dir, fmt, progress_callback=progress_callback)
            return self._summary(label, files, failures, base_dir)

        # scope == "all"
        label = root_label or "전체 노트"
        base_dir = target_root / self._safe_dir_name(label)
        base_dir.mkdir(parents=True, exist_ok=True)
        all_folders = self._folders.get_all()
        folder_ids = [f["id"] for f in all_folders]
        return self._export_tree(folder_ids, base_dir, fmt, label, root_id=None, progress_callback=progress_callback)

    # ── Tree export (preserves folder hierarchy) ───────────────────────────
    def _export_tree(
        self,
        folder_ids: List[str],
        base_dir: Path,
        fmt: str,
        label: str,
        root_id: Optional[str],
        progress_callback=None,
    ) -> Dict[str, Any]:
        all_folders_map = {f["id"]: f for f in self._folders.get_all()}
        rel_paths = self._build_relative_paths(folder_ids, all_folders_map, root_id)

        notes = self._notes.get_all_by_folder_ids(folder_ids)
        total_notes = len(notes)
        files: List[str] = []
        failures: List[Dict[str, str]] = []
        used_names: Dict[Path, set] = {}

        for idx, note in enumerate(notes):
            sub_rel = rel_paths.get(note.get("folder_id"), Path(""))
            sub_dir = base_dir / sub_rel
            title = note.get("title") or "무제"
            if progress_callback:
                progress_callback(idx + 1, total_notes, f"보내는 중: {title}")
            try:
                sub_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                failures.append(
                    {"title": title, "error": f"폴더 생성 실패: {exc}"}
                )
                continue

            written = self._export_one(note, sub_dir, fmt, used_names)
            if written:
                files.append(written)
            else:
                failures.append(
                    {"title": title, "error": "변환 실패"}
                )

        return self._summary(label, files, failures, base_dir)

    # ── Flat export (no hierarchy) ─────────────────────────────────────────
    def _export_flat(
        self, notes: List[Dict[str, Any]], target_dir: Path, fmt: str, progress_callback=None
    ) -> Tuple[List[str], List[Dict[str, str]]]:
        total_notes = len(notes)
        files: List[str] = []
        failures: List[Dict[str, str]] = []
        used_names: Dict[Path, set] = {}

        for idx, note in enumerate(notes):
            title = note.get("title") or "무제"
            if progress_callback:
                progress_callback(idx + 1, total_notes, f"보내는 중: {title}")
            written = self._export_one(note, target_dir, fmt, used_names)
            if written:
                files.append(written)
            else:
                failures.append(
                    {"title": title, "error": "변환 실패"}
                )
        return files, failures

    # ── Per-note conversion ────────────────────────────────────────────────
    def _export_one(
        self,
        note: Dict[str, Any],
        sub_dir: Path,
        fmt: str,
        used_names: Dict[Path, set],
    ) -> Optional[str]:
        base_name = self._exporter.safe_filename(note.get("title") or "무제")
        unique_name = self._dedupe_name(used_names, sub_dir, base_name, fmt)

        try:
            output_path = self._exporter.export(
                title=note.get("title") or "",
                markdown=note.get("content") or "",
                content_json=note.get("content_json") or "",
                fmt=fmt,
                out_dir=str(sub_dir),
            )
        except Exception:
            return None

        produced = Path(output_path)
        target = sub_dir / f"{unique_name}.{fmt}"
        if produced != target:
            try:
                if target.exists():
                    target.unlink()
                produced.rename(target)
                return str(target)
            except Exception:
                return str(produced)
        return str(produced)

    # ── Helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _build_relative_paths(
        folder_ids: List[str],
        all_folders_map: Dict[str, Dict[str, Any]],
        root_id: Optional[str],
    ) -> Dict[str, Path]:
        """Compute each folder's relative path under the export base directory.

        - When ``root_id`` is provided, the root folder maps to ``Path("")`` so
          its notes go directly under base_dir, and descendants reflect the
          remaining hierarchy.
        - When ``root_id`` is None (library-wide), the entire chain up to the
          top-level folder is preserved.
        """
        rel: Dict[str, Path] = {}
        for fid in folder_ids:
            chain: List[str] = []
            cur: Optional[str] = fid
            while cur and cur in all_folders_map and cur != root_id:
                name = all_folders_map[cur].get("name") or "무제 폴더"
                chain.append(FolderExportService._safe_dir_name(name))
                cur = all_folders_map[cur].get("parent_id")
            chain.reverse()
            rel[fid] = Path(*chain) if chain else Path("")
        return rel

    @staticmethod
    def _dedupe_name(
        used: Dict[Path, set], sub_dir: Path, base_name: str, fmt: str
    ) -> str:
        bucket = used.setdefault(sub_dir, set())
        candidate = base_name
        n = 2
        while candidate.lower() in bucket or (sub_dir / f"{candidate}.{fmt}").exists():
            candidate = f"{base_name}_{n}"
            n += 1
        bucket.add(candidate.lower())
        return candidate

    @staticmethod
    def _safe_dir_name(name: str) -> str:
        return CurrentNoteExportService.safe_filename(name)

    @staticmethod
    def _summary(
        label: str,
        files: List[str],
        failures: List[Dict[str, str]],
        base_dir: Path,
    ) -> Dict[str, Any]:
        return {
            "label": label,
            "count": len(files),
            "failedCount": len(failures),
            "outputDir": str(base_dir),
            "files": files,
            "failures": failures,
        }
