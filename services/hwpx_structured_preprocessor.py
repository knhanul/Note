from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from services.hwpx_importer import (
    HWPXDocument,
    HeadingBlock,
    ImageBlock,
    ListItemBlock,
    ParagraphBlock,
    TableBlock,
    UnknownBlock,
    parse_hwpx_document,
)


logger = logging.getLogger(__name__)

PARSER_VERSION = "hwpx_importer_v1"
PREPROCESSING_VERSION = "structured_hwpx_v1"

KEY_VALUE_SEPARATORS = [":", "：", " - ", " – ", " — "]
KEY_VALUE_HEADER_HINTS = {"key", "name", "item", "field", "label", "label"}
VALUE_HEADER_HINTS = {"value", "detail", "content", "desc", "description"}
KEY_VALUE_HEADER_HINTS_KO = {"항목", "구분", "이름", "표시", "조건", "분류"}
VALUE_HEADER_HINTS_KO = {"내용", "값", "설명", "기준", "결과"}


@dataclass
class StructuredTableRow:
    row_index: int
    cells: list[str]
    normalized_cells: list[str]
    markdown: str
    search_text: str
    row_json: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_index": self.row_index,
            "cells": self.cells,
            "normalized_cells": self.normalized_cells,
            "markdown": self.markdown,
            "search_text": self.search_text,
            "row_json": self.row_json,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredTableRow":
        return cls(
            row_index=int(data.get("row_index", 0)),
            cells=list(data.get("cells", [])),
            normalized_cells=list(data.get("normalized_cells", [])),
            markdown=str(data.get("markdown", "")),
            search_text=str(data.get("search_text", "")),
            row_json=dict(data.get("row_json", {}) or {}),
        )


@dataclass
class StructuredTable:
    table_id: str
    headers: list[str]
    rows: list[StructuredTableRow]
    markdown: str
    search_text: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "headers": self.headers,
            "rows": [row.to_dict() for row in self.rows],
            "markdown": self.markdown,
            "search_text": self.search_text,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredTable":
        return cls(
            table_id=str(data.get("table_id", "")),
            headers=list(data.get("headers", [])),
            rows=[StructuredTableRow.from_dict(row) for row in data.get("rows", [])],
            markdown=str(data.get("markdown", "")),
            search_text=str(data.get("search_text", "")),
            warnings=list(data.get("warnings", [])),
        )


