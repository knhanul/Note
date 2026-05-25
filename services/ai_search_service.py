import json
from dataclasses import dataclass, field
from typing import Optional

from services.ai_document_index_repository import AiDocumentIndexRepository


@dataclass
class SearchResultChunk:
    chunk_id: str
    document_id: str
    title: Optional[str]
    source_type: str
    source_path: Optional[str]
    note_id: Optional[str]
    heading_path: list[str] = field(default_factory=list)
    chunk_text: str = ""
    snippet: Optional[str] = None
    score: float = 0.0
    chunk_order: int = 0


class AiSearchService:
    MAX_LIMIT = 100
    DEFAULT_LIMIT = 20
    SNIPPET_LENGTH = 150

    def __init__(self, repository: AiDocumentIndexRepository):
        self._repo = repository

    def search_keyword(
        self, query: str, limit: int = 20, offset: int = 0, fallback: bool = False
    ) -> list[SearchResultChunk]:
        import logging
        logger = logging.getLogger(__name__)
        
        if not query or not query.strip():
            return []

        limit = self._normalize_limit(limit)
        offset = self._normalize_offset(offset)
        query = query.strip()
        query_lower = query.lower()
        escaped_query = self._escape_like_wildcards(query)

        conn = self._repo._db.get_connection()
        cursor = conn.cursor()

        like_pattern = f"%{escaped_query}%"
        cursor.execute("""
            SELECT
                c.chunk_id,
                c.document_id,
                d.title,
                d.source_type,
                d.source_path,
                d.note_id,
                c.heading_path_json,
                c.chunk_text,
                c.chunk_order
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE d.title LIKE ?
               OR c.heading_path_json LIKE ?
               OR c.chunk_text LIKE ?
            ORDER BY c.chunk_order
        """, (like_pattern, like_pattern, like_pattern))
        rows = cursor.fetchall()

        logger.info(f"[AiSearchService] Keyword search: query='{query}', found {len(rows)} raw rows")

        results: list[SearchResultChunk] = []
        for row in rows:
            score = self._calculate_score(
                row["title"],
                row["heading_path_json"],
                row["chunk_text"],
                query,
                query_lower,
            )
            if score > 0:
                snippet = self._create_snippet(row["chunk_text"], query_lower)
                results.append(self._row_to_search_result(row, score, snippet))

        results.sort(key=lambda r: (-r.score, r.title or "", r.document_id, r.chunk_order))
        
        # Fallback: if no results and fallback enabled, return recent indexed documents
        if not results and fallback:
            logger.info(f"[AiSearchService] No keyword match for '{query}', returning recent documents as fallback")
            return self._get_recent_documents(limit, offset)
        
        return results[offset : offset + limit]
    
    def _get_recent_documents(self, limit: int, offset: int) -> list[SearchResultChunk]:
        """Get recent indexed documents as fallback when no search results."""
        import logging
        logger = logging.getLogger(__name__)
        
        conn = self._repo._db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                c.chunk_id,
                c.document_id,
                d.title,
                d.source_type,
                d.source_path,
                d.note_id,
                c.heading_path_json,
                c.chunk_text,
                c.chunk_order
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            ORDER BY d.created_at DESC, c.chunk_order
            LIMIT ?
        """, (limit * 2,))  # Get more chunks to ensure we have enough
        rows = cursor.fetchall()
        
        logger.info(f"[AiSearchService] Fallback: found {len(rows)} recent documents")
        
        results: list[SearchResultChunk] = []
        for row in rows:
            snippet = self._create_snippet(row["chunk_text"], "")
            results.append(self._row_to_search_result(row, 0.1, snippet))
        
        return results[offset : offset + limit]

    def search_by_document(
        self,
        document_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SearchResultChunk]:
        if not query or not query.strip():
            return []

        limit = self._normalize_limit(limit)
        offset = self._normalize_offset(offset)
        query = query.strip()
        query_lower = query.lower()
        escaped_query = self._escape_like_wildcards(query)

        conn = self._repo._db.get_connection()
        cursor = conn.cursor()

        like_pattern = f"%{escaped_query}%"
        cursor.execute("""
            SELECT
                c.chunk_id,
                c.document_id,
                d.title,
                d.source_type,
                d.source_path,
                d.note_id,
                c.heading_path_json,
                c.chunk_text,
                c.chunk_order
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE c.document_id = ?
              AND (d.title LIKE ? OR c.heading_path_json LIKE ? OR c.chunk_text LIKE ?)
            ORDER BY c.chunk_order
        """, (document_id, like_pattern, like_pattern, like_pattern))
        rows = cursor.fetchall()

        results: list[SearchResultChunk] = []
        for row in rows:
            score = self._calculate_score(
                row["title"],
                row["heading_path_json"],
                row["chunk_text"],
                query,
                query_lower,
            )
            if score > 0:
                snippet = self._create_snippet(row["chunk_text"], query_lower)
                results.append(self._row_to_search_result(row, score, snippet))

        results.sort(key=lambda r: (-r.score, r.chunk_order))
        return results[offset : offset + limit]

    def search_title_or_chunk(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> list[SearchResultChunk]:
        return self.search_keyword(query, limit, offset)

    def count_keyword(self, query: str) -> int:
        if not query or not query.strip():
            return 0

        query = query.strip()
        escaped_query = self._escape_like_wildcards(query)
        like_pattern = f"%{escaped_query}%"

        conn = self._repo._db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(DISTINCT c.chunk_id) as cnt
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE d.title LIKE ?
               OR c.heading_path_json LIKE ?
               OR c.chunk_text LIKE ?
        """, (like_pattern, like_pattern, like_pattern))
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def count_by_document(self, document_id: str, query: str) -> int:
        if not query or not query.strip():
            return 0

        query = query.strip()
        escaped_query = self._escape_like_wildcards(query)
        like_pattern = f"%{escaped_query}%"

        conn = self._repo._db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(DISTINCT c.chunk_id) as cnt
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE c.document_id = ?
              AND (d.title LIKE ? OR c.heading_path_json LIKE ? OR c.chunk_text LIKE ?)
        """, (document_id, like_pattern, like_pattern, like_pattern))
        row = cursor.fetchone()
        return row["cnt"] if row else 0

    def _normalize_limit(self, limit: int) -> int:
        if limit < 1:
            return self.DEFAULT_LIMIT
        if limit > self.MAX_LIMIT:
            return self.MAX_LIMIT
        return limit

    def _normalize_offset(self, offset: int) -> int:
        return max(0, offset)

    def _escape_like_wildcards(self, query: str) -> str:
        return query.replace("%", r"\%").replace("_", r"\_")

    def _create_snippet(self, chunk_text: str, query_lower: str) -> Optional[str]:
        if not chunk_text:
            return None

        text_lower = chunk_text.lower()
        query_words = [w for w in query_lower.split() if w]

        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1:
                start = max(0, pos - 50)
                end = min(len(chunk_text), pos + self.SNIPPET_LENGTH - 50)
                snippet = chunk_text[start:end]
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(chunk_text) else ""
                return prefix + snippet + suffix

        if len(chunk_text) > self.SNIPPET_LENGTH:
            return chunk_text[: self.SNIPPET_LENGTH] + "..."
        return chunk_text

    def _calculate_score(
        self,
        title: Optional[str],
        heading_path_json: Optional[str],
        chunk_text: str,
        query: str,
        query_lower: str,
    ) -> float:
        score = 0.0

        if title:
            title_lower = title.lower()
            if query_lower in title_lower:
                score += 3.0
            else:
                for word in query_lower.split():
                    if word in title_lower:
                        score += 3.0

        if heading_path_json:
            try:
                heading_path = json.loads(heading_path_json)
                if isinstance(heading_path, list):
                    heading_text = " ".join(heading_path).lower()
                    if query_lower in heading_text:
                        score += 2.0
                    else:
                        for word in query_lower.split():
                            if word in heading_text:
                                score += 2.0
            except (json.JSONDecodeError, TypeError):
                pass

        if chunk_text:
            chunk_lower = chunk_text.lower()
            if query_lower in chunk_lower:
                score += 1.0
            else:
                for word in query_lower.split():
                    if word in chunk_lower:
                        score += 1.0

        return score

    def _row_to_search_result(
        self, row: dict, score: float, snippet: Optional[str] = None
    ) -> SearchResultChunk:
        heading_path: list[str] = []
        if row["heading_path_json"]:
            try:
                parsed = json.loads(row["heading_path_json"])
                if isinstance(parsed, list):
                    heading_path = parsed
            except (json.JSONDecodeError, TypeError):
                heading_path = []

        return SearchResultChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            title=row["title"],
            source_type=row["source_type"],
            source_path=row["source_path"],
            note_id=row["note_id"],
            heading_path=heading_path,
            chunk_text=row["chunk_text"],
            snippet=snippet,
            score=score,
            chunk_order=row["chunk_order"],
        )
