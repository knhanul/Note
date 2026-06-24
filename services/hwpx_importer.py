"""Incremental HWPX importer.

Developer flow:
1) open HWPX zip and extract image assets
2) parse section XML nodes into document blocks (paragraph/table/image)
3) render blocks into Markdown/HTML-safe output
"""
from __future__ import annotations

from dataclasses import dataclass, field
import html as html_mod
import logging
from pathlib import Path
import re
import tempfile
import unicodedata
from typing import List
import xml.etree.ElementTree as ET
import zipfile


logger = logging.getLogger(__name__)

__all__ = [
    "HWPXDocument",
    "ParagraphBlock",
    "HeadingBlock",
    "ListItemBlock",
    "ImageBlock",
    "TableBlock",
    "UnknownBlock",
    "hwpx_to_markdown",
    "parse_hwpx_document",
]

_TABLE_TAGS = {"tbl", "table"}
_ROW_TAGS = {"tr", "row"}
_CELL_TAGS = {"td", "tc", "cell"}
_IMAGE_TAGS = {"pic", "img", "image"}


@dataclass
class ParagraphBlock:
    text: str


@dataclass
class HeadingBlock:
    text: str
    level: int = 2


@dataclass
class ListItemBlock:
    text: str
    ordered: bool = False
    level: int = 0


@dataclass
class ImageBlock:
    image_path: str
    alt_text: str = ""


@dataclass
class TableBlock:
    rows: List[List[str]]
    html: str = ""


@dataclass
class UnknownBlock:
    kind: str
    raw: str = ""


@dataclass
class HWPXDocument:
    blocks: list["Block"]
    extracted_images: list[str]
    footnotes: list[str] = field(default_factory=list)
    endnotes: list[str] = field(default_factory=list)


Block = ParagraphBlock | HeadingBlock | ListItemBlock | ImageBlock | TableBlock | UnknownBlock


def hwpx_to_markdown(hwpx_path: str, assets_dir: str | None = None) -> str:
    """Convert HWPX file to Markdown.

    Args:
        hwpx_path: Path to .hwpx file.
        assets_dir: Optional output directory for extracted assets.

    Returns:
        Markdown text. Returns empty string on complete failure.
    """
    zf = _open_hwpx_zip(hwpx_path)
    if zf is None:
        return ""

    try:
        hwpx_file = Path(hwpx_path)
        base_dir = hwpx_file.parent.resolve()
        target_assets_dir = _resolve_assets_dir(hwpx_file, assets_dir)
        image_map, extracted_images = _extract_images_from_zip(zf, target_assets_dir, base_dir)
        _enrich_image_map_with_manifest(zf, image_map)

        _detect_header_footer(zf)

        document = _parse_hwpx_document(zf, hwpx_path, image_map, extracted_images)
        return _render_document_to_markdown(document)
    except Exception:
        logger.exception("Unexpected failure while parsing HWPX: %s", hwpx_path)
        return ""
    finally:
        try:
            zf.close()
        except Exception:
            logger.debug("Failed to close HWPX zip: %s", hwpx_path, exc_info=True)


def parse_hwpx_document(hwpx_path: str, assets_dir: str | None = None) -> HWPXDocument:
    """Parse HWPX file and return structured document blocks.

    Args:
        hwpx_path: Path to .hwpx file.
        assets_dir: Optional output directory for extracted assets.

    Returns:
        HWPXDocument with parsed blocks and extracted assets.
    """
    zf = _open_hwpx_zip(hwpx_path)
    if zf is None:
        return HWPXDocument(blocks=[], extracted_images=[])

    try:
        hwpx_file = Path(hwpx_path)
        base_dir = hwpx_file.parent.resolve()
        target_assets_dir = _resolve_assets_dir(hwpx_file, assets_dir)
        image_map, extracted_images = _extract_images_from_zip(zf, target_assets_dir, base_dir)
        _enrich_image_map_with_manifest(zf, image_map)

        _detect_header_footer(zf)

        return _parse_hwpx_document(zf, hwpx_path, image_map, extracted_images)
    except Exception:
        logger.exception("Unexpected failure while parsing HWPX: %s", hwpx_path)
        return HWPXDocument(blocks=[], extracted_images=[])
    finally:
        try:
            zf.close()
        except Exception:
            logger.debug("Failed to close HWPX zip: %s", hwpx_path, exc_info=True)


