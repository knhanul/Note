"""HWPX import service for Note2.

This module provides HWPX file import capabilities by reusing existing
hwpx_importer.
"""

from pathlib import Path
from typing import Optional, Tuple

from services.hwpx_importer import hwpx_to_markdown
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


HWPX_WARNING_CODES = {
    "FILE_NOT_FOUND": "HWPX_FILE_NOT_FOUND",
    "INVALID_EXTENSION": "HWPX_INVALID_EXTENSION",
    "BROKEN_ZIP": "HWPX_BROKEN_ZIP",
    "SECTION_NOT_FOUND": "HWPX_SECTION_NOT_FOUND",
    "XML_PARSE_FAILED": "HWPX_XML_PARSE_FAILED",
    "CONVERSION_EMPTY": "HWPX_CONVERSION_EMPTY",
    "CONVERSION_FAILED": "HWPX_CONVERSION_FAILED",
    "FALLBACK_USED": "HWPX_FALLBACK_USED",
    "IMPORT_FAILED": "HWPX_IMPORT_FAILED",
    "IMAGE_REF_UNRESOLVED": "IMAGE_REF_UNRESOLVED",
    "TABLE_MERGED_CELL_FALLBACK": "TABLE_MERGED_CELL_FALLBACK_HTML",
    "HEADER_FOOTER_IGNORED": "HEADER_FOOTER_IGNORED",
}


def _make_warning(code: str, message: str) -> str:
    """Create a standardized warning string with code prefix."""
    return f"[{code}] {message}"


def convert_hwpx_to_markdown_text(hwpx_path: str) -> Tuple[str, list[str]]:
    """Convert HWPX file to Markdown text.

    This function attempts to convert HWPX to Markdown using the existing
    hwpx_importer. If that fails, it falls back to gethwp (if available).

    Args:
        hwpx_path: Path to the HWPX file.

    Returns:
        Tuple of (markdown_text, warnings).
        Returns ("", [warning]) on failure.
    """
    warnings: list[str] = []
    path = Path(hwpx_path)

    if not path.exists():
        warnings.append(_make_warning("FILE_NOT_FOUND", f"HWPX file not found: {hwpx_path}"))
        return "", warnings

    if path.suffix.lower() != ".hwpx":
        warnings.append(_make_warning("INVALID_EXTENSION", f"Expected .hwpx file, got: {path.suffix}"))
        return "", warnings

    try:
        markdown = hwpx_to_markdown(hwpx_path)
        if markdown:
            return markdown, warnings
        warnings.append(_make_warning("CONVERSION_EMPTY", "HWPX to Markdown conversion returned empty result"))
    except Exception as exc:
        warnings.append(_make_warning("CONVERSION_FAILED", f"HWPX to Markdown conversion failed: {exc}"))

    fallback_markdown = _try_fallback_import(hwpx_path)
    if fallback_markdown:
        warnings.append(_make_warning("FALLBACK_USED", "Used fallback import (gethwp)"))
        return fallback_markdown, warnings

    warnings.append(_make_warning("IMPORT_FAILED", "HWPX import failed"))
    return "", warnings


def _try_fallback_import(hwpx_path: str) -> str:
    """Try fallback import via gethwp for HWPX."""
    try:
        import gethwp
        return gethwp.read_hwpx(hwpx_path) or ""
    except ImportError:
        return ""
    except Exception:
        return ""


def import_hwpx_as_markdown_document(hwpx_path: str) -> MarkdownDocument:
    """Import an HWPX file as a MarkdownDocument.

    This function wraps convert_hwpx_to_markdown_text() and returns
    the result as a MarkdownDocument object.

    Args:
        hwpx_path: Path to the HWPX file.

    Returns:
        MarkdownDocument with body_markdown, metadata, source_path, and warnings.
        On failure, returns MarkdownDocument with empty body_markdown and warnings.
    """
    try:
        markdown_text, warnings = convert_hwpx_to_markdown_text(hwpx_path)
    except Exception as exc:
        return MarkdownDocument(
            body_markdown="",
            metadata=MarkdownMetadata(title=Path(hwpx_path).stem if hwpx_path else None),
            source_path=hwpx_path,
            warnings=[_make_warning("IMPORT_FAILED", f"HWPX import failed: {exc}")],
        )

    path = Path(hwpx_path)
    title = path.stem if path.exists() else None

    return MarkdownDocument(
        body_markdown=markdown_text,
        metadata=MarkdownMetadata(title=title),
        source_path=hwpx_path,
        warnings=warnings,
    )


__all__ = [
    "convert_hwpx_to_markdown_text",
    "import_hwpx_as_markdown_document",
]
