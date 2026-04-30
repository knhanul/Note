"""HWPX XML parser for structured document import.

Parses HWPX (Hancom Word XML) files to extract structured content
including paragraphs, tables, and images, converting them to Markdown.
"""
from __future__ import annotations

import base64
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import xml.etree.ElementTree as ET


@dataclass
class ImageInfo:
    """Information about an image in HWPX."""
    id: str
    path: str
    base64_data: str
    alt_text: str


@dataclass
class TableCell:
    """Table cell data."""
    text: str
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False


@dataclass
class Table:
    """Table structure."""
    rows: List[List[TableCell]]
    caption: str = ""


@dataclass
class Paragraph:
    """Paragraph with style information."""
    text: str
    level: int = 0  # 0=normal, 1-6=heading levels
    is_list: bool = False
    list_type: str = ""  # "bullet" or "number"
    list_number: int = 0


@dataclass
class HWPXDocument:
    """Parsed HWPX document structure."""
    paragraphs: List[Paragraph]
    tables: List[Table]
    images: List[ImageInfo]


class HWPXParser:
    """Parser for HWPX files."""

    # HWPX XML namespace (may vary by version)
    HWPX_NS = {"hwp": "http://schemas.hancom.co.kr/office/2013/hwpml"}

    def __init__(self, hwpx_path: Path):
        self.hwpx_path = hwpx_path
        self._zip_file: Optional[zipfile.ZipFile] = None

    def parse(self) -> HWPXDocument:
        """Parse HWPX file and extract structured content."""
        try:
            with zipfile.ZipFile(self.hwpx_path) as zf:
                self._zip_file = zf
                doc = HWPXDocument(paragraphs=[], tables=[], images=[])

                # Extract images first
                doc.images = self._extract_images(zf)

                # Parse section.xml for document content
                section_xml_path = "Contents/section.xml"
                if section_xml_path in zf.namelist():
                    section_xml = zf.read(section_xml_path)
                    self._parse_section_xml(section_xml, doc)
                else:
                    print(f"[HWPXParser] section.xml not found in {self.hwpx_path}")

                return doc
        except Exception as exc:
            print(f"[HWPXParser] Failed to parse {self.hwpx_path}: {exc}")
            raise
        finally:
            self._zip_file = None

    def _extract_images(self, zf: zipfile.ZipFile) -> List[ImageInfo]:
        """Extract images from HWPX ZIP archive."""
        images: List[ImageInfo] = []

        # HWPX stores images in Files/ or Files/IMAGE/ directory
        image_files = [n for n in zf.namelist() if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))]

        for img_path in image_files:
            try:
                img_data = zf.read(img_path)
                b64_data = base64.b64encode(img_data).decode("ascii")

                # Extract image ID from filename
                img_id = Path(img_path).stem
                images.append(ImageInfo(
                    id=img_id,
                    path=img_path,
                    base64_data=b64_data,
                    alt_text=""
                ))
            except Exception as exc:
                print(f"[HWPXParser] Failed to extract image {img_path}: {exc}")

        return images

    def _parse_section_xml(self, xml_content: bytes, doc: HWPXDocument) -> None:
        """Parse section.xml to extract paragraphs and tables."""
        try:
            root = ET.fromstring(xml_content)
            
            # Try to parse with namespace, fallback to no namespace
            sections = root.findall(".//hwp:sec", self.HWPX_NS)
            if not sections:
                sections = root.findall(".//sec")

            for sec in sections:
                self._parse_section(sec, doc)
        except Exception as exc:
            print(f"[HWPXParser] Failed to parse section XML: {exc}")

    def _parse_section(self, sec: ET.Element, doc: HWPXDocument) -> None:
        """Parse a section element."""
        # Parse paragraphs
        paras = sec.findall(".//hwp:p", self.HWPX_NS)
        if not paras:
            paras = sec.findall(".//p")

        for para in paras:
            paragraph = self._parse_paragraph(para)
            if paragraph and paragraph.text.strip():
                doc.paragraphs.append(paragraph)

        # Parse tables
        tables = sec.findall(".//hwp:tbl", self.HWPX_NS)
        if not tables:
            tables = sec.findall(".//tbl")

        for tbl in tables:
            table = self._parse_table(tbl)
            if table and table.rows:
                doc.tables.append(table)

    def _parse_paragraph(self, para: ET.Element) -> Optional[Paragraph]:
        """Parse a paragraph element."""
        try:
            # Extract text
            text_elems = para.findall(".//hwp:t", self.HWPX_NS)
            if not text_elems:
                text_elems = para.findall(".//t")

            text = "".join(elem.text or "" for elem in text_elems)

            # Detect heading level (HWPX uses different control codes)
            level = 0
            # Check for heading style (implementation depends on actual HWPX structure)
            # This is a placeholder - actual implementation needs real HWPX samples
            ctrl_elems = para.findall(".//hwp:ctrl", self.HWPX_NS)
            if not ctrl_elems:
                ctrl_elems = para.findall(".//ctrl")

            for ctrl in ctrl_elems:
                if ctrl.get("heading"):
                    level = int(ctrl.get("heading", "0"))
                    break

            # Detect list
            is_list = False
            list_type = ""
            list_number = 0

            list_elems = para.findall(".//hwp:list", self.HWPX_NS)
            if not list_elems:
                list_elems = para.findall(".//list")

            if list_elems:
                is_list = True
                list_type = list_elems[0].get("type", "bullet")
                list_number = int(list_elems[0].get("num", "0"))

            return Paragraph(
                text=text,
                level=level,
                is_list=is_list,
                list_type=list_type,
                list_number=list_number
            )
        except Exception as exc:
            print(f"[HWPXParser] Failed to parse paragraph: {exc}")
            return None

    def _parse_table(self, tbl: ET.Element) -> Optional[Table]:
        """Parse a table element."""
        try:
            rows: List[List[TableCell]] = []

            # Parse rows
            tr_elems = tbl.findall(".//hwp:tr", self.HWPX_NS)
            if not tr_elems:
                tr_elems = tbl.findall(".//tr")

            for tr in tr_elems:
                row_cells: List[TableCell] = []

                # Parse cells
                td_elems = tr.findall(".//hwp:td", self.HWPX_NS)
                if not td_elems:
                    td_elems = tr.findall(".//td")

                for td in td_elems:
                    # Extract cell text
                    text_elems = td.findall(".//hwp:t", self.HWPX_NS)
                    if not text_elems:
                        text_elems = td.findall(".//t")

                    text = "".join(elem.text or "" for elem in text_elems)

                    # Get cell span attributes
                    row_span = int(td.get("rowspan", "1"))
                    col_span = int(td.get("colspan", "1"))

                    # Check if header cell
                    is_header = td.get("header") == "true" or td.tag.endswith("th")

                    row_cells.append(TableCell(
                        text=text,
                        row_span=row_span,
                        col_span=col_span,
                        is_header=is_header
                    ))

                if row_cells:
                    rows.append(row_cells)

            if rows:
                return Table(rows=rows)
            return None
        except Exception as exc:
            print(f"[HWPXParser] Failed to parse table: {exc}")
            return None

    def to_markdown(self, doc: HWPXDocument) -> str:
        """Convert parsed HWPX document to Markdown."""
        md_lines: List[str] = []

        # Convert paragraphs
        for para in doc.paragraphs:
            md_lines.append(self._paragraph_to_markdown(para))

        # Convert tables
        for table in doc.tables:
            md_lines.append(self._table_to_markdown(table))

        # Join with proper spacing
        return "\n\n".join(line for line in md_lines if line.strip())

    def _paragraph_to_markdown(self, para: Paragraph) -> str:
        """Convert paragraph to Markdown."""
        text = para.text.strip()

        if not text:
            return ""

        # Handle headings
        if para.level > 0 and para.level <= 6:
            heading_prefix = "#" * para.level
            return f"{heading_prefix} {text}"

        # Handle lists
        if para.is_list:
            if para.list_type == "number":
                return f"{para.list_number}. {text}"
            else:
                return f"- {text}"

        # Normal paragraph
        return text

    def _table_to_markdown(self, table: Table) -> str:
        """Convert table to Markdown."""
        if not table.rows:
            return ""

        md_lines: List[str] = []

        # Determine column count
        max_cols = max(len(row) for row in table.rows)

        for row_idx, row in enumerate(table.rows):
            # Pad row to max columns
            padded_row = row + [TableCell(text="")] * (max_cols - len(row))

            # Convert cells
            cells = [cell.text for cell in padded_row]
            md_line = "| " + " | ".join(cells) + " |"
            md_lines.append(md_line)

            # Add separator after header row
            if row_idx == 0 and any(cell.is_header for cell in padded_row):
                separator = "| " + " | ".join(["---"] * max_cols) + " |"
                md_lines.append(separator)

        return "\n".join(md_lines)


def sanitize_hwp_text(text: str) -> str:
    """Sanitize HWP text by removing control characters."""
    # Remove common HWP control characters
    # HWP uses various control codes in the 0x01-0x1F range
    control_chars = {
        '\x0c': '',  # Form feed
        '\x1e': '',  # Record separator
        '\x1f': '',  # Unit separator
        '\x0b': '\n',  # Vertical tab -> newline
        '\x0a': '\n',  # Line feed
        '\x0d': '',  # Carriage return
    }

    for char, replacement in control_chars.items():
        text = text.replace(char, replacement)

    # Remove other non-printable characters except common whitespace
    text = re.sub(r'[\x00-\x08\x0e-\x1f\x7f-\x9f]', '', text)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
