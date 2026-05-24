"""Import/export compatibility layer for Note2.

This package currently re-exports existing services without changing import,
export, conversion, file path, or database behavior.
"""

from .conversion_diagnostics import (
    ConversionDiagnosticResult,
    check_hwp_com_available,
    check_hwp_import_environment,
    check_pywin32_available,
)
from .current_note_exporter import CurrentNoteExporter, CurrentNoteExportService
from .folder_exporter import FolderExporter, FolderExportService
from .folder_importer import FolderImporter, FolderImportService
from .hwp_converter import convert_hwp_to_hwpx_via_com
from .hwp_import_service import convert_hwp_to_markdown_text, import_hwpx_as_markdown_text
from .hwpx_import_service import convert_hwpx_to_markdown_text, import_hwpx_as_markdown_document
from .hwpx_importer import (
    HWPXDocument,
    ImageBlock,
    ParagraphBlock,
    TableBlock,
    UnknownBlock,
    hwpx_to_markdown,
)
from .markdown_import_service import load_markdown_document, load_markdown_document_from_text
from .markdown_export_service import (
    build_markdown_export_content,
    make_safe_markdown_filename,
    resolve_unique_filename,
    write_markdown_file,
)

__all__ = [
    "ConversionDiagnosticResult",
    "check_hwp_com_available",
    "check_hwp_import_environment",
    "check_pywin32_available",
    "CurrentNoteExporter",
    "CurrentNoteExportService",
    "FolderExporter",
    "FolderExportService",
    "FolderImporter",
    "FolderImportService",
    "convert_hwp_to_hwpx_via_com",
    "convert_hwp_to_markdown_text",
    "convert_hwpx_to_markdown_text",
    "import_hwpx_as_markdown_document",
    "import_hwpx_as_markdown_text",
    "HWPXDocument",
    "ImageBlock",
    "ParagraphBlock",
    "TableBlock",
    "UnknownBlock",
    "hwpx_to_markdown",
    "load_markdown_document",
    "load_markdown_document_from_text",
    "build_markdown_export_content",
    "make_safe_markdown_filename",
    "resolve_unique_filename",
    "write_markdown_file",
]
