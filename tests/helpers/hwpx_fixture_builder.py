"""Synthetic HWPX fixture builder for testing.

This module provides utilities to create minimal HWPX files for testing
without using real business documents.
"""

import io
import zipfile
from pathlib import Path
from typing import Optional


def create_minimal_hwpx(tmp_path: Path, body_text: str = "테스트 문단") -> Path:
    """Create a minimal HWPX with a single paragraph.

    Args:
        tmp_path: Directory to create the file in.
        body_text: Text content for the paragraph.

    Returns:
        Path to the created .hwpx file.
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>{body_text}</t></p>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "minimal.hwpx")


def create_hwpx_with_section_xml(
    tmp_path: Path,
    section_xml: str,
    filename: str = "sample.hwpx"
) -> Path:
    """Create an HWPX file with custom section XML.

    Args:
        tmp_path: Directory to create the file in.
        section_xml: XML content for the section file.
        filename: Name of the output file.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / filename
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", section_xml.encode("utf-8"))
    return output_path


def create_broken_hwpx(tmp_path: Path) -> Path:
    """Create a broken HWPX file (invalid zip).

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created broken .hwpx file.
    """
    output_path = tmp_path / "broken.hwpx"
    output_path.write_text("this is not a valid zip file", encoding="utf-8")
    return output_path


def create_hwpx_without_section(tmp_path: Path) -> Path:
    """Create an HWPX file without section XML.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "no_section.hwpx"
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
    return output_path


def create_hwpx_with_table(tmp_path: Path) -> Path:
    """Create an HWPX with a basic table.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <tbl>
    <tr>
      <td><t>헤더1</t></td>
      <td><t>헤더2</t></td>
    </tr>
    <tr>
      <td><t>셀1</t></td>
      <td><t>셀2</t></td>
    </tr>
  </tbl>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "table.hwpx")


def create_hwpx_with_table_with_pipe(tmp_path: Path) -> Path:
    """Create an HWPX with a table containing pipe character in cell.

    This is a synthetic test structure for pipe escaping.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <tbl>
    <tr>
      <td><t>이름</t></td>
      <td><t>값|데이터</t></td>
    </tr>
    <tr>
      <td><t>A</t></td>
      <td><t>1|2|3</t></td>
    </tr>
  </tbl>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "table_pipe.hwpx")


def create_hwpx_with_table_with_newline(tmp_path: Path) -> Path:
    """Create an HWPX with a table containing line breaks in cells.

    This is a synthetic test structure for cell newline handling.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <tbl>
    <tr>
      <td><t>제목</t></td>
      <td><t>설명</t></td>
    </tr>
    <tr>
      <td><t>첫 번째</t><lb/><t>두 번째 줄</t></td>
      <td><t>줄1</t><lb/><t>줄2</t></td>
    </tr>
  </tbl>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "table_newline.hwpx")


def create_hwpx_with_mismatched_table(tmp_path: Path) -> Path:
    """Create an HWPX with a table where rows have different column counts.

    This is a synthetic test structure for mismatched row length handling.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <tbl>
    <tr>
      <td><t>컬럼1</t></td>
      <td><t>컬럼2</t></td>
      <td><t>컬럼3</t></td>
    </tr>
    <tr>
      <td><t>데이터1</t></td>
      <td><t>데이터2</t></td>
    </tr>
    <tr>
      <td><t>데이터A</t></td>
    </tr>
  </tbl>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "table_mismatch.hwpx")


def create_hwpx_with_merged_cell_table(tmp_path: Path) -> Path:
    """Create an HWPX with a table containing merged cells (rowspan/colspan).

    This is a synthetic test structure for merged cell fallback.
    The importer should detect colspan and use HTML table fallback.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <tbl>
    <tr>
      <td colSpan="2"><t>병합 헤더</t></td>
    </tr>
    <tr>
      <td><t>셀1</t></td>
      <td><t>셀2</t></td>
    </tr>
  </tbl>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "table_merged.hwpx")


def create_hwpx_with_image_placeholder(tmp_path: Path) -> Path:
    """Create an HWPX with an image reference placeholder.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>문단 시작</t><pic binData="image1"/><t>문단 끝</t></p>
</body>
"""
    output_path = tmp_path / "image.hwpx"
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", xml.encode("utf-8"))
        zf.writestr("BinData/image1.png", b"\x89PNG\r\n\x1a\n")
    return output_path


