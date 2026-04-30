from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import hwpx_importer as hi


class TestHWPXImporter(unittest.TestCase):
    def _make_hwpx(self, base_dir: Path, file_name: str, entries: dict[str, bytes]) -> Path:
        hwpx_path = base_dir / file_name
        with zipfile.ZipFile(hwpx_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, payload in entries.items():
                zf.writestr(name, payload)
        return hwpx_path

    def test_find_section_files_prefers_section_xml(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            hwpx = self._make_hwpx(
                root,
                "sample.hwpx",
                {
                    "Contents/content.xml": b"<doc/>",
                    "Contents/section1.xml": b"<doc/>",
                    "Contents/section0.xml": b"<doc/>",
                },
            )
            zf = hi._open_hwpx_zip(str(hwpx))
            self.assertIsNotNone(zf, "HWPX ZIP should open successfully for section scan test")
            assert zf is not None
            try:
                section_files = hi._find_section_files(zf)
            finally:
                zf.close()

            self.assertEqual(
                section_files,
                ["Contents/section0.xml", "Contents/section1.xml"],
                "Section discovery should prefer and sort section*.xml files",
            )

    def test_paragraph_text_extraction(self) -> None:
        xml = """
        <root xmlns='urn:test'>
          <sec>
            <p><t>첫째 문단</t></p>
            <p><t>둘째</t><lineBreak/><t>줄바꿈</t><tab/><t>탭</t></p>
          </sec>
        </root>
        """
        blocks = hi._parse_section_xml(xml, image_map={})
        md = hi._render_blocks_to_markdown(blocks)

        self.assertIn("첫째 문단", md, "Paragraph text should be extracted from <t> nodes")
        self.assertIn("둘째", md, "Second paragraph text should be preserved")
        self.assertIn("줄바꿈", md, "lineBreak content should remain readable")

    def test_clean_text_normalization(self) -> None:
        raw = "\ufeff가\u00a0나\u200b다\ufffd\x01\tA\n\n\n\nB"
        cleaned = hi._clean_text(raw)

        self.assertNotIn("\ufeff", cleaned, "BOM should be removed")
        self.assertNotIn("\u200b", cleaned, "Zero-width space should be removed")
        self.assertNotIn("\ufffd", cleaned, "Replacement character should be removed")
        self.assertNotIn("\x01", cleaned, "Unsafe control chars should be removed")
        self.assertIn("가 나다", cleaned, "NBSP should normalize to regular spacing")
        self.assertNotIn("\t", cleaned, "Tab characters should not remain after markdown spacing normalization")
        self.assertIn("A", cleaned, "Text next to tab should remain after normalization")
        self.assertNotIn("\n\n\n", cleaned, "Consecutive blank lines must be capped at two")

    def test_image_extraction_and_markdown_insertion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            assets = root / "assets"
            section_xml = """
            <root>
              <sec>
                <p><t>이미지 앞</t></p>
                <p><pic binRef='image1'/></p>
              </sec>
            </root>
            """.encode("utf-8")
            hwpx = self._make_hwpx(
                root,
                "img.hwpx",
                {
                    "Contents/section0.xml": section_xml,
                    "BinData/image1.png": b"\x89PNG\r\n\x1a\n",
                },
            )

            md = hi.hwpx_to_markdown(str(hwpx), assets_dir=str(assets))
            extracted_file = assets / "imported_001.png"

            self.assertTrue(extracted_file.exists(), "Image should be extracted to the target assets directory")
            self.assertIn("![image](", md, "Markdown should include extracted image syntax")
            self.assertIn("imported_001.png", md, "Markdown image path should point to extracted file name")

    def test_simple_table_to_markdown(self) -> None:
        xml = """
        <root>
          <sec>
            <tbl>
              <tr><td><p><t>제목1</t></p></td><td><p><t>제목2</t></p></td></tr>
              <tr><td><p><t>내용1</t></p></td><td><p><t>내용2</t></p></td></tr>
            </tbl>
          </sec>
        </root>
        """
        blocks = hi._parse_section_xml(xml, image_map={})
        md = hi._render_blocks_to_markdown(blocks)

        self.assertIn("| 제목1 | 제목2 |", md, "Simple table header should render as GFM header row")
        self.assertIn("|---|---|", md, "Simple table should include GFM separator row")
        self.assertIn("| 내용1 | 내용2 |", md, "Simple table body rows should be rendered")

    def test_complex_table_to_html(self) -> None:
        xml = """
        <root>
          <sec>
            <tbl>
              <tr>
                <td rowSpan='2'><p><t>구분</t></p></td>
                <td><p><t>1월</t></p></td>
              </tr>
              <tr>
                <td><p><t>2월</t></p></td>
              </tr>
            </tbl>
          </sec>
        </root>
        """
        blocks = hi._parse_section_xml(xml, image_map={})
        md = hi._render_blocks_to_markdown(blocks)

        self.assertIn("<table>", md, "Complex table should be preserved as HTML table")
        self.assertIn('rowspan="2"', md, "rowSpan should be reflected in HTML output")
        self.assertIn("</table>", md, "Complex table HTML should be well-formed and closed")

    def test_broken_xml_or_missing_section_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            missing_section_hwpx = self._make_hwpx(root, "missing.hwpx", {"DocInfo/header.xml": b"<doc/>"})
            broken_xml_hwpx = self._make_hwpx(
                root,
                "broken.hwpx",
                {"Contents/section0.xml": b"<root><sec><p><t>broken"},
            )

            for path in (missing_section_hwpx, broken_xml_hwpx):
                with self.subTest(path=path.name):
                    try:
                        md = hi.hwpx_to_markdown(str(path))
                    except Exception as exc:  # pragma: no cover
                        self.fail(f"Importer must not raise for invalid/missing XML: {path.name}, error={exc}")
                    self.assertIsInstance(md, str, "Fallback result should always be a string")


if __name__ == "__main__":
    unittest.main()
