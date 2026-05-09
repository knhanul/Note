"""Smoke-check import/export compatibility wrappers without touching files or DB."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.import_export.current_note_exporter import (
    CurrentNoteExporter,
    CurrentNoteExportService,
)
from packages.import_export.folder_exporter import FolderExporter, FolderExportService
from packages.import_export.folder_importer import FolderImporter, FolderImportService
from packages.import_export.hwp_converter import convert_hwp_to_hwpx_via_com
from packages.import_export.hwpx_importer import HWPXDocument, hwpx_to_markdown


def main() -> None:
    assert CurrentNoteExporter is CurrentNoteExportService
    assert FolderExporter is FolderExportService
    assert FolderImporter is FolderImportService
    assert callable(convert_hwp_to_hwpx_via_com)
    assert callable(hwpx_to_markdown)
    assert HWPXDocument is not None
    print("import_export imports ok")


if __name__ == "__main__":
    main()