def _parse_hwpx_document(
    zf: zipfile.ZipFile,
    hwpx_path: str,
    image_map: dict[str, str],
    extracted_images: list[str],
) -> HWPXDocument:
    section_files = _find_section_files(zf)
    if not section_files:
        logger.warning("No section XML files found in HWPX: %s", hwpx_path)
        return HWPXDocument(blocks=[], extracted_images=extracted_images)

    blocks: list[Block] = []
    for section_path in section_files:
        xml_text = _read_xml(zf, section_path)
        if not xml_text:
            continue
        blocks.extend(_parse_section_xml(xml_text, image_map))

    footnotes, endnotes = _extract_notes_from_zip(zf)

    return HWPXDocument(
        blocks=blocks,
        extracted_images=extracted_images,
        footnotes=footnotes,
        endnotes=endnotes,
    )


def _render_document_to_markdown(document: HWPXDocument) -> str:
    body = _render_blocks_to_markdown(document.blocks, document.extracted_images)

    out_lines = [body] if body else []

    if document.footnotes:
        out_lines.append("## 각주")
        for i, footnote in enumerate(document.footnotes, 1):
            if footnote.strip():
                out_lines.append(f"{i}. {footnote}")

    if document.endnotes:
        out_lines.append("## 미주")
        for i, endnote in enumerate(document.endnotes, 1):
            if endnote.strip():
                out_lines.append(f"{i}. {endnote}")

    return "\n\n".join(out_lines).strip()


def _open_hwpx_zip(hwpx_path: str) -> zipfile.ZipFile | None:
    try:
        zf = zipfile.ZipFile(hwpx_path, "r")
        return zf
    except FileNotFoundError:
        logger.warning("HWPX file not found: %s", hwpx_path)
        return None
    except zipfile.BadZipFile:
        logger.warning("Invalid HWPX ZIP format: %s", hwpx_path)
        return None
    except Exception:
        logger.exception("Failed to open HWPX zip: %s", hwpx_path)
        return None


def _find_section_files(zf: zipfile.ZipFile) -> list[str]:
    names = zf.namelist()

    # Common HWPX section path pattern
    section_files = [
        name for name in names
        if name.startswith("Contents/")
        and name.lower().endswith(".xml")
        and "section" in name.lower()
    ]

    # Fallback: include content XML if section naming is different
    if not section_files:
        section_files = [
            name for name in names
            if name.startswith("Contents/") and name.lower().endswith(".xml")
        ]

    section_files.sort()
    return section_files


def _extract_notes_from_zip(zf: zipfile.ZipFile) -> tuple[list[str], list[str]]:
    footnotes: list[str] = []
    endnotes: list[str] = []

    footnote_tags = {"footnote", "footNote", "fn", "각주"}
    endnote_tags = {"endnote", "endNote", "en", "미주"}

    try:
        for name in zf.namelist():
            if not name.lower().endswith(".xml"):
                continue
            if "footnote" in name.lower() or "endnote" in name.lower():
                try:
                    xml_text = zf.read(name).decode("utf-8")
                    root = ET.fromstring(xml_text)
                    for elem in root.iter():
                        local = elem.tag.split("}", 1)[-1].lower() if "}" in elem.tag else elem.tag.lower()
                        if local in footnote_tags:
                            text = _extract_text_from_paragraph(elem)
                            if text:
                                footnotes.append(_clean_text(text))
                        elif local in endnote_tags:
                            text = _extract_text_from_paragraph(elem)
                            if text:
                                endnotes.append(_clean_text(text))
                except Exception:
                    logger.debug("Failed to parse note file: %s", name)
    except Exception:
        logger.exception("Failed to extract notes from HWPX")

    return footnotes, endnotes


def _detect_header_footer(zf: zipfile.ZipFile) -> bool:
    """Detect if HWPX contains header/footer content.

    Returns True if header/footer files or tags are detected.
    Does not convert them to markdown, only logs a warning.
    """
    header_footer_patterns = {"header", "footer", "head", "ftr", "hdr", "머리말", "꼬리말"}

    try:
        for name in zf.namelist():
            name_lower = name.lower()
            if any(pattern in name_lower for pattern in header_footer_patterns):
                if name_lower.endswith(".xml"):
                    logger.warning("HEADER_FOOTER_IGNORED: Header/footer content detected but not imported: %s", name)
                    return True
    except Exception:
        logger.debug("Failed to detect header/footer in HWPX")

    return False


