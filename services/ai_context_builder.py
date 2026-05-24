from dataclasses import dataclass, field
from typing import Optional

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_search_service import SearchResultChunk


@dataclass
class ContextSource:
    chunk_id: str
    document_id: str
    title: Optional[str]
    source_type: str
    source_path: Optional[str]
    note_id: Optional[str]
    heading_path: list[str] = field(default_factory=list)
    chunk_order: int = 0
    score: Optional[float] = None


@dataclass
class ContextItem:
    chunk_id: str
    document_id: str
    heading_path: list[str]
    chunk_text: str
    chunk_order: int
    is_primary: bool
    source: ContextSource


@dataclass
class ContextBundle:
    query: str
    items: list[ContextItem] = field(default_factory=list)
    sources: list[ContextSource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_chars: int = 0


class AiContextBuilder:
    MIN_MAX_CHARS = 1000
    DEFAULT_MAX_CHARS = 6000
    DEFAULT_MAX_CHUNKS = 8

    def __init__(self, repository: AiDocumentIndexRepository):
        self._repo = repository

    def build_context_bundle(
        self,
        query: str,
        search_results: list[SearchResultChunk],
        max_chars: int = 6000,
        neighbor_window: int = 1,
        max_chunks: int = 8,
    ) -> ContextBundle:
        warnings: list[str] = []

        if not search_results:
            warnings.append("CONTEXT_NO_SEARCH_RESULTS")
            return ContextBundle(
                query=query,
                items=[],
                sources=[],
                warnings=warnings,
                total_chars=0,
            )

        max_chars = max(max_chars, self.MIN_MAX_CHARS)
        max_chunks = max(max_chunks, 1)

        primary_chunks: dict[str, tuple[SearchResultChunk, bool]] = {}
        for i, result in enumerate(search_results[:max_chunks]):
            primary_chunks[result.chunk_id] = (result, True)

        neighbor_chunks: dict[str, tuple[SearchResultChunk, bool]] = {}
        if neighbor_window > 0:
            for chunk_id, (primary, _) in primary_chunks.items():
                chunk = self._repo.get_chunk_by_id(chunk_id)
                if chunk:
                    neighbors = self._repo.get_neighbor_chunks(
                        chunk.document_id, chunk.chunk_order, neighbor_window
                    )
                    for n in neighbors:
                        if n.chunk_id not in primary_chunks:
                            search_result = SearchResultChunk(
                                chunk_id=n.chunk_id,
                                document_id=n.document_id,
                                title=n.title,
                                source_type=n.source_type,
                                source_path=n.source_path,
                                note_id=n.note_id,
                                heading_path=n.heading_path,
                                chunk_text=n.chunk_text,
                                score=0.0,
                                chunk_order=n.chunk_order,
                            )
                            neighbor_chunks[n.chunk_id] = (search_result, False)

        all_chunks = {**primary_chunks, **neighbor_chunks}

        items: list[ContextItem] = []
        sources_dict: dict[str, ContextSource] = {}

        for chunk_id, (result, is_primary) in all_chunks.items():
            source = ContextSource(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                title=result.title,
                source_type=result.source_type,
                source_path=result.source_path,
                note_id=result.note_id,
                heading_path=result.heading_path,
                chunk_order=result.chunk_order,
                score=result.score if is_primary else None,
            )
            sources_dict[chunk_id] = source

            item = ContextItem(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                heading_path=result.heading_path,
                chunk_text=result.chunk_text,
                chunk_order=result.chunk_order,
                is_primary=is_primary,
                source=source,
            )
            items.append(item)

        items.sort(key=lambda x: (x.document_id, x.chunk_order))

        total_chars = sum(len(item.chunk_text) for item in items)

        if total_chars > max_chars:
            truncated_items: list[ContextItem] = []
            chars_count = 0
            for item in items:
                if chars_count + len(item.chunk_text) <= max_chars:
                    truncated_items.append(item)
                    chars_count += len(item.chunk_text)
                elif not item.is_primary:
                    continue
                elif chars_count < max_chars:
                    max_len = max_chars - chars_count
                    truncated_item = ContextItem(
                        chunk_id=item.chunk_id,
                        document_id=item.document_id,
                        heading_path=item.heading_path,
                        chunk_text=item.chunk_text[:max_len] + "...",
                        chunk_order=item.chunk_order,
                        is_primary=item.is_primary,
                        source=item.source,
                    )
                    truncated_items.append(truncated_item)
                    chars_count = max_chars
                    warnings.append("CONTEXT_PRIMARY_CHUNK_TRUNCATED")
                    break
                else:
                    break

            if len(truncated_items) < len(items):
                warnings.append("CONTEXT_MAX_CHARS_REACHED")

            items = truncated_items
            total_chars = sum(len(item.chunk_text) for item in items)

        sources = list(sources_dict.values())

        return ContextBundle(
            query=query,
            items=items,
            sources=sources,
            warnings=warnings,
            total_chars=total_chars,
        )
