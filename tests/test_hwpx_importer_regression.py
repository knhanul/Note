"""HWPX importer regression tests.

These tests verify that the current HWPX import behavior remains stable.
Quality improvements will be added in later phases.
"""

import tempfile
import unittest
from pathlib import Path

from tests.helpers.hwpx_fixture_builder import (
    create_broken_hwpx,
    create_empty_hwpx,
    create_hwpx_with_bullet_list,
    create_hwpx_with_empty_notes,
    create_hwpx_with_endnote,
    create_hwpx_with_footnote,
    create_hwpx_with_footnote_and_endnote,
    create_hwpx_with_heading_paragraphs,
    create_hwpx_with_header_footer,
    create_hwpx_with_image_reference_by_filename,
    create_hwpx_with_image_reference_by_stem,
    create_hwpx_with_multiple_images_and_ambiguous_reference,
    create_hwpx_with_merged_cell_table,
    create_hwpx_with_mismatched_table,
    create_hwpx_with_mixed_list_and_paragraphs,
    create_hwpx_with_nested_list_hint,
    create_hwpx_with_numbered_list,
    create_hwpx_with_section_xml,
    create_hwpx_with_table,
    create_hwpx_with_table_with_newline,
    create_hwpx_with_table_with_pipe,
    create_hwpx_with_image_placeholder,
    create_hwpx_with_unresolved_image_reference,
    create_hwpx_with_unused_extracted_image,
    create_hwpx_without_section,
    create_minimal_hwpx,
)


class HwpxImporterRegressionTest(unittest.TestCase):
    def test_minimal_paragraph(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_minimal_hwpx(tmp_path, "테스트 문단")

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)

    def test_section_xml_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_without_section(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)

    def test_broken_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_broken_hwpx(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)

    def test_basic_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_table(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("|", result)

    def test_image_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_image_placeholder(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)

    def test_empty_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_empty_hwpx(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)

    def test_heading_style_paragraph(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_heading_paragraphs(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("# 제목입니다", result)
            self.assertIn("## 소제목입니다", result)

    def test_heading_level_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_heading_paragraphs(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("# ", result)
            self.assertIn("## ", result)
            self.assertNotIn("####### ", result)

    def test_paragraph_order_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_heading_paragraphs(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            title_pos = result.find("제목입니다")
            para1_pos = result.find("일반 문단입니다")
            heading2_pos = result.find("소제목입니다")
            para2_pos = result.find("또 다른 일반 문단입니다")
            self.assertGreater(title_pos, -1)
            self.assertGreater(para1_pos, title_pos)
            self.assertGreater(heading2_pos, para1_pos)
            self.assertGreater(para2_pos, heading2_pos)

    def test_non_heading_paragraph_not_converted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_minimal_hwpx(tmp_path, "일반 문단")

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertNotIn("#", result)

    def test_basic_table_markdown_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_table(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("|", result)
            self.assertIn("---", result)
            self.assertIn("헤더1", result)
            self.assertIn("헤더2", result)

    def test_table_cell_pipe_escaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_table_with_pipe(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("\\|", result)
            self.assertIn("값\\|데이터", result)

    def test_table_cell_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_table_with_newline(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertNotIn("<br>", result)
            self.assertIn("|", result)

    def test_mismatched_row_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_mismatched_table(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("|", result)

    def test_merged_cell_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_merged_cell_table(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("<table>", result)

    def test_bullet_list_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_bullet_list(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("- ", result)
            self.assertIn("첫 번째 항목", result)

    def test_numbered_list_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_numbered_list(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("1. ", result)
            self.assertIn("첫 번째", result)

    def test_normal_paragraph_not_converted_to_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_minimal_hwpx(tmp_path, "일반 문단")

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertNotIn("- ", result)
            self.assertNotIn("1. ", result)

    def test_mixed_list_and_paragraph_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_mixed_list_and_paragraphs(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            para_pos = result.find("일반 문단입니다")
            list_pos = result.find("목록 항목")
            self.assertGreater(para_pos, -1)
            self.assertGreater(list_pos, para_pos)

    def test_nested_list_indentation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_nested_list_hint(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("  - ", result)
            self.assertIn("    - ", result)

    def test_heading_not_converted_to_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_heading_paragraphs(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("#", result)
            self.assertNotIn("- ", result)

    def test_image_reference_by_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_image_reference_by_filename(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("![", result)

    def test_image_reference_by_stem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_image_reference_by_stem(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("![", result)

    def test_unresolved_image_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_unresolved_image_reference(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertNotIn("![]()", result)

    def test_ambiguous_multiple_image_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_multiple_images_and_ambiguous_reference(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)

    def test_unused_extracted_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_unused_extracted_image(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("추출된 이미지", result)

    def test_footnote_section_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_footnote(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("## 각주", result)
            self.assertIn("1.", result)

    def test_endnote_section_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_endnote(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("## 미주", result)
            self.assertIn("1.", result)

    def test_footnote_and_endnote_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_footnote_and_endnote(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("## 각주", result)
            self.assertIn("## 미주", result)

    def test_no_notes_no_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_minimal_hwpx(tmp_path, "테스트")

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertNotIn("## 각주", result)
            self.assertNotIn("## 미주", result)

    def test_empty_notes_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_empty_notes(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertNotIn("## 각주", result)
            self.assertNotIn("## 미주", result)

    def test_header_footer_warning_logged(self):
        import logging
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hwpx_path = create_hwpx_with_header_footer(tmp_path)

            from services.hwpx_importer import hwpx_to_markdown

            with self.assertLogs("services.hwpx_importer", level=logging.WARNING) as cm:
                result = hwpx_to_markdown(str(hwpx_path))

            self.assertIsInstance(result, str)
            self.assertIn("HEADER_FOOTER_IGNORED", " ".join(cm.output))


if __name__ == "__main__":
    unittest.main()
