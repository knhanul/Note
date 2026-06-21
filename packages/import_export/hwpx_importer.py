"""Compatibility wrapper for HWPX import helpers."""

from services.hwpx_importer import (
    HWPXDocument,
    HeadingBlock,
    ImageBlock,
    ListItemBlock,
    ParagraphBlock,
    TableBlock,
    UnknownBlock,
    hwpx_to_markdown,
    parse_hwpx_document,
)

__all__ = [
    "HWPXDocument",
    "HeadingBlock",
    "ImageBlock",
    "ListItemBlock",
    "ParagraphBlock",
    "TableBlock",
    "UnknownBlock",
    "hwpx_to_markdown",
    "parse_hwpx_document",
]
