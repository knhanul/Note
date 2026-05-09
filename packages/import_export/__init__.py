"""Import/export compatibility layer for Note2.

This package currently re-exports existing services without changing import,
export, conversion, file path, or database behavior.
"""

from .current_note_exporter import CurrentNoteExporter, CurrentNoteExportService
from .folder_exporter import FolderExporter, FolderExportService
from .folder_importer import FolderImporter, FolderImportService
from .hwp_converter import convert_hwp_to_hwpx_via_com
from .hwpx_importer import (
    HWPXDocument,
    ImageBlock,
    ParagraphBlock,
    TableBlock,
    UnknownBlock,
    hwpx_to_markdown,
)

__all__ = [
    "CurrentNoteExporter",
    "CurrentNoteExportService",
    "FolderExporter",
    "FolderExportService",
    "FolderImporter",
    "FolderImportService",
    "convert_hwp_to_hwpx_via_com",
    "HWPXDocument",
    "ImageBlock",
    "ParagraphBlock",
    "TableBlock",
    "UnknownBlock",
    "hwpx_to_markdown",
]
