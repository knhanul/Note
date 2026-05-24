"""Markdown import service for Note2.

This module provides pure Markdown file parsing capabilities.
It re-uses parse_markdown_document() and extract_markdown_assets() from services.
"""

from pathlib import Path
from typing import Optional, Tuple

from services.markdown_asset_resolver import extract_markdown_assets
from services.markdown_document_model import MarkdownDocument
from services.markdown_front_matter import parse_markdown_document


def load_markdown_document(file_path: str) -> Tuple[MarkdownDocument, list[str]]:
    """Load a Markdown file and parse it into a MarkdownDocument.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        Tuple of (MarkdownDocument, asset_warnings).

    Note:
        This function only handles file reading and parsing.
        It does NOT handle:
        - Note DB storage
        - Folder creation/mapping
        - Image file copying
        - note_images upsert
        - note-image:// token replacement
    """
    path = Path(file_path)
    text = _read_text(path)
    doc = parse_markdown_document(text, source_path=str(path))

    _, asset_warnings = extract_markdown_assets(doc.body_markdown, base_path=str(path))

    return doc, asset_warnings


def load_markdown_document_from_text(text: str, source_path: Optional[str] = None) -> Tuple[MarkdownDocument, list[str]]:
    """Parse Markdown text directly into a MarkdownDocument.

    Args:
        text: Markdown content as string.
        source_path: Optional source file path for relative path resolution.

    Returns:
        Tuple of (MarkdownDocument, asset_warnings).
    """
    doc = parse_markdown_document(text, source_path=source_path or "")

    _, asset_warnings = extract_markdown_assets(doc.body_markdown, base_path=source_path or "")

    return doc, asset_warnings


def _read_text(fpath: Path) -> str:
    """Read text file with encoding fallback."""
    for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"):
        try:
            return fpath.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return fpath.read_text(encoding="utf-8", errors="ignore")


__all__ = [
    "load_markdown_document",
    "load_markdown_document_from_text",
]
