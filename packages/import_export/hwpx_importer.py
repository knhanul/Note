"""Compatibility wrapper for HWPX import helpers."""

from services.hwpx_importer import (
    HWPXDocument,
    ImageBlock,
    ParagraphBlock,
    TableBlock,
    UnknownBlock,
    hwpx_to_markdown,
)

__all__ = [
    "HWPXDocument",
    "ImageBlock",
    "ParagraphBlock",
    "TableBlock",
    "UnknownBlock",
    "hwpx_to_markdown",
]