def _enrich_image_map_with_manifest(zf: zipfile.ZipFile, image_map: dict[str, str]) -> None:
    """Parse HWPX manifest (content.hpf) to map itemIDs to image paths.

    HWPX section XML references images by numeric itemID (e.g. '1312416266').
    The manifest file maps these IDs to bindata file paths (e.g. 'bindata/image1.jpg').
    This function enriches image_map with those ID-to-path mappings.
    """
    manifest_candidates = [
        name for name in zf.namelist()
        if name.lower().endswith(".hpf")
        or "manifest" in name.lower() and name.lower().endswith(".xml")
    ]
    if not manifest_candidates:
        logger.debug("No HWPX manifest file found for image ID mapping")
        return

    logger.debug("HWPX manifest candidates: %s", manifest_candidates)

    for manifest_path in manifest_candidates:
        try:
            xml_text = _read_xml(zf, manifest_path)
            if not xml_text.strip():
                continue
            root = ET.fromstring(xml_text)
            for elem in root.iter():
                tag = elem.tag
                if not isinstance(tag, str):
                    continue
                local = tag.split("}", 1)[-1].lower() if "}" in tag else tag.lower()
                if local != "item":
                    continue
                item_id = None
                item_href = None
                for raw_key, raw_value in elem.attrib.items():
                    key = raw_key.split("}", 1)[-1].lower() if "}" in raw_key else raw_key.lower()
                    if key == "id":
                        item_id = (raw_value or "").strip()
                    elif key in ("href", "src", "path"):
                        item_href = (raw_value or "").strip()
                if not item_id or not item_href:
                    continue
                # Try to match the href to an existing image_map entry
                href_lower = item_href.replace("\\", "/").strip().lower()
                href_name = Path(href_lower).name.lower()
                href_stem = Path(href_lower).stem.lower()
                for key in (href_lower, href_name, href_stem, item_id.lower()):
                    if key in image_map:
                        image_map[item_id.lower()] = image_map[key]
                        logger.debug("Manifest mapped itemID '%s' -> '%s' via key '%s'", item_id, image_map[key], key)
                        break
        except Exception:
            logger.debug("Failed to parse HWPX manifest: %s", manifest_path)


def _resolve_assets_dir(hwpx_path: Path, assets_dir: str | None) -> Path:
    if assets_dir:
        target = Path(assets_dir)
    else:
        target = hwpx_path.with_name(f"{hwpx_path.stem}_assets")

    try:
        target.mkdir(parents=True, exist_ok=True)
        return target.resolve()
    except Exception:
        logger.exception("Failed to prepare assets dir, using temp dir: %s", target)
        temp_dir = Path(tempfile.mkdtemp(prefix="hwpx_assets_"))
        return temp_dir.resolve()


def _extract_images_from_zip(
    zf: zipfile.ZipFile,
    target_assets_dir: Path,
    base_dir: Path,
) -> tuple[dict[str, str], list[str]]:
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    candidates = []
    for name in zf.namelist():
        lower = name.lower()
        suffix = Path(name).suffix.lower()
        if "bindata/" in lower and suffix in image_exts:
            candidates.append(name)

    candidates.sort()
    image_map: dict[str, str] = {}
    extracted_paths: list[str] = []

    for idx, zip_path in enumerate(candidates, start=1):
        try:
            raw = zf.read(zip_path)
            ext = Path(zip_path).suffix.lower()
            save_name = f"imported_{idx:03d}{ext}"
            save_path = _unique_asset_path(target_assets_dir, save_name)
            save_path.write_bytes(raw)

            md_rel_path = _to_markdown_rel_path(save_path, base_dir)
            extracted_paths.append(md_rel_path)

            original_name = Path(zip_path).name.lower()
            original_stem = Path(zip_path).stem.lower()

            image_map[original_name] = md_rel_path
            image_map[original_stem] = md_rel_path
            image_map[zip_path.lower()] = md_rel_path
        except Exception:
            logger.exception("Failed to extract image from HWPX: %s", zip_path)

    if extracted_paths:
        logger.info("Extracted %d images from HWPX", len(extracted_paths))

    return image_map, extracted_paths


