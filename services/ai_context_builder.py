import logging
from dataclasses import dataclass, field
from typing import Optional

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_search_service import SearchResultChunk


logger = logging.getLogger(__name__)


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
    original_len: int = 0
    used_len: int = 0
    truncated: bool = False
    truncation_reason: str = ""


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
    BROKEN_TABLE_MARKERS = ["column 1", "column 2", "column 3"]
    TABLE_BLOCK_TYPES = {"table_row", "key_value", "table"}
    TABLE_ROW_MIN_BUDGET = 500

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

        filtered_results = []
        excluded_empty_tables = []
        for result in search_results:
            if self._is_broken_table(result.chunk_text or ""):
                excluded_empty_tables.append(result.chunk_id)
                continue
            if self._is_empty_table(result.chunk_text or ""):
                excluded_empty_tables.append(result.chunk_id)
                continue
            filtered_results.append(result)

        if excluded_empty_tables:
            logger.info(
                "[AiContextBuilder] excluded_empty_tables=%s",
                excluded_empty_tables,
            )
            warnings.append(f"CONTEXT_EXCLUDED_BROKEN_TABLES:{len(excluded_empty_tables)}")

        table_results = [r for r in filtered_results if self._is_table_chunk(r)]
        non_table_results = [r for r in filtered_results if not self._is_table_chunk(r)]
        prioritized_results = table_results + non_table_results

        primary_chunks: dict[str, tuple[SearchResultChunk, bool]] = {}
        for i, result in enumerate(prioritized_results[:max_chunks]):
            primary_chunks[result.chunk_id] = (result, True)

        preserved_table_rows = sum(1 for r in primary_chunks.values() if self._is_table_chunk(r[0]))
        if preserved_table_rows > 0:
            logger.info(
                "[AiContextBuilder] preserved_table_rows=%d",
                preserved_table_rows,
            )

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
                original_len=len(result.chunk_text or ""),
                used_len=len(result.chunk_text or ""),
            )
            items.append(item)

        items.sort(key=lambda x: (x.document_id, x.chunk_order))

        total_chars = sum(len(item.chunk_text) for item in items)

        if total_chars > max_chars:
            balanced_items: list[ContextItem] = []
            budget_left = max_chars
            excluded_chunks = 0

            for index, item in enumerate(items):
                remaining_items = len(items) - index
                if budget_left <= 0:
                    excluded_chunks += remaining_items
                    break

                share_budget = budget_left if remaining_items <= 1 else budget_left // remaining_items
                is_table = self._is_table_chunk(item)
                min_budget = self.TABLE_ROW_MIN_BUDGET if is_table else 250
                max_budget = 1200 if is_table else 900
                share_budget = max(min_budget, min(max_budget, share_budget))
                share_budget = min(share_budget, budget_left)

                original_text = item.chunk_text or ""
                original_len = len(original_text)

                if original_len > share_budget:
                    truncated_len = max(0, share_budget - 3)
                    used_text = original_text[:truncated_len] + "..."
                    used_len = len(used_text)
                    truncated = True
                    truncation_reason = "balanced_budget"
                    warnings.append("CONTEXT_PRIMARY_CHUNK_TRUNCATED" if item.is_primary else "CONTEXT_CHUNK_TRUNCATED")
                else:
                    used_text = original_text
                    used_len = original_len
                    truncated = False
                    truncation_reason = ""

                balanced_item = ContextItem(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    heading_path=item.heading_path,
                    chunk_text=used_text,
                    chunk_order=item.chunk_order,
                    is_primary=item.is_primary,
                    source=item.source,
                    original_len=original_len,
                    used_len=used_len,
                    truncated=truncated,
                    truncation_reason=truncation_reason,
                )
                balanced_items.append(balanced_item)
                budget_left -= used_len

                logger.info(
                    "[AiContextBuilder] selected_chunk[%s]: doc='%s', source_type=%s, chunk_order=%s, original_len=%s, used_len=%s, truncated=%s, reason=%s",
                    index,
                    balanced_item.source.title or balanced_item.document_id,
                    balanced_item.source.source_type,
                    balanced_item.chunk_order,
                    original_len,
                    used_len,
                    truncated,
                    truncation_reason or "none",
                )

            if len(balanced_items) < len(items):
                warnings.append("CONTEXT_MAX_CHARS_REACHED")
                excluded_chunks = max(excluded_chunks, len(items) - len(balanced_items))

            items = balanced_items
            total_chars = sum(len(item.chunk_text) for item in items)
            logger.info(
                "[AiContextBuilder] context_budget: max=%s, used=%s, excluded_chunks=%s",
                max_chars,
                total_chars,
                excluded_chunks,
            )
        else:
            for index, item in enumerate(items):
                logger.info(
                    "[AiContextBuilder] selected_chunk[%s]: doc='%s', source_type=%s, chunk_order=%s, original_len=%s, used_len=%s, truncated=%s, reason=%s",
                    index,
                    item.source.title or item.document_id,
                    item.source.source_type,
                    item.chunk_order,
                    item.original_len,
                    item.used_len,
                    item.truncated,
                    item.truncation_reason or "none",
                )

        sources = list(sources_dict.values())

        return ContextBundle(
            query=query,
            items=items,
            sources=sources,
            warnings=warnings,
            total_chars=total_chars,
        )

    def _is_broken_table(self, text: str) -> bool:
        """Check if text contains broken table markers like 'Column 1', 'Column 2'."""
        if not text:
            return False
        text_lower = text.lower()
        marker_count = sum(1 for m in self.BROKEN_TABLE_MARKERS if m in text_lower)
        return marker_count >= 2

    def _is_empty_table(self, text: str) -> bool:
        """Check if text is an empty or near-empty table."""
        if not text:
            return True
        stripped = text.strip()
        if not stripped:
            return True
        if len(stripped) < 10 and all(c in "|- \n" for c in stripped):
            return True
        return False

    def _is_table_chunk(self, result) -> bool:
        """Check if a search result or context item is a table-type chunk."""
        if hasattr(result, "source") and hasattr(result.source, "source_type"):
            pass
        chunk_text = result.chunk_text or ""
        if "| " in chunk_text or "|--" in chunk_text or "---|" in chunk_text:
            return True
        if hasattr(result, "chunk_text") and chunk_text.startswith("|"):
            return True
        return False