def create_empty_hwpx(tmp_path: Path) -> Path:
    """Create an empty HWPX file.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "empty.hwpx")


def create_hwpx_with_heading_paragraphs(tmp_path: Path) -> Path:
    """Create an HWPX with heading and paragraph styles.

    This is a synthetic test structure with style attributes that
    the importer can recognize as heading hints.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p style="Heading 1"><t>제목입니다</t></p>
  <p><t>일반 문단입니다</t></p>
  <p style="Heading 2"><t>소제목입니다</t></p>
  <p><t>또 다른 일반 문단입니다</t></p>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "heading.hwpx")


def create_hwpx_with_bullet_list(tmp_path: Path) -> Path:
    """Create an HWPX with bullet list items.

    This is a synthetic test structure for bullet list detection.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p style="bullet"><t>첫 번째 항목</t></p>
  <p style="bullet"><t>두 번째 항목</t></p>
  <p style="bullet"><t>세 번째 항목</t></p>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "bullet_list.hwpx")


def create_hwpx_with_numbered_list(tmp_path: Path) -> Path:
    """Create an HWPX with numbered list items.

    This is a synthetic test structure for numbered list detection.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p style="number"><t>첫 번째</t></p>
  <p style="number"><t>두 번째</t></p>
  <p style="numbered"><t>세 번째</t></p>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "numbered_list.hwpx")


def create_hwpx_with_mixed_list_and_paragraphs(tmp_path: Path) -> Path:
    """Create an HWPX with mixed paragraphs and list items.

    This is a synthetic test structure for mixed content.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>일반 문단입니다</t></p>
  <p style="bullet"><t>목록 항목 1</t></p>
  <p style="bullet"><t>목록 항목 2</t></p>
  <p><t>또 다른 일반 문단입니다</t></p>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "mixed_list.hwpx")


def create_hwpx_with_nested_list_hint(tmp_path: Path) -> Path:
    """Create an HWPX with nested list items (level hint).

    This is a synthetic test structure for nested list indentation.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p style="bullet" level="0"><t>첫 번째 수준</t></p>
  <p style="bullet" level="1"><t>두 번째 수준</t></p>
  <p style="bullet" level="2"><t>세 번째 수준</t></p>
</body>
"""
    return create_hwpx_with_section_xml(tmp_path, xml, "nested_list.hwpx")


def create_hwpx_with_image_reference_by_filename(tmp_path: Path) -> Path:
    """Create an HWPX with image reference by filename.

    This is a synthetic test structure for image reference by filename.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "image_file.hwpx"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>문단 시작</t><pic binData="test001.png"/><t>문단 끝</t></p>