def _unique_asset_path(target_dir: Path, file_name: str) -> Path:
    base = Path(file_name).stem
    ext = Path(file_name).suffix
    candidate = target_dir / file_name
    n = 2
    while candidate.exists():
        candidate = target_dir / f"{base}_{n:03d}{ext}"
        n += 1
    return candidate


def _to_markdown_rel_path(path: Path, base_dir: Path) -> str:
    try:
        rel = path.resolve().relative_to(base_dir.resolve())
        return rel.as_posix()
    except Exception:
        return path.resolve().as_posix()


def _read_xml(zf: zipfile.ZipFile, xml_path: str) -> str:
    try:
        raw = zf.read(xml_path)
    except KeyError:
        logger.warning("XML file not found in HWPX: %s", xml_path)
        return ""
    except Exception:
        logger.exception("Failed to read XML from HWPX: %s", xml_path)
        return ""

    for enc in ("utf-8", "utf-16", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue

    logger.debug("Falling back to utf-8 ignore decode for XML: %s", xml_path)
    return raw.decode("utf-8", errors="ignore")


def _parse_section_xml(xml_text: str, image_map: dict[str, str]) -> list[Block]:
    blocks: list[Block] = []
    if not xml_text.strip():
        return blocks

    try:
        root = ET.fromstring(xml_text)
    except Exception:
        logger.exception("Failed to parse section XML")
        return blocks

    parent_map: dict[ET.Element, ET.Element] = {child: parent for parent in root.iter() for child in parent}

    # Namespace-safe approach: inspect local tag names.
    for elem in root.iter():
        tag = elem.tag
        if not isinstance(tag, str):
            continue
        local = tag.split("}", 1)[-1] if "}" in tag else tag

        if local == "p":
            if _is_under_tag(elem, parent_map, _TABLE_TAGS):
                continue
            heading_level = _detect_heading_level(elem)
            if heading_level is not None:
                text = _extract_text_from_paragraph(elem)
                text = _clean_text(text)
                if text:
                    blocks.append(HeadingBlock(text=text, level=heading_level))
            else:
                list_info = _detect_list_info(elem)
                if list_info is not None:
                    ordered, level = list_info
                    text = _extract_text_from_paragraph(elem)
                    text = _clean_text(text)
                    if text:
                        blocks.append(ListItemBlock(text=text, ordered=ordered, level=level))
                else:
                    blocks.extend(_extract_blocks_from_paragraph(elem, image_map))
        elif local in _TABLE_TAGS:
            blocks.append(_parse_table(elem))

    return blocks


def _is_under_tag(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
    target_locals: set[str],
) -> bool:
    cur = parent_map.get(elem)
    while cur is not None:
        local = _local_name(cur.tag)
        if local in target_locals:
            return True
        cur = parent_map.get(cur)
    return False


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _is_heading_style(value: str) -> bool:
    if not value:
        return False
    value_lower = value.lower()
    heading_keywords = {"heading", "head", "title", "표제", "제목", "소제목", "제1장", "제1편"}
    return any(kw in value_lower for kw in heading_keywords)


def _detect_heading_level(elem: ET.Element) -> int | None:
    style = elem.attrib.get("style") or elem.attrib.get("styleId") or ""
    if _is_heading_style(style):
        style_lower = style.lower()
        if "1" in style_lower and "heading" in style_lower:
            return 1
        if "2" in style_lower and "heading" in style_lower:
            return 2
        if "3" in style_lower and "heading" in style_lower:
            return 3
        if "제1" in style or "제1장" in style or "제1편" in style:
            return 1
        if "제2" in style or "제2장" in style or "제2편" in style:
            return 2
        if "제3" in style or "제3장" in style or "제3편" in style:
            return 3
        if "제4" in style:
            return 4
        if "제5" in style:
            return 5
        if "제6" in style:
            return 6
        if "title" in style_lower or "표제" in style or "제목" in style:
            return 1
        if "소제목" in style:
            return 2
        return 2
    outline_level = elem.attrib.get("outlineLevel") or elem.attrib.get("outline") or ""
    if outline_level:
        try:
            level = int(outline_level)
            if 1 <= level <= 6:
                return level
        except (ValueError, TypeError):
            pass
    return None


def _is_bullet_list_style(value: str) -> bool:
    if not value:
        return False
    value_lower = value.lower()
    bullet_keywords = {"bullet", "list", "ul", "unordered", "불릿", "글머리표", "글머리"}
    return any(kw in value_lower for kw in bullet_keywords)


def _is_ordered_list_style(value: str) -> bool:
    if not value:
        return False
    value_lower = value.lower()
    ordered_keywords = {"number", "numbered", "ordered", "ol", "번호", "번호목록", "순서"}
    return any(kw in value_lower for kw in ordered_keywords)


def _detect_list_info(elem: ET.Element) -> tuple[bool, int] | None:
    style = elem.attrib.get("style") or elem.attrib.get("styleId") or ""
    if _is_bullet_list_style(style):
        level_str = elem.attrib.get("level") or elem.attrib.get("listLevel") or "0"
        try:
            level = int(level_str)
            level = max(0, min(6, level))
        except (ValueError, TypeError):
            level = 0
        return (False, level)
    if _is_ordered_list_style(style):
        level_str = elem.attrib.get("level") or elem.attrib.get("listLevel") or "0"
        try:
            level = int(level_str)
            level = max(0, min(6, level))
        except (ValueError, TypeError):
            level = 0
        return (True, level)
    num_id = elem.attrib.get("numId") or elem.attrib.get("numberingId") or ""
    if num_id and num_id != "0":
        level_str = elem.attrib.get("level") or "0"
        try:
            level = int(level_str)
            level = max(0, min(6, level))
        except (ValueError, TypeError):
            level = 0
        return (True, level)
    return None


def _parse_table(table_elem: ET.Element) -> Block:
    try:
        if not _is_simple_table(table_elem):
            html_table = _render_complex_table_to_html(table_elem)
            if html_table:
                return TableBlock(rows=[], html=html_table)
            return UnknownBlock(kind="table")

        rows: list[list[str]] = []
        row_elems = [
            node for node in table_elem.iter()
            if _local_name(node.tag) in _ROW_TAGS
        ]

        for row in row_elems:
            cells: list[str] = []
            cell_elems = [
                node for node in row.iter()
                if _local_name(node.tag) in _CELL_TAGS
            ]
            for cell in cell_elems:
                cell_text = _extract_text_from_paragraph(cell)
                cell_text = _clean_text(cell_text)
                cell_text = cell_text.replace("\n", " ")
                cells.append(cell_text)

            if cells:
                rows.append(cells)

        if not rows:
            return UnknownBlock(kind="table")

        max_cols = max(len(r) for r in rows)
        normalized_rows = [r + [""] * (max_cols - len(r)) for r in rows]
        return TableBlock(rows=normalized_rows)
    except Exception:
        logger.exception("Failed to parse table")
        return UnknownBlock(kind="table")


def _is_simple_table(table_elem: ET.Element) -> bool:
    complex_tags = {
        *_TABLE_TAGS, *_IMAGE_TAGS, "ole", "object", "chart", "shape", "drawing",
    }

    for node in table_elem.iter():
        local = _local_name(node.tag)

        if local in _CELL_TAGS:
            row_span = (node.attrib.get("rowSpan") or node.attrib.get("rowspan") or "1").strip()
            col_span = (node.attrib.get("colSpan") or node.attrib.get("colspan") or "1").strip()
            if row_span not in {"", "1"}:
                return False
            if col_span not in {"", "1"}:
                return False

        if local in complex_tags and node is not table_elem:
            return False

    return True


def _escape_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _render_simple_table_to_markdown(table: TableBlock) -> str:
    if not table.rows:
        return ""

    rows = table.rows
    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    header = [_escape_table_cell(c) for c in rows[0]]
    body = [[_escape_table_cell(c) for c in r] for r in rows[1:]]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * col_count) + " |",
    ]

    for row in body:
        lines.append("| " + " | ".join(row) + " |")

    table_text = "\n".join(lines)
    return f"\n\n{table_text}\n\n"