@dataclass
class StructuredBlock:
    block_id: str
    block_type: str
    order: int
    raw_text: str
    normalized_text: str
    markdown: str
    search_text: str
    heading_path: list[str] = field(default_factory=list)
    section_path: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "order": self.order,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "markdown": self.markdown,
            "search_text": self.search_text,
            "heading_path": self.heading_path,
            "section_path": self.section_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredBlock":
        return cls(
            block_id=str(data.get("block_id", "")),
            block_type=str(data.get("block_type", "")),
            order=int(data.get("order", 0)),
            raw_text=str(data.get("raw_text", "")),
            normalized_text=str(data.get("normalized_text", "")),
            markdown=str(data.get("markdown", "")),
            search_text=str(data.get("search_text", "")),
            heading_path=list(data.get("heading_path", [])),
            section_path=list(data.get("section_path", [])),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass
class StructuredDocument:
    source_path: str
    source_hash: str
    file_size: int
    modified_time: float
    parser_version: str
    preprocessing_version: str
    blocks: list[StructuredBlock] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "file_size": self.file_size,
            "modified_time": self.modified_time,
            "parser_version": self.parser_version,
            "preprocessing_version": self.preprocessing_version,
            "blocks": [block.to_dict() for block in self.blocks],
            "warnings": self.warnings,
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredDocument":
        return cls(
            source_path=str(data.get("source_path", "")),
            source_hash=str(data.get("source_hash", "")),
            file_size=int(data.get("file_size", 0)),
            modified_time=float(data.get("modified_time", 0.0)),
            parser_version=str(data.get("parser_version", "")),
            preprocessing_version=str(data.get("preprocessing_version", "")),
            blocks=[StructuredBlock.from_dict(block) for block in data.get("blocks", [])],
            warnings=list(data.get("warnings", [])),
            stats=dict(data.get("stats", {}) or {}),
        )


def preprocess_hwpx_file(
    hwpx_path: str | Path,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
) -> StructuredDocument:
    path = Path(hwpx_path).resolve()
    if not path.exists():
        return StructuredDocument(
            source_path=str(path),
            source_hash="",
            file_size=0,
            modified_time=0.0,
            parser_version=PARSER_VERSION,
            preprocessing_version=PREPROCESSING_VERSION,
            blocks=[],
            warnings=["HWPX_FILE_NOT_FOUND"],
            stats={},
        )
    cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / "app_data" / "ai" / "preprocessed_hwpx"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_key = _build_cache_key(path)
    cache_path = cache_dir / f"{cache_key['sha256']}.json"

    if use_cache:
        cached = _load_cached_document(cache_path, cache_key)
        if cached is not None:
            logger.info("[HWPXPreprocessor] Cache hit: %s", path)
            return cached

    logger.info("[HWPXPreprocessor] Preprocessing HWPX: %s", path)
    document = parse_hwpx_document(str(path))
    structured = _build_structured_document(path, document, cache_key)

    _save_cached_document(cache_path, structured)
    return structured


def _build_cache_key(path: Path) -> dict[str, Any]:
    file_bytes = path.read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    stat = path.stat()
    return {
        "file_path": str(path),
        "file_size": stat.st_size,
        "modified_time": stat.st_mtime,
        "sha256": file_hash,
        "parser_version": PARSER_VERSION,
        "preprocessing_version": PREPROCESSING_VERSION,
    }


def _load_cached_document(cache_path: Path, cache_key: dict[str, Any]) -> StructuredDocument | None:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("[HWPXPreprocessor] Failed to read cache: %s", cache_path)
        return None

    stored_key = data.get("cache_key")
    if stored_key != cache_key:
        return None

    doc_data = data.get("document")
    if not isinstance(doc_data, dict):
        return None

    return StructuredDocument.from_dict(doc_data)


def _save_cached_document(cache_path: Path, document: StructuredDocument) -> None:
    payload = {
        "cache_key": {
            "file_path": document.source_path,
            "file_size": document.file_size,
            "modified_time": document.modified_time,
            "sha256": document.source_hash,
            "parser_version": document.parser_version,
            "preprocessing_version": document.preprocessing_version,
        },
        "document": document.to_dict(),
    }
    try:
        cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        logger.warning("[HWPXPreprocessor] Failed to write cache: %s", cache_path)


def _build_structured_document(
    path: Path,
    document: HWPXDocument,
    cache_key: dict[str, Any],
) -> StructuredDocument:
    blocks: list[StructuredBlock] = []
    warnings: list[str] = []
    heading_stack: list[str] = []

    order = 0
    table_counter = 0

    for block in document.blocks:
        if isinstance(block, HeadingBlock):
            heading_text = _normalize_text(block.text)
            heading_stack = _update_heading_stack(heading_stack, block.level, heading_text)
            blocks.append(
                _make_block(
                    block_type="heading",
                    order=order,
                    raw_text=block.text,
                    markdown=f"{'#' * max(block.level, 1)} {heading_text}".strip(),
                    heading_path=list(heading_stack),
                    metadata={"level": block.level},
                )
            )
            order += 1
            continue
        elif isinstance(block, ParagraphBlock):
            order = _append_text_block(
                blocks,
                order,
                block_type="paragraph",
                text=block.text,
                heading_path=heading_stack,
                warnings=warnings,
            )
            continue
        elif isinstance(block, ListItemBlock):
            prefix = f"{'  ' * block.level}{'1.' if block.ordered else '-'} "
            markdown = prefix + _normalize_text(block.text)
            blocks.append(
                _make_block(
                    block_type="list_item",
                    order=order,
                    raw_text=block.text,
                    markdown=markdown,
                    heading_path=list(heading_stack),
                    metadata={"ordered": block.ordered, "level": block.level},
                )
            )
            order += 1
            continue
        elif isinstance(block, TableBlock):
            table_counter += 1
            table_block, row_blocks, key_value_blocks, table_warnings = _build_table_blocks(
                table_id=f"table_{table_counter}",
                table_block=block,
                heading_path=heading_stack,
                order_start=order,
            )
            warnings.extend(table_warnings)
            blocks.extend([table_block, *row_blocks, *key_value_blocks])
            order = order + 1 + len(row_blocks) + len(key_value_blocks)
            continue
        elif isinstance(block, ImageBlock):
            blocks.append(
                _make_block(
                    block_type="image",
                    order=order,
                    raw_text=block.alt_text or "",
                    markdown=f"![{block.alt_text}]({block.image_path})".strip(),
                    heading_path=list(heading_stack),
                    metadata={"image_path": block.image_path},
                )
            )
            order += 1
            continue
        elif isinstance(block, UnknownBlock):
            blocks.append(
                _make_block(
                    block_type="unknown",
                    order=order,
                    raw_text=block.raw,
                    markdown=block.raw,
                    heading_path=list(heading_stack),
                    metadata={"kind": block.kind},
                )
            )
            order += 1
            continue
        else:
            blocks.append(
                _make_block(
                    block_type="unknown",
                    order=order,
                    raw_text="",
                    markdown="",
                    heading_path=list(heading_stack),
                )
            )
            order += 1
            continue

    order = _append_note_blocks(blocks, order, "footnote", document.footnotes, heading_stack)
    order = _append_note_blocks(blocks, order, "endnote", document.endnotes, heading_stack)

    stats = _build_stats(blocks)

    return StructuredDocument(
        source_path=str(path),
        source_hash=cache_key["sha256"],
        file_size=cache_key["file_size"],
        modified_time=cache_key["modified_time"],
        parser_version=PARSER_VERSION,
        preprocessing_version=PREPROCESSING_VERSION,
        blocks=blocks,
        warnings=warnings,
        stats=stats,
    )


def _make_block(
    block_type: str,
    order: int,
    raw_text: str,
    markdown: str,
    heading_path: Iterable[str],
    metadata: dict[str, Any] | None = None,
) -> StructuredBlock:
    cleaned_markdown = _clean_markdown_for_context(markdown)
    normalized = _normalize_text(raw_text)
    return StructuredBlock(
        block_id=f"{block_type}_{order}",
        block_type=block_type,
        order=order,
        raw_text=raw_text,
        normalized_text=normalized,
        markdown=cleaned_markdown.strip(),
        search_text=_build_search_text(cleaned_markdown if cleaned_markdown else normalized),
        heading_path=list(heading_path),
        section_path=list(heading_path),
        metadata=metadata or {},
    )


def _append_text_block(
    blocks: list[StructuredBlock],
    order: int,
    block_type: str,
    text: str,
    heading_path: list[str],
    warnings: list[str],
) -> int:
    if not text or not text.strip():
        return order

    key_value = _detect_key_value(text)
    if key_value is not None:
        key, value = key_value
        markdown = f"- {key}: {value}"
        blocks.append(
            _make_block(
                block_type="key_value",
                order=order,
                raw_text=text,
                markdown=markdown,
                heading_path=list(heading_path),
                metadata={"key": key, "value": value},
            )
        )
        return order + 1

    blocks.append(
        _make_block(
            block_type=block_type,
            order=order,
            raw_text=text,
            markdown=_normalize_text(text),
            heading_path=list(heading_path),
        )
    )
    return order + 1


def _append_note_blocks(
    blocks: list[StructuredBlock],
    order: int,
    block_type: str,
    notes: list[str],
    heading_path: list[str],
) -> int:
    for note in notes:
        if note.strip():
            blocks.append(
                _make_block(
                    block_type=block_type,
                    order=order,
                    raw_text=note,
                    markdown=note,
                    heading_path=list(heading_path),
                )
            )
            order += 1
    return order


def _build_table_blocks(
    table_id: str,
    table_block: TableBlock,
    heading_path: list[str],
    order_start: int,
) -> tuple[StructuredBlock, list[StructuredBlock], list[StructuredBlock], list[str]]:
    warnings: list[str] = []

    if not table_block.rows and table_block.html:
        markdown = table_block.html
        table_struct = StructuredTable(
            table_id=table_id,
            headers=[],
            rows=[],
            markdown=markdown,
            search_text=_build_search_text(_strip_html(markdown)),
            warnings=["TABLE_HTML_ONLY"],
        )
        table_struct_block = _make_block(
            block_type="table",
            order=order_start,
            raw_text=markdown,
            markdown=markdown,
            heading_path=list(heading_path),
            metadata=table_struct.to_dict(),
        )
        return table_struct_block, [], [], table_struct.warnings

    rows = _normalize_table_rows(table_block.rows)
    headers, body_rows = _detect_table_headers(rows)

    if not headers:
        headers = [f"Column {idx + 1}" for idx in range(len(rows[0]) if rows else 0)]
        warnings.append("TABLE_HEADER_ASSUMED")

    table_markdown = _render_markdown_table(headers, body_rows)
    table_search = _build_table_search_text(headers, body_rows)

    row_blocks: list[StructuredBlock] = []
    key_value_blocks: list[StructuredBlock] = []

    table_rows = []
    for row_index, row in enumerate(body_rows):
        row_cells = [cell.strip() for cell in row]
        row_markdown = _render_row_markdown(headers, row_cells)
        row_json = {headers[idx]: row_cells[idx] for idx in range(min(len(headers), len(row_cells)))}
        row_search = _build_row_sentence(headers, row_cells)
        table_rows.append(
            StructuredTableRow(
                row_index=row_index,
                cells=row_cells,
                normalized_cells=[_normalize_text(cell) for cell in row_cells],
                markdown=row_markdown,
                search_text=row_search,
                row_json=row_json,
            )
        )

    table_struct = StructuredTable(
        table_id=table_id,
        headers=headers,
        rows=table_rows,
        markdown=table_markdown,
        search_text=table_search,
        warnings=warnings,
    )

    table_block_struct = _make_block(
        block_type="table",
        order=order_start,
        raw_text=table_markdown,
        markdown=table_markdown,
        heading_path=list(heading_path),
        metadata=table_struct.to_dict(),
    )

    for row in table_rows:
        row_blocks.append(
            _make_block(
                block_type="table_row",
                order=order_start + 1 + len(row_blocks),
                raw_text=" ".join(row.cells),
                markdown=row.markdown,
                heading_path=list(heading_path),
                metadata={
                    "table_id": table_id,
                    "row_index": row.row_index,
                    "row_json": row.row_json,
                    "headers": headers,
                    "search_text": row.search_text,
                },
            )
        )

    key_value_blocks.extend(
        _build_key_value_blocks_from_table(
            headers,
            table_rows,
            table_id=table_id,
            heading_path=heading_path,
            order_start=order_start + 1 + len(row_blocks),
        )
    )

    return table_block_struct, row_blocks, key_value_blocks, warnings


def _build_key_value_blocks_from_table(
    headers: list[str],
    rows: list[StructuredTableRow],
    table_id: str,
    heading_path: list[str],
    order_start: int,
) -> list[StructuredBlock]:
    blocks: list[StructuredBlock] = []
    if len(headers) != 2:
        return blocks

    header_join = " ".join(headers).lower()
    header_score = sum(
        1
        for token in (KEY_VALUE_HEADER_HINTS | KEY_VALUE_HEADER_HINTS_KO)
        if token.lower() in header_join
    )
    header_score += sum(
        1
        for token in (VALUE_HEADER_HINTS | VALUE_HEADER_HINTS_KO)
        if token.lower() in header_join
    )

    if header_score < 1:
        return blocks

    for row in rows:
        if len(row.cells) < 2:
            continue
        key = row.cells[0].strip()
        value = row.cells[1].strip()
        if not key or not value:
            continue
        blocks.append(
            _make_block(
                block_type="key_value",
                order=order_start + len(blocks),
                raw_text=f"{key}: {value}",
                markdown=f"- {key}: {value}",
                heading_path=list(heading_path),
                metadata={"key": key, "value": value, "table_id": table_id},
            )
        )

    return blocks


def _normalize_table_rows(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return []
    max_cols = max(len(row) for row in rows)
    normalized = []
    for row in rows:
        normalized_row = [cell.strip() if cell else "" for cell in row]
        if len(normalized_row) < max_cols:
            normalized_row.extend([""] * (max_cols - len(normalized_row)))
        normalized.append(normalized_row)
    return normalized


def _detect_table_headers(rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    if not rows:
        return [], []

    header_candidates = rows[:2]
    header_rows = []
    for candidate in header_candidates:
        if _is_header_row(candidate):
            header_rows.append(candidate)
        else:
            break

    if not header_rows:
        return [], rows

    data_rows = rows[len(header_rows) :]
    headers = _merge_header_rows(header_rows)
    return headers, data_rows


def _is_header_row(row: list[str]) -> bool:
    if not row:
        return False
    non_empty = [cell for cell in row if cell.strip()]
    if not non_empty:
        return False
    numeric_cells = sum(1 for cell in non_empty if _looks_numeric(cell))
    numeric_ratio = numeric_cells / max(len(non_empty), 1)
    if numeric_ratio > 0.5:
        return False
    short_cells = sum(1 for cell in non_empty if len(cell) <= 15)
    return short_cells >= max(1, len(non_empty) // 2)


def _merge_header_rows(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    max_cols = max(len(row) for row in rows)
    merged: list[str] = []

    for col in range(max_cols):
        parts = []
        for row in rows:
            if col < len(row) and row[col].strip():
                parts.append(row[col].strip())
        merged.append(" / ".join(parts))
    return merged


def _render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""
    header_line = "| " + " | ".join(_escape_table_cell(h) for h in headers) + " |"
    divider = "|" + "|".join(["---"] * len(headers)) + "|"
    lines = [header_line, divider]
    for row in rows:
        padded = row + [""] * (len(headers) - len(row))
        line = "| " + " | ".join(_escape_table_cell(cell) for cell in padded) + " |"
        lines.append(line)
    return "\n".join(lines)


def _render_row_markdown(headers: list[str], row: list[str]) -> str:
    if not headers:
        return ""
    header_line = "| " + " | ".join(_escape_table_cell(h) for h in headers) + " |"
    divider = "|" + "|".join(["---"] * len(headers)) + "|"
    padded = row + [""] * (len(headers) - len(row))
    row_line = "| " + " | ".join(_escape_table_cell(cell) for cell in padded) + " |"
    return "\n".join([header_line, divider, row_line])


def _escape_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _build_table_search_text(headers: list[str], rows: list[list[str]]) -> str:
    parts = [" ".join(headers)] if headers else []
    for row in rows:
        parts.append(" ".join(cell for cell in row if cell.strip()))
    return _build_search_text(" ".join(parts))


def _build_row_sentence(headers: list[str], row: list[str]) -> str:
    items = []
    for idx, cell in enumerate(row):
        label = headers[idx] if idx < len(headers) and headers[idx] else f"Column {idx + 1}"
        if cell.strip():
            items.append(f"{label}: {cell.strip()}")
    return "; ".join(items)


def _build_stats(blocks: list[StructuredBlock]) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "block_count": len(blocks),
        "paragraphs": 0,
        "tables": 0,
        "table_rows": 0,
        "key_values": 0,
    }
    for block in blocks:
        if block.block_type == "paragraph":
            stats["paragraphs"] += 1
        elif block.block_type == "table":
            stats["tables"] += 1
        elif block.block_type == "table_row":
            stats["table_rows"] += 1
        elif block.block_type == "key_value":
            stats["key_values"] += 1
    return stats


def _build_search_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"[\|#*`>-]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    value = text.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[\t\f\v]+", " ", value)
    value = re.sub(r"[ ]{2,}", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _clean_markdown_for_context(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        if _is_markdown_table_divider(stripped):
            prev_stripped = cleaned_lines[-1].strip() if cleaned_lines else ""
            if prev_stripped.startswith("|"):
                cleaned_lines.append(line)
                continue
            continue

        if _is_meaningless_table_row(stripped):
            continue

        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _is_markdown_table_divider(line: str) -> bool:
    return bool(re.match(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$", line))


def _is_meaningless_table_row(line: str) -> bool:
    if not line.startswith("|"):
        return False

    cells = [cell.strip() for cell in line.strip("|").split("|")]
    if len(cells) < 2:
        return False

    non_empty = [cell for cell in cells if cell]
    if not non_empty:
        return True

    if all(re.fullmatch(r"[A-Za-z]", cell) for cell in non_empty):
        return True

    if all(not re.search(r"[0-9A-Za-z가-힣]", cell) for cell in non_empty):
        return True

    return False


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _looks_numeric(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"\d", text))


def _detect_key_value(text: str) -> tuple[str, str] | None:
    candidate = text.strip()
    if not candidate:
        return None

    for sep in KEY_VALUE_SEPARATORS:
        if sep in candidate:
            parts = candidate.split(sep, 1)
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value and len(key) <= 40:
                return key, value

    match = re.match(r"^([^()]{1,40})\(([^()]{1,200})\)$", candidate)
    if match:
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key and value:
            return key, value

    return None


def _update_heading_stack(stack: list[str], level: int, text: str) -> list[str]:
    if level <= 0:
        return stack
    level = min(level, 6)
    new_stack = list(stack[: level - 1])
    new_stack.append(text)
    return new_stack
