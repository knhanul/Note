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
    STRICT_SCORE_THRESHOLD = 0.5
    RELAXED_SCORE_THRESHOLD = 0.3
    TITLE_SCORE_THRESHOLD = 0.5

    QUERY_EXPRESSION_PATTERNS = [
        "알려줘", "알려주세요", "알겠어요", "알겠습니다",
        "설명해줘", "설명해주세요", "설명해 주세요",
        "정리해줘", "정리해주세요", "정리해 주세요",
        "대해서", "관련해서", "관해",
        "무엇", "어떻게", "어떤", "어디", "언제", "왜", "얼마",
        "있나요", "있을까", "있습니다", "있어",
        "없나요", "없을까", "없습니다", "없어",
        "가능한가", "가능한지", "가능합니다",
        "필요한", "필요해", "필요합니다",
        "원하는", "원해", "원합니다",
        "검색", "찾아", "찾아줘", "찾아주세요",
        "질문", "답변", "정보", "자료",
        "요약", "요약해", "요약해주세요",
        "비교", "비교해", "비교해주세요",
        "작성", "작성해", "작성해주세요",
        "추천", "추천해", "추천해주세요",
        "조언", "조언해", "조언해주세요",
        "도움", "도움말",
    ]

    QUERY_EXPANSION_MAP = {
        "아르바이트": ["알바", "파트타임", "근무자", "직원", "운영 인력", "관리 인력", "보조 인력", "채용", "근무", "급여", "시급"],
        "알바": ["아르바이트", "파트타임", "근무자", "직원", "운영 인력", "관리 인력"],
        "파트타임": ["아르바이트", "알바", "근무자", "직원", "단시간근로"],
        "휘트니스 센터": ["헬스장", "피트니스", "GX", "운동시설", "커뮤니티시설", "헬스", "피트니스센터"],
        "헬스장": ["휘트니스 센터", "피트니스", "GX", "운동시설"],
        "피트니스": ["휘트니스 센터", "헬스장", "GX", "운동"],
        "GX": ["그룹운동", "GX프로그램", "그룹피트니스", "GX강좌"],
        "근무자": ["직원", "근무", "운영", "관리", "인력", "아르바이트"],
        "직원": ["근무자", "근무", "인력", "아르바이트", "파트타임"],
        "운영": ["운영인력", "관리", "근무", "행정"],
        "관리": ["관리인력", "운영", "감독", "행정"],
    }

    def __init__(self, repository: AiDocumentIndexRepository):
        self._repo = repository

    def normalize_query(self, query: str) -> str:
        """Normalize user query by removing query expressions and extracting core keywords."""
        import logging
        logger = logging.getLogger(__name__)
        
        normalized = query.lower().strip()
        
        for pattern in self.QUERY_EXPRESSION_PATTERNS:
            normalized = normalized.replace(pattern, " ")
        
        normalized = " ".join(normalized.split())
        
        logger.info(f"[AiSearchService] Query normalization: original='{query}', normalized='{normalized}'")
        return normalized

    def generate_search_queries(self, normalized_query: str) -> list[str]:
        """Generate search queries from normalized query."""
        import logging
        logger = logging.getLogger(__name__)
        
        queries = [normalized_query]
        
        for key, synonyms in self.QUERY_EXPANSION_MAP.items():
            if key in normalized_query:
                for syn in synonyms:
                    if syn not in queries:
                        queries.append(syn)
                
                for syn in synonyms[:3]:
                    combined = f"{normalized_query.replace(key, '').strip()} {syn}".strip()
                    if combined and combined not in queries:
                        queries.append(combined)
        
        result = queries[:8]
        logger.info(f"[AiSearchService] Generated search queries: {result}")
        return result

    def search_keyword(
        self, query: str, limit: int = 20, offset: int = 0, fallback: bool = False
    ) -> list[SearchResultChunk]:
        import logging
        logger = logging.getLogger(__name__)
        
        if not query or not query.strip():
            return []

        limit = self._normalize_limit(limit)
        offset = self._normalize_offset(offset)
        
        normalized_query = self.normalize_query(query)
        search_queries = self.generate_search_queries(normalized_query)
        
        logger.info(f"[AiSearchService] original_query='{query}', normalized_query='{normalized_query}', generated_search_queries={search_queries}")

        strict_results = self._search_chunks(search_queries, self.STRICT_SCORE_THRESHOLD, "strict")
        logger.info(f"[AiSearchService] strict_result_count={len(strict_results)}")

        if not strict_results:
            relaxed_results = self._search_chunks(search_queries, self.RELAXED_SCORE_THRESHOLD, "relaxed")
            logger.info(f"[AiSearchService] relaxed_result_count={len(relaxed_results)}")
            
            title_results = self._search_by_title(search_queries)
            logger.info(f"[AiSearchService] title_result_count={len(title_results)}")
            
            all_results = {r.chunk_id: r for r in relaxed_results}
            for r in title_results:
                if r.chunk_id not in all_results:
                    all_results[r.chunk_id] = r
            
            results = list(all_results.values())
            results.sort(key=lambda r: (-r.score, r.title or "", r.document_id, r.chunk_order))
            
            direct_evidence = [r for r in results if r.score >= self.RELAXED_SCORE_THRESHOLD]
            possible_related = [r for r in results if r.score < self.RELAXED_SCORE_THRESHOLD and r.score > 0]
            
            logger.info(f"[AiSearchService] selected_direct_count={len(direct_evidence)}, selected_possible_count={len(possible_related)}")
            
            return direct_evidence[offset : offset + limit]
        
        results = strict_results
        results.sort(key=lambda r: (-r.score, r.title or "", r.document_id, r.chunk_order))
        
        logger.info(f"[AiSearchService] selected_direct_count={len(results)}, selected_possible_count=0")
        
        return results[offset : offset + limit]

    def _search_chunks(self, queries: list[str], threshold: float, search_type: str) -> list[SearchResultChunk]:
        """Search chunks with given queries and threshold."""
        import logging
        logger = logging.getLogger(__name__)
        
        all_results: dict[str, SearchResultChunk] = {}

        for sq in queries:
            escaped_query = self._escape_like_wildcards(sq)
            sq_lower = sq.lower()
            
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

            for row in rows:
                score = self._calculate_score(
                    row["title"],
                    row["heading_path_json"],
                    row["chunk_text"],
                    sq,
                    sq_lower,
                )
                if score > 0:
                    chunk_id = row["chunk_id"]
                    if chunk_id in all_results:
                        all_results[chunk_id].score = max(all_results[chunk_id].score, score)
                    else:
                        snippet = self._create_snippet(row["chunk_text"], sq_lower)
                        all_results[chunk_id] = self._row_to_search_result(row, score, snippet)

        results = list(all_results.values())
        filtered = [r for r in results if r.score >= threshold]
        
        logger.info(f"[AiSearchService] {search_type} search: query_count={len(queries)}, raw={len(results)}, filtered={len(filtered)}")
        
        return filtered

    def _search_by_title(self, queries: list[str]) -> list[SearchResultChunk]:
        """Search by document title only (for possible_related)."""
        import logging
        logger = logging.getLogger(__name__)
        
        all_results: dict[str, SearchResultChunk] = {}

        for sq in queries:
            escaped_query = self._escape_like_wildcards(sq)
            
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
                ORDER BY d.created_at DESC, c.chunk_order
            """, (like_pattern,))
            rows = cursor.fetchall()

            for row in rows:
                score = self._calculate_title_score(row["title"], sq.lower()) * 0.5
                if score > 0:
                    chunk_id = row["chunk_id"]
                    if chunk_id not in all_results:
                        snippet = self._create_snippet(row["chunk_text"], "")
                        all_results[chunk_id] = self._row_to_search_result(row, score, snippet)

        results = list(all_results.values())
        logger.info(f"[AiSearchService] title search: results={len(results)}")
        
        return results

    def _calculate_title_score(self, title: Optional[str], query: str) -> float:
        """Calculate score for title-only search."""
        if not title:
            return 0.0
        
        score = 0.0
        title_lower = title.lower()
        
        if query in title_lower:
            score += 3.0
        else:
            for word in query.split():
                if word in title_lower:
                    score += 2.0
        
        return score

    def check_index_terms(self, normalized_query: str) -> dict[str, int]:
        """Debug: Check which terms exist in the index."""
        import logging
        logger = logging.getLogger(__name__)
        
        terms = normalized_query.split()
        term_counts = {}
        
        conn = self._repo._db.get_connection()
        cursor = conn.cursor()
        
        for term in terms:
            escaped_term = self._escape_like_wildcards(term)
            like_pattern = f"%{escaped_term}%"
            
            cursor.execute("""
                SELECT COUNT(DISTINCT c.chunk_id) as cnt
                FROM ai_document_chunks c
                JOIN ai_documents d ON c.document_id = d.document_id
                WHERE d.title LIKE ?
                   OR c.heading_path_json LIKE ?
                   OR c.chunk_text LIKE ?
            """, (like_pattern, like_pattern, like_pattern))
            
            row = cursor.fetchone()
            count = row["cnt"] if row else 0
            term_counts[term] = count
            logger.info(f"[IndexDebug] term='{term}', count={count}")
        
        return term_counts

    def _expand_query(self, query: str) -> list[str]:
        """Expand query with synonyms and related terms."""
        expanded = [query]
        query_lower = query.lower()
        
        for key, synonyms in self.QUERY_EXPANSION_MAP.items():
            if key in query_lower:
                for syn in synonyms:
                    expanded_query = query_lower.replace(key, syn)
                    if expanded_query not in expanded:
                        expanded.append(expanded_query)
                
                for syn in synonyms[:3]:
                    combined = f"{query_lower.replace(key, '').strip()} {syn}".strip()
                    if combined and combined not in expanded:
                        expanded.append(combined)
        
        return expanded[:10]
    
    def _get_recent_documents(self, limit: int, offset: int, query: str = "") -> list[SearchResultChunk]:
        """Get recent indexed documents as fallback when no search results. DEPRECATED - use only when explicitly needed."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.warning(f"[AiSearchService] DEPRECATED: Using recent documents fallback for query '{query}'. This should be disabled.")
        
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
        """, (limit * 2,))
        rows = cursor.fetchall()
        
        logger.info(f"[AiSearchService] Fallback (DEPRECATED): found {len(rows)} recent documents")
        
        results: list[SearchResultChunk] = []
        for row in rows:
            snippet = self._create_snippet(row["chunk_text"], "")
            results.append(self._row_to_search_result(row, 0.05, snippet))
        
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