def _render_complex_table_to_html(table_elem: ET.Element) -> str:
    try:
        row_elems = [
            node for node in table_elem.iter()
            if _local_name(node.tag) in _ROW_TAGS
        ]
        if not row_elems:
            return ""

        lines: list[str] = ["<table>"]

        for row in row_elems:
            lines.append("  <tr>")
            cell_elems = [
                node for node in row.iter()
                if _local_name(node.tag) in _CELL_TAGS
            ]

            for cell in cell_elems:
                row_span = _safe_span_value(cell.attrib.get("rowSpan") or cell.attrib.get("rowspan"))
                col_span = _safe_span_value(cell.attrib.get("colSpan") or cell.attrib.get("colspan"))

                cell_text = _extract_text_from_paragraph(cell)
                cell_text = _clean_text(cell_text)

                if _contains_unsupported_object(cell):
                    cell_text = (cell_text + "\n[지원되지 않는 객체]").strip()

                safe_text = html_mod.escape(cell_text).replace("\n", "<br>")

                attrs: list[str] = []
                if row_span > 1:
                    attrs.append(f'rowspan="{row_span}"')
                if col_span > 1:
                    attrs.append(f'colspan="{col_span}"')

                attr_part = f" {' '.join(attrs)}" if attrs else ""
                lines.append(f"    <td{attr_part}>{safe_text}</td>")

            lines.append("  </tr>")

        lines.append("</table>")
        return "\n".join(lines)
    except Exception:
        logger.exception("Failed to render complex table as HTML")
        return ""


