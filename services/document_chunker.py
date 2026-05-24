import hashlib
import re
from dataclasses import dataclass

from services.document_chunk_model import DocumentChunk, IndexedDocument
from services.markdown_document_model import MarkdownDocument


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_RE = re.compile(r"^\s*([-*+]\s+|\d+[.)]\s+)")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


@dataclass
class _Section:
    heading_path: list[str]
    text: str


def build_indexed_document(
    document: MarkdownDocument,
    document_id: str,
    source_type: str,
    source_path: str | None = None,
    note_id: str | None = None,
) -> IndexedDocument:
    body = document.body_markdown or ""
    metadata = document.metadata
    return IndexedDocument(
        document_id=document_id,
        source_type=source_type,
        source_path=source_path if source_path is not None else document.source_path,
        note_id=note_id,
        title=metadata.title,
        body_checksum=_checksum_text(body),
        tags=list(metadata.tags or []),
        warnings=list(document.warnings or []),
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
    )


def chunk_markdown_document(
    document: MarkdownDocument,
    document_id: str,
    source_type: str,
    source_path: str | None = None,
    note_id: str | None = None,
    target_size: int = 700,
    min_size: int = 200,
    max_size: int = 1400,
) -> list[DocumentChunk]:
    body = (document.body_markdown or "").strip()
    if not body:
        return []

    sections = _split_into_sections(body)
    blocks: list[_Section] = []
    for section in sections:
        if len(section.text) <= max_size:
            blocks.append(section)
            continue
        blocks.extend(_split_large_section(section, max_size=max_size, target_size=target_size))

    blocks = _merge_small_sections(blocks, min_size=min_size, max_size=max_size)

    resolved_source_path = source_path if source_path is not None else document.source_path
    title = document.metadata.title
    doc_warnings = list(document.warnings or [])

    chunks: list[DocumentChunk] = []
    search_cursor = 0

    for order, block in enumerate(blocks):
        chunk_text = block.text.strip()
        if not chunk_text:
            continue

        start_offset, end_offset = _find_offsets(body, chunk_text, search_cursor)
        if end_offset is not None:
            search_cursor = end_offset

        chunks.append(
            DocumentChunk(
                chunk_id=_make_chunk_id(document_id, order, chunk_text),
                document_id=document_id,
                source_type=source_type,
                source_path=resolved_source_path,
                note_id=note_id,
                title=title,
                heading_path=list(block.heading_path),
                chunk_text=chunk_text,
                chunk_order=order,
                start_offset=start_offset,
                end_offset=end_offset,
                warnings=list(doc_warnings),
            )
        )

    return chunks


def _split_into_sections(markdown: str) -> list[_Section]:
    lines = markdown.splitlines()
    stack: list[str] = []
    current_lines: list[str] = []
    current_path: list[str] = []
    sections: list[_Section] = []

    def flush() -> None:
        if not current_lines:
            return
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(_Section(heading_path=list(current_path), text=text))

    for line in lines:
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush()
            current_lines = []

            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            stack[:] = stack[: level - 1]
            stack.append(heading_text)
            current_path = list(stack)

            current_lines.append(line)
        else:
            if not current_lines:
                current_path = list(stack)
            current_lines.append(line)

    flush()
    return sections


def _merge_small_sections(sections: list[_Section], min_size: int, max_size: int) -> list[_Section]:
    if not sections:
        return sections

    merged: list[_Section] = []
    for section in sections:
        if merged and len(section.text) < min_size and merged[-1].heading_path == section.heading_path:
            candidate = f"{merged[-1].text}\n\n{section.text}".strip()
            if len(candidate) <= max_size:
                merged[-1] = _Section(heading_path=merged[-1].heading_path, text=candidate)
                continue
        merged.append(section)

    if len(merged) >= 2 and len(merged[0].text) < min_size and merged[0].heading_path == merged[1].heading_path:
        candidate = f"{merged[0].text}\n\n{merged[1].text}".strip()
        if len(candidate) <= max_size:
            merged[1] = _Section(heading_path=merged[1].heading_path, text=candidate)
            merged = merged[1:]

    return merged


def _split_large_section(section: _Section, max_size: int, target_size: int) -> list[_Section]:
    paragraph_blocks = _split_markdown_blocks(section.text)
    chunks: list[str] = []
    current = ""

    for block in paragraph_blocks:
        block = block.strip()
        if not block:
            continue

        if not current:
            if len(block) <= max_size:
                current = block
            else:
                chunks.extend(_split_hard(block, max_size=max_size, target_size=target_size))
        else:
            candidate = f"{current}\n\n{block}".strip()
            if len(candidate) <= max_size:
                current = candidate
            else:
                chunks.append(current)
                if len(block) <= max_size:
                    current = block
                else:
                    chunks.extend(_split_hard(block, max_size=max_size, target_size=target_size))
                    current = ""

    if current:
        chunks.append(current)

    return [_Section(heading_path=list(section.heading_path), text=text) for text in chunks if text.strip()]


def _split_markdown_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            i += 1
            continue

        if _is_table_start(lines, i):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            table_lines = []
            while i < len(lines) and lines[i].strip() and _looks_like_table_line(lines[i]):
                table_lines.append(lines[i])
                i += 1
            blocks.append("\n".join(table_lines).strip())
            continue

        if _is_list_line(line):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            list_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and _is_list_line(lines[i]):
                list_lines.append(lines[i])
                i += 1
            blocks.append("\n".join(list_lines).strip())
            continue

        current.append(line)
        i += 1

    if current:
        blocks.append("\n".join(current).strip())

    return [b for b in blocks if b.strip()]


def _split_hard(text: str, max_size: int, target_size: int) -> list[str]:
    if len(text) <= max_size:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if not current:
            current = sentence
            continue

        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_size:
            current = candidate
        else:
            parts.append(current)
            current = sentence

    if current:
        parts.append(current)

    final_parts: list[str] = []
    for part in parts:
        if len(part) <= max_size:
            final_parts.append(part)
            continue

        start = 0
        step = max(target_size, 1)
        while start < len(part):
            end = min(start + step, len(part))
            if end < len(part):
                split_at = part.rfind(" ", start, end)
                if split_at > start:
                    end = split_at
            final_parts.append(part[start:end].strip())
            start = end

    return [p for p in final_parts if p]


def _is_list_line(line: str) -> bool:
    return bool(_LIST_RE.match(line))


def _is_table_start(lines: list[str], idx: int) -> bool:
    if idx + 1 >= len(lines):
        return False
    return _looks_like_table_line(lines[idx]) and bool(_TABLE_SEP_RE.match(lines[idx + 1]))


def _looks_like_table_line(line: str) -> bool:
    stripped = line.strip()
    return "|" in stripped and stripped.count("|") >= 2


def _make_chunk_id(document_id: str, order: int, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    return f"{document_id}:{order}:{digest}"


def _checksum_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _find_offsets(body: str, chunk_text: str, cursor: int) -> tuple[int | None, int | None]:
    idx = body.find(chunk_text, cursor)
    if idx >= 0:
        return idx, idx + len(chunk_text)

    idx = body.find(chunk_text)
    if idx >= 0:
        return idx, idx + len(chunk_text)

    return None, None


__all__ = [
    "chunk_markdown_document",
    "build_indexed_document",
]
