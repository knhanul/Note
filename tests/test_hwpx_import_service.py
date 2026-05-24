"""HWPX import service tests.

These tests verify the packages/import_export/hwpx_import_service module.
"""

import tempfile
import unittest
from pathlib import Path

from tests.helpers.hwpx_fixture_builder import (
    create_broken_hwpx,
    create_minimal_hwpx,
)


class HwpxImportServiceTest(unittest.TestCase):
    def test_module_import(self):
        from packages.import_export.hwpx_import_service import convert_hwpx_to_markdown_text
        self.assertTrue(callable(convert_hwpx_to_markdown_text))

    def test_nonexistent_path(self):
        from packages.import_export.hwpx_import_service import convert_hwpx_to_markdown_text

        result = convert_hwpx_to_markdown_text("/nonexistent/path.hwpx")

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        markdown_text, warnings = result
        self.assertIsInstance(markdown_text, str)
        self.assertIsInstance(warnings, list)
        self.assertIn("not found", warnings[0])

    def test_invalid_extension(self):
        from packages.import_export.hwpx_import_service import convert_hwpx_to_markdown_text

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            txt_path = tmp_path / "test.txt"
            txt_path.write_text("test", encoding="utf-8")

            result = convert_hwpx_to_markdown_text(str(txt_path))

            markdown_text, warnings = result
            self.assertEqual(markdown_text, "")
            self.assertIn(".hwpx", warnings[0])

    def test_synthetic_minimal_hwpx(self):
        from packages.import_export.hwpx_import_service import convert_hwpx_to_markdown_text

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_minimal_hwpx(tmp_path, "테스트 문단")

            result = convert_hwpx_to_markdown_text(str(hwpx_path))

            self.assertIsInstance(result, tuple)
            markdown_text, warnings = result
            self.assertIsInstance(markdown_text, str)
            self.assertIsInstance(warnings, list)

    def test_broken_hwpx(self):
        from packages.import_export.hwpx_import_service import convert_hwpx_to_markdown_text

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_broken_hwpx(tmp_path)

            result = convert_hwpx_to_markdown_text(str(hwpx_path))

            markdown_text, warnings = result
            self.assertIsInstance(markdown_text, str)
            self.assertIsInstance(warnings, list)

    def test_import_hwpx_as_markdown_document_import(self):
        from packages.import_export.hwpx_import_service import import_hwpx_as_markdown_document
        self.assertTrue(callable(import_hwpx_as_markdown_document))

    def test_import_hwpx_as_markdown_document_minimal(self):
        from packages.import_export.hwpx_import_service import import_hwpx_as_markdown_document
        from services.markdown_document_model import MarkdownDocument

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_minimal_hwpx(tmp_path, "테스트 문단")

            doc = import_hwpx_as_markdown_document(str(hwpx_path))

            self.assertIsInstance(doc, MarkdownDocument)
            self.assertIsInstance(doc.body_markdown, str)
            self.assertIsInstance(doc.source_path, str)
            self.assertIsInstance(doc.warnings, list)
            self.assertIsInstance(doc.metadata.title, str)

    def test_import_hwpx_as_markdown_document_nonexistent(self):
        from packages.import_export.hwpx_import_service import import_hwpx_as_markdown_document
        from services.markdown_document_model import MarkdownDocument

        doc = import_hwpx_as_markdown_document("/nonexistent/path.hwpx")

        self.assertIsInstance(doc, MarkdownDocument)
        self.assertIsInstance(doc.warnings, list)
        self.assertTrue(any("HWPX" in w for w in doc.warnings))

    def test_import_hwpx_as_markdown_document_broken(self):
        from packages.import_export.hwpx_import_service import import_hwpx_as_markdown_document
        from services.markdown_document_model import MarkdownDocument

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_broken_hwpx(tmp_path)

            doc = import_hwpx_as_markdown_document(str(hwpx_path))

            self.assertIsInstance(doc, MarkdownDocument)
            self.assertIsInstance(doc.warnings, list)


if __name__ == "__main__":
    unittest.main()