def _safe_span_value(value: str | None) -> int:
    if not value:
        return 1
    try:
        n = int(str(value).strip())
        return n if n > 1 else 1
    except Exception:
        return 1


def _contains_unsupported_object(cell_elem: ET.Element) -> bool:
    unsupported_tags = {
        "ole", "object", "chart", "shape", "drawing", "equation",
        "video", "audio", *_TABLE_TAGS, *_IMAGE_TAGS,
    }

    for node in cell_elem.iter():
        local = _local_name(node.tag)
        if local in unsupported_tags and node is not cell_elem:
            return True
    return False


def _extract_text_from_paragraph(paragraph_elem: ET.Element) -> str:
    pieces: list[str] = []

    # HWPX usually stores text in <t> nodes within a paragraph.
    # Some documents also use explicit line-break/tab-like elements.
    for node in paragraph_elem.iter():
        tag = node.tag
        if not isinstance(tag, str):
            continue
        local = tag.split("}", 1)[-1] if "}" in tag else tag

        if local == "t":
            if node.text:
                pieces.append(node.text)
            continue

        if local in {"lineBreak", "br", "lb"}:
            pieces.append("\n")
            continue

        if local in {"tab", "tabDef"}:
            pieces.append("\t")
            continue

    return "".join(pieces)


def _extract_blocks_from_paragraph(
    paragraph_elem: ET.Element,
    image_map: dict[str, str],
) -> list[Block]:
    blocks: list[Block] = []
    pieces: list[str] = []

    for node in paragraph_elem.iter():
        tag = node.tag
        if not isinstance(tag, str):
            continue
        local = tag.split("}", 1)[-1] if "}" in tag else tag

        if local == "t":
            if node.text:
                pieces.append(node.text)
            continue

        if local in {"lineBreak", "br", "lb"}:
            pieces.append("\n")
            continue

        if local in {"tab", "tabDef"}:
            pieces.append("\t")
            continue

        if local in _IMAGE_TAGS:
            image_path = _resolve_image_ref(node, image_map)
            current_text = _clean_text("".join(pieces))
            if current_text:
                blocks.append(ParagraphBlock(text=current_text))
            pieces = []

            if image_path:
                blocks.append(ImageBlock(image_path=image_path, alt_text="image"))
            else:
                blocks.append(UnknownBlock(kind="image"))

    tail_text = _clean_text("".join(pieces))
    if tail_text:
        blocks.append(ParagraphBlock(text=tail_text))

    return blocks


def _resolve_image_ref(node: ET.Element, image_map: dict[str, str]) -> str | None:
    candidates: list[str] = []

    # First, look for binaryItemIDRef in child elements (e.g. <hc:img binaryItemIDRef="image1"/>)
    # This is the primary image reference mechanism in HWPX
    for child in node.iter():
        for raw_key, raw_value in child.attrib.items():
            key = raw_key.split("}", 1)[-1].lower() if "}" in raw_key else raw_key.lower()
            if key == "binaryitemidref":
                value = (raw_value or "").strip()
                if value:
                    candidates.append(value)

    # Also check the node's own attributes for other reference types
    for raw_key, raw_value in node.attrib.items():
        key = raw_key.split("}", 1)[-1].lower() if "}" in raw_key else raw_key.lower()
        value = (raw_value or "").strip()
        if not value:
            continue
        # Skip numeric id/instid attributes on the pic element itself
        if key in ("id", "instid") and value.isdigit():
            continue
        if any(token in key for token in ("ref", "href", "bin", "src", "embed", "item")):
            candidates.append(value)

    for candidate in candidates:
        normalized = candidate.replace("#", "").replace("\\", "/").strip().lower()
        name = Path(normalized).name.lower()
        stem = Path(normalized).stem.lower()
        for key in (normalized, name, stem):
            if key in image_map:
                return image_map[key]

    if candidates:
        logger.warning("Unresolved image reference: %s (available: %s)", candidates, list(image_map.keys()))

    return None


