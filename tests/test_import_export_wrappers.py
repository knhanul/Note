import importlib
import unittest

from packages.import_export.current_note_exporter import CurrentNoteExporter, CurrentNoteExportService
from packages.import_export.folder_exporter import FolderExporter, FolderExportService
from packages.import_export.folder_importer import FolderImporter, FolderImportService
from packages.import_export.hwp_converter import convert_hwp_to_hwpx_via_com
from packages.import_export.hwpx_import_service import convert_hwpx_to_markdown_text
from packages.import_export.hwpx_importer import HWPXDocument, hwpx_to_markdown
from services.current_note_export_service import CurrentNoteExportService as ServiceCurrentNoteExportService
from services.folder_export_service import FolderExportService as ServiceFolderExportService
from services.folder_import_service import FolderImportService as ServiceFolderImportService


class ImportExportWrappersTest(unittest.TestCase):
    def test_wrapper_modules_import(self):
        module_names = [
            "packages.import_export.current_note_exporter",
            "packages.import_export.folder_exporter",
            "packages.import_export.folder_importer",
            "packages.import_export.hwp_converter",
            "packages.import_export.hwpx_importer",
            "packages.import_export.hwpx_import_service",
        ]

        for module_name in module_names:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_exporter_aliases_reexport_existing_services(self):
        self.assertIs(CurrentNoteExporter, CurrentNoteExportService)
        self.assertIs(CurrentNoteExportService, ServiceCurrentNoteExportService)
        self.assertIs(FolderExporter, FolderExportService)
        self.assertIs(FolderExportService, ServiceFolderExportService)
        self.assertIs(FolderImporter, FolderImportService)
        self.assertIs(FolderImportService, ServiceFolderImportService)

    def test_conversion_symbols_import_without_running_conversion(self):
        self.assertTrue(callable(convert_hwp_to_hwpx_via_com))
        self.assertTrue(callable(hwpx_to_markdown))
        self.assertTrue(callable(convert_hwpx_to_markdown_text))
        self.assertIsNotNone(HWPXDocument)


if __name__ == "__main__":
    unittest.main()
