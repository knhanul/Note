"""Markdown export service for Note2.

This module provides pure Markdown export capabilities.
It re-uses serialize_front_matter(), sanitize_filename(), and dedupe_filename() from services.
"""

from pathlib import Path
from typing import List, Optional

from services.markdown_document_model import MarkdownMetadata
from services.markdown_filename_policy import dedupe_filename, sanitize_filename
from services.markdown_front_matter import serialize_front_matter


def build_markdown_export_content(
    body_markdown: str,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    created_at: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> str:
    """Build Markdown export content with front matter.

    Args:
        body_markdown: The main Markdown body content.
        title: Optional title for front matter.
        tags: Optional list of tags.
        created_at: Optional creation timestamp.
        updated_at: Optional update timestamp.

    Returns:
        Complete Markdown content with front matter (if metadata present).
    """
    metadata = MarkdownMetadata(
        title=title,
        tags=tags if tags else [],
        created_at=created_at,
        updated_at=updated_at,
    )
    front_matter = serialize_front_matter(metadata)

    if metadata.title or metadata.tags or metadata.created_at or metadata.updated_at:
        return front_matter + "\n\n" + body_markdown
    return body_markdown


def make_safe_markdown_filename(title: str) -> str:
    """Create a safe filename from a title.

    Args:
        title: The note title.

    Returns:
        Safe filename string (without extension).
    """
    return sanitize_filename(title or "무제")


def resolve_unique_filename(
    base_name: str,
    existing_names: set,
) -> str:
    """Resolve a unique filename by adding suffix if needed.

    Args:
        base_name: Desired base filename (without extension).
        existing_names: Set of already-used filenames (lowercase).

    Returns:
        Unique filename that doesn't conflict with existing_names.
    """
    return dedupe_filename(base_name, existing_names)


def write_markdown_file(
    target_dir: Path,
    file_name: str,
    content: str,
) -> str:
    """Write Markdown content to a file.

    Args:
        target_dir: Directory to write the file.
        file_name: Filename (without extension, .md will be added).
        content: Markdown content to write.

    Returns:
        Full path to the written file.
    """
    out_path = target_dir / f"{file_name}.md"
    out_path.write_text(content, encoding="utf-8")
    return str(out_path)


__all__ = [
    "build_markdown_export_content",
    "make_safe_markdown_filename",
    "resolve_unique_filename",
    "write_markdown_file",
]