</body>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", xml.encode("utf-8"))
        zf.writestr("BinData/test001.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
    return output_path


def create_hwpx_with_image_reference_by_stem(tmp_path: Path) -> Path:
    """Create an HWPX with image reference by stem (without extension).

    This is a synthetic test structure for image reference by stem.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "image_stem.hwpx"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>문단 시작</t><pic binData="test002"/><t>문단 끝</t></p>
</body>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", xml.encode("utf-8"))
        zf.writestr("BinData/test002.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
    return output_path


def create_hwpx_with_unresolved_image_reference(tmp_path: Path) -> Path:
    """Create an HWPX with unresolved image reference.

    This is a synthetic test structure for unresolved image reference.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "image_unresolved.hwpx"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>문단 시작</t><pic binData="nonexistent.png"/><t>문단 끝</t></p>
</body>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", xml.encode("utf-8"))
    return output_path


def create_hwpx_with_multiple_images_and_ambiguous_reference(tmp_path: Path) -> Path:
    """Create an HWPX with multiple images and ambiguous reference.

    This is a synthetic test structure for ambiguous image reference.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "image_ambiguous.hwpx"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>문단 시작</t><pic binData="image"/><t>문단 끝</t></p>
</body>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", xml.encode("utf-8"))
        zf.writestr("BinData/image1.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
        zf.writestr("BinData/image2.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 10)
    return output_path


def create_hwpx_with_unused_extracted_image(tmp_path: Path) -> Path:
    """Create an HWPX with image that is not referenced in body.

    This is a synthetic test structure for unused extracted image.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "image_unused.hwpx"
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>이미지 없이 일반 문단만 있음</t></p>
</body>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", xml.encode("utf-8"))
        zf.writestr("BinData/unused.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
    return output_path


def create_hwpx_with_footnote(tmp_path: Path) -> Path:
    """Create an HWPX with footnotes.

    This is a synthetic test structure for footnote detection.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "footnote.hwpx"
    body_xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>본문 내용입니다</t></p>
</body>
"""
    footnote_xml = """<?xml version="1.0" encoding="UTF-8"?>
<footnotes>
  <footnote>
    <t>첫 번째 각주입니다</t>
  </footnote>
  <footnote>
    <t>두 번째 각주입니다</t>
  </footnote>
</footnotes>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", body_xml.encode("utf-8"))
        zf.writestr("Contents/footnote.xml", footnote_xml.encode("utf-8"))
    return output_path


def create_hwpx_with_endnote(tmp_path: Path) -> Path:
    """Create an HWPX with endnotes.

    This is a synthetic test structure for endnote detection.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "endnote.hwpx"
    body_xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>본문 내용입니다</t></p>
</body>
"""
    endnote_xml = """<?xml version="1.0" encoding="UTF-8"?>
<endnotes>
  <endnote>
    <t>첫 번째 미주입니다</t>
  </endnote>
  <endnote>
    <t>두 번째 미주입니다</t>
  </endnote>
</endnotes>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", body_xml.encode("utf-8"))
        zf.writestr("Contents/endnote.xml", endnote_xml.encode("utf-8"))
    return output_path


def create_hwpx_with_footnote_and_endnote(tmp_path: Path) -> Path:
    """Create an HWPX with both footnotes and endnotes.

    This is a synthetic test structure for both note types.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "footnote_endnote.hwpx"
    body_xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>본문 내용입니다</t></p>
</body>
"""
    footnote_xml = """<?xml version="1.0" encoding="UTF-8"?>
<footnotes>
  <footnote>
    <t>각주 내용</t>
  </footnote>
</footnotes>
"""
    endnote_xml = """<?xml version="1.0" encoding="UTF-8"?>
<endnotes>
  <endnote>
    <t>미주 내용</t>
  </endnote>
</endnotes>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", body_xml.encode("utf-8"))
        zf.writestr("Contents/footnote.xml", footnote_xml.encode("utf-8"))
        zf.writestr("Contents/endnote.xml", endnote_xml.encode("utf-8"))
    return output_path


def create_hwpx_with_empty_notes(tmp_path: Path) -> Path:
    """Create an HWPX with empty note files.

    This is a synthetic test structure for empty notes.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "empty_notes.hwpx"
    body_xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>본문 내용입니다</t></p>
</body>
"""
    empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
<root></root>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", body_xml.encode("utf-8"))
        zf.writestr("Contents/footnote.xml", empty_xml.encode("utf-8"))
        zf.writestr("Contents/endnote.xml", empty_xml.encode("utf-8"))
    return output_path


def create_hwpx_with_header_footer(tmp_path: Path) -> Path:
    """Create an HWPX with header and footer content.

    This is a synthetic test structure for header/footer detection.

    Args:
        tmp_path: Directory to create the file in.

    Returns:
        Path to the created .hwpx file.
    """
    output_path = tmp_path / "header_footer.hwpx"
    body_xml = """<?xml version="1.0" encoding="UTF-8"?>
<body>
  <p><t>본문 내용입니다</t></p>
</body>
"""
    header_xml = """<?xml version="1.0" encoding="UTF-8"?>
<header>
  <p><t>머리말 내용입니다</t></p>
</header>
"""
    footer_xml = """<?xml version="1.0" encoding="UTF-8"?>
<footer>
  <p><t>꼬리말 내용입니다</t></p>
</footer>
"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("DocInfo.xml", "<?xml version='1.0'?><DocInfo/>")
        zf.writestr("Contents/section0.xml", body_xml.encode("utf-8"))
        zf.writestr("Contents/header.xml", header_xml.encode("utf-8"))
        zf.writestr("Contents/footer.xml", footer_xml.encode("utf-8"))
    return output_path


__all__ = [
    "create_minimal_hwpx",
    "create_hwpx_with_section_xml",
    "create_broken_hwpx",
    "create_hwpx_without_section",
    "create_hwpx_with_table",
    "create_hwpx_with_table_with_pipe",
    "create_hwpx_with_table_with_newline",
    "create_hwpx_with_mismatched_table",
    "create_hwpx_with_merged_cell_table",
    "create_hwpx_with_image_placeholder",
    "create_hwpx_with_image_reference_by_filename",
    "create_hwpx_with_image_reference_by_stem",
    "create_hwpx_with_unresolved_image_reference",
    "create_hwpx_with_multiple_images_and_ambiguous_reference",
    "create_hwpx_with_unused_extracted_image",
    "create_hwpx_with_footnote",
    "create_hwpx_with_endnote",
    "create_hwpx_with_footnote_and_endnote",
    "create_hwpx_with_empty_notes",
    "create_hwpx_with_header_footer",
    "create_empty_hwpx",
    "create_hwpx_with_heading_paragraphs",
    "create_hwpx_with_bullet_list",
    "create_hwpx_with_numbered_list",
    "create_hwpx_with_mixed_list_and_paragraphs",
    "create_hwpx_with_nested_list_hint",
]