def _clean_text(text: str) -> str:
    if not text:
        return ""

    original_len = len(text)

    cleaned = unicodedata.normalize("NFKC", text)
    cleaned = _normalize_special_whitespace(cleaned)
    cleaned = _normalize_line_endings(cleaned)
    cleaned = _remove_unsafe_control_chars(cleaned)
    cleaned = _normalize_markdown_spacing(cleaned)

    if cleaned != text:
        logger.debug(
            "HWPX text cleaned: original_len=%d cleaned_len=%d",
            original_len,
            len(cleaned),
        )

    return cleaned.strip()


def _normalize_special_whitespace(text: str) -> str:
    # Preserve readability while removing problematic invisible chars.
    cleaned = text
    cleaned = cleaned.replace("\ufeff", "")  # BOM
    cleaned = cleaned.replace("\u00a0", " ")  # non-breaking space
    cleaned = cleaned.replace("\u200b", "")  # zero-width space
    cleaned = cleaned.replace("\ufffd", "")  # replacement character
    return cleaned


def _normalize_line_endings(text: str) -> str:
    cleaned = text
    cleaned = cleaned.replace("\r\n", "\n")
    cleaned = cleaned.replace("\r", "\n")
    cleaned = cleaned.replace("\x0b", "\n")  # vertical tab
    cleaned = cleaned.replace("\x0c", "\n")  # form feed
    cleaned = cleaned.replace("\u2028", "\n")  # unicode line separator
    cleaned = cleaned.replace("\u2029", "\n")  # unicode paragraph separator
    return cleaned


def _remove_unsafe_control_chars(text: str) -> str:
    # Keep '\n' and '\t'. Remove remaining control chars.
    return re.sub(r"[\x00-\x08\x0e-\x1f\x7f-\x9f]", "", text)


def _normalize_markdown_spacing(text: str) -> str:
    cleaned = text
    # Tabs can break markdown alignment; convert to 4 spaces.
    cleaned = cleaned.replace("\t", "    ")
    # Collapse only horizontal spaces, keep newlines.
    cleaned = re.sub(r"[ \u3000]{2,}", " ", cleaned)
    # Keep at most one blank line between blocks.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _render_blocks_to_markdown(blocks: list[Block], extracted_images: list[str] | None = None) -> str:
    extracted_images = extracted_images or []
    out: list[str] = []
    used_images: set[str] = set()

    for block in blocks:
        if isinstance(block, HeadingBlock):
            if block.text:
                level = max(1, min(6, block.level))
                out.append(f"{'#' * level} {block.text}")
        elif isinstance(block, ListItemBlock):
            if block.text:
                indent = "  " * max(0, min(6, block.level))
                if block.ordered:
                    out.append(f"{indent}1. {block.text}")
                else:
                    out.append(f"{indent}- {block.text}")
        elif isinstance(block, ParagraphBlock):
            if block.text:
                out.append(block.text)
        elif isinstance(block, TableBlock):
            if block.html:
                out.append(block.html)
            else:
                md_table = _render_simple_table_to_markdown(block)
                if md_table:
                    out.append(md_table)
        elif isinstance(block, ImageBlock):
            if block.image_path:
                used_images.add(block.image_path)
                out.append(f"![{block.alt_text or 'image'}]({block.image_path})")
        else:
            # Unknown blocks are currently ignored to keep output clean.
            continue

    remaining = [p for p in extracted_images if p not in used_images]
    if remaining:
        out.append("## 추출된 이미지")
        for image_path in remaining:
            out.append(f"![image]({image_path})")

    return "\n\n".join(out).strip()
