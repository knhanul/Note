from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    source_type: str
    source_path: str | None
    note_id: str | None
    title: str | None
    heading_path: list[str] = field(default_factory=list)
    chunk_text: str = ""
    search_text: str = ""
    chunk_order: int = 0
    start_offset: int | None = None
    end_offset: int | None = None
    warnings: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    block_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexedDocument:
    document_id: str
    source_type: str
    source_path: str | None
    note_id: str | None
    title: str | None
    body_checksum: str
    tags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class IndexedDocumentSummary:
    document_id: str
    source_type: str
    source_path: str | None
    note_id: str | None
    title: str | None
    chunk_count: int
    created_at: str | None = None
    updated_at: str | None = None
