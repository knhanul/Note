import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.chroma_vector_store import ChromaVectorStore
from services.ollama_embedding_service import OllamaEmbeddingService
from services.rank_fusion import reciprocal_rank_fusion

logger = logging.getLogger(__name__)


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
    relevance_tier: str = "direct_evidence"


class AiSearchService:
    MAX_LIMIT = 100
    DEFAULT_LIMIT = 20
    SNIPPET_LENGTH = 150
    STRICT_SCORE_THRESHOLD = 0.5
    RELAXED_SCORE_THRESHOLD = 0.3
    TITLE_SCORE_THRESHOLD = 0.5
    MAX_CHUNKS_PER_DOC = 3
    UNRELATED_SCORE_THRESHOLD = 0.5
    HYBRID_CANDIDATE_LIMIT = 15
    RRF_K = 60
    RRF_SCORE_SCALE = 100.0

    PROCEDURE_QUERY_KEYWORDS = [
        "방법", "절차", "방식", "방안", "진행", "어떻게",
        "처리방법", "교체방법", "도입방법", "검토방법",
    ]

    BUSINESS_METHOD_SYNONYMS = [
        "절차", "방안", "검토", "방식", "계획", "진행",
    ]

    PROCEDURE_CONTEXT_KEYWORDS = [
        "절차", "방안", "검토", "안건", "제안", "건의",
        "구매", "렌탈", "도입", "시공", "비용", "견적",
        "비교", "대안", "추진", "승인", "보고",
    ]

    BROAD_TERM_PENALTY_THRESHOLD = 0.3

    BROKEN_TABLE_MARKERS = ["column 1", "column 2", "column 3"]

    STOPWORDS = {
        "관련", "내용", "정보", "자료", "건", "사항",
        "알려줘", "알려주세요", "설명", "설명해줘",
        "정리", "정리해줘", "대해서", "관련해서",
        "무엇", "어떻게", "란", "이란", "란?", "이란?",
        "무엇인가", "무엇인가요", "무엇인지",
        "대해", "관해", "관하여", "대하여",
    }

    QUERY_EXPRESSION_PATTERNS = [
        "알려줘", "알려주세요", "알겠어요", "알겠습니다",
        "설명해줘", "설명해주세요", "설명해 주세요",
        "정리해줘", "정리해주세요", "정리해 주세요",
        "대해서", "관련해서", "관해", "대해", "관하여", "대하여",
        "무엇", "무엇인가", "무엇인가요", "무엇인지",
        "어떻게", "어떤", "어디", "언제", "왜", "얼마",
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

    KOREAN_QUESTION_SUFFIXES = [
        "란?", "이란?", "란", "이란",
        "인가요?", "인가요", "인가", "인지",
        "는?", "은?", "가?", "이?",
        "할까?", "할까요?", "할까", "할까요",
        "몰라?", "몰라요?", "아니?", "아니요?",
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
        "교체방법": ["교체", "교체 절차", "교체 방안", "교체 검토"],
        "도입방법": ["도입", "도입 절차", "도입 방안", "도입 검토"],
        "처리방법": ["처리", "처리 절차", "처리 방안"],
        "검토방법": ["검토", "검토 방안", "검토 절차"],
    }

    def __init__(
        self,
        repository: AiDocumentIndexRepository,
        embedding_service: OllamaEmbeddingService | None = None,
        vector_store: ChromaVectorStore | None = None,
    ):
        self._repo = repository
        self._embedding = embedding_service
        self._vector_store = vector_store

    def classify_question_type(self, query: str) -> str:
        """Classify question type based on keywords."""
        if not query:
            return "general"
        query_lower = query.lower()
        for kw in self.PROCEDURE_QUERY_KEYWORDS:
            if kw in query_lower:
                return "procedure_query"
        return "general"

    def normalize_query(self, query: str) -> str:
        """Normalize user query by removing query expressions and extracting core keywords."""
        logger = logging.getLogger(__name__)
        
        original = (query or "").strip()
        normalized = original.lower()
        removed_phrases: list[str] = []

        for suffix in self.KOREAN_QUESTION_SUFFIXES:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].rstrip()
                removed_phrases.append(suffix)
                break

        for pattern in self.QUERY_EXPRESSION_PATTERNS:
            if pattern in normalized:
                removed_phrases.append(pattern)
            normalized = normalized.replace(pattern, " ")

        normalized = normalized.strip("?,.!")

        tokens = [token.strip(".,!?()[]{}\"'“”‘’·") for token in re.split(r"\s+", normalized) if token.strip()]
        kept_tokens: list[str] = []
        removed_tokens: list[str] = []

        for token in tokens:
            if self._is_meaningful_token(token):
                kept_tokens.append(token)
            else:
                removed_tokens.append(token)

        if not kept_tokens:
            fallback_token = self._pick_fallback_token(tokens, original)
            if fallback_token:
                kept_tokens = [fallback_token]

        normalized_query = " ".join(self._dedupe_preserve_order(kept_tokens))
        normalized_query = " ".join(normalized_query.split())

        logger.info(
            "[AiSearchService] Query normalization: original='%s', normalized='%s', removed_suffixes=%s",
            query, normalized_query, self._dedupe_preserve_order(removed_phrases),
        )
        return normalized_query

    def _is_meaningful_token(self, token: str) -> bool:
        if not token:
            return False
        if any(char.isdigit() for char in token):
            return True
        return token not in self.STOPWORDS

    def _pick_fallback_token(self, tokens: list[str], original: str) -> str:
        for token in tokens:
            if any(char.isdigit() for char in token):
                return token
        for token in tokens:
            if token and token not in self.STOPWORDS:
                return token
        original_tokens = [token.strip(".,!?()[]{}\"'“”‘’·") for token in original.split() if token.strip()]
        return original_tokens[0] if original_tokens else ""

    def _dedupe_preserve_order(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def generate_search_queries(self, normalized_query: str, question_type: str = "general") -> list[str]:
        """Generate search queries from normalized query."""
        logger = logging.getLogger(__name__)

        queries: list[str] = []
        seen: set[str] = set()

        if normalized_query:
            queries.append(normalized_query)
            seen.add(normalized_query)

            words = normalized_query.split()
            if len(words) >= 2:
                compact = "".join(words)
                if compact not in seen:
                    queries.append(compact)
                    seen.add(compact)

        for term in normalized_query.split():
            if term and term not in seen:
                queries.append(term)
                seen.add(term)

        for key, synonyms in self.QUERY_EXPANSION_MAP.items():
            if key in normalized_query:
                for syn in synonyms:
                    if syn not in seen and syn not in self.STOPWORDS:
                        queries.append(syn)
                        seen.add(syn)

                for syn in synonyms[:3]:
                    combined = f"{normalized_query.replace(key, '').strip()} {syn}".strip()
                    if combined and combined not in seen and combined not in self.STOPWORDS:
                        queries.append(combined)
                        seen.add(combined)

        if question_type == "procedure_query":
            core_words = [w for w in normalized_query.split() if w and w not in self.STOPWORDS]
            if core_words:
                core_phrase = " ".join(core_words)
                for syn in self.BUSINESS_METHOD_SYNONYMS:
                    expanded = f"{core_phrase} {syn}"
                    if expanded not in seen:
                        queries.append(expanded)
                        seen.add(expanded)
                for word in core_words:
                    for syn in self.BUSINESS_METHOD_SYNONYMS[:3]:
                        expanded = f"{word} {syn}"
                        if expanded not in seen:
                            queries.append(expanded)
                            seen.add(expanded)

        result = queries[:15]
        logger.info(f"[AiSearchService] Generated search queries: {result}")
        return result

    def search_keyword(
        self, query: str, limit: int = 20, offset: int = 0, fallback: bool = False
    ) -> list[SearchResultChunk]:
        if not query or not query.strip():
            return []

        limit = self._normalize_limit(limit)
        offset = self._normalize_offset(offset)

        question_type = self.classify_question_type(query)
        normalized_query = self.normalize_query(query)
        search_queries = self.generate_search_queries(normalized_query, question_type)

        logger.info(f"[AiSearchService] question_type={question_type}")
        logger.info(f"[AiSearchService] original_query='{query}', normalized_query='{normalized_query}', generated_search_queries={search_queries}")

        keyword_results = self._search_keyword_candidates(normalized_query, search_queries, question_type)
        vector_results = self._search_vector_chunks(query, self.HYBRID_CANDIDATE_LIMIT)
        results = self._fuse_hybrid_results(keyword_results, vector_results)

        if not results:
            return []

        results = self._apply_title_exact_match_boost(results, normalized_query)
        results = self._apply_unrelated_penalty(results, normalized_query)

        if question_type == "procedure_query":
            broad_terms = self._identify_broad_terms(normalized_query)
            if broad_terms:
                results = self._apply_broad_term_penalty(results, broad_terms)
                logger.info(f"[AiSearchService] broad_term_penalty_terms={broad_terms}")
            results = self._apply_procedure_context_boost(results, normalized_query)
            results = self._apply_broken_table_penalty(results)

        results.sort(key=lambda r: (-r.score, r.title or "", r.document_id, r.chunk_order))

        exact_title_docs = self._find_exact_title_matches(normalized_query)
        if exact_title_docs:
            results = self._filter_by_exact_title_docs(results, exact_title_docs)
            logger.info(f"[AiSearchService] exact_title_match_docs={len(exact_title_docs)}, filtered_results={len(results)}")

        results = self._apply_chunk_cap_per_doc(results, self.MAX_CHUNKS_PER_DOC)

        for r in results:
            r.relevance_tier = self._classify_relevance(r, normalized_query)

        direct_evidence = [r for r in results if r.relevance_tier == "direct_evidence"]
        possible_related = [r for r in results if r.relevance_tier == "possible_related"]

        logger.info(
            "[AiSearchService] final: direct=%d, possible_related=%d, total=%d",
            len(direct_evidence), len(possible_related), len(results),
        )

        return results[offset : offset + limit]

    def _search_keyword_candidates(
        self,
        normalized_query: str,
        search_queries: list[str],
        question_type: str,
    ) -> list[SearchResultChunk]:
        strict_results = self._search_chunks(search_queries, self.STRICT_SCORE_THRESHOLD, "strict", question_type)
        logger.info(f"[AiSearchService] strict_result_count={len(strict_results)}")

        if strict_results:
            return strict_results

        relaxed_results = self._search_chunks(search_queries, self.RELAXED_SCORE_THRESHOLD, "relaxed", question_type)
        logger.info(f"[AiSearchService] relaxed_result_count={len(relaxed_results)}")

        title_results = self._search_by_title(search_queries)
        logger.info(f"[AiSearchService] title_result_count={len(title_results)}")

        all_results = {r.chunk_id: r for r in relaxed_results}
        for result in title_results:
            if result.chunk_id not in all_results:
                all_results[result.chunk_id] = result
        return list(all_results.values())

    def _search_vector_chunks(self, query: str, limit: int) -> list[SearchResultChunk]:
        if not self._embedding or not self._vector_store or not self._vector_store.enabled:
            return []

        embedding = self._embedding.embed_text(query)
        if not embedding:
            return []

        chunk_ids = self._vector_store.query(embedding=embedding, limit=limit)
        if not chunk_ids:
            return []

        chunk_rows = self._fetch_chunks_by_ids(chunk_ids)
        results: list[SearchResultChunk] = []
        for rank, chunk_id in enumerate(chunk_ids):
            row = chunk_rows.get(chunk_id)
            if not row:
                continue
            snippet = self._create_snippet(row["chunk_text"], query.lower())
            score = float(limit - rank)
            results.append(self._row_to_search_result(row, score, snippet))
        logger.info("[AiSearchService] vector_result_count=%d", len(results))
        return results

    def _fuse_hybrid_results(
        self,
        keyword_results: list[SearchResultChunk],
        vector_results: list[SearchResultChunk],
    ) -> list[SearchResultChunk]:
        if not keyword_results and not vector_results:
            return []

        if not vector_results:
            return keyword_results

        if not keyword_results:
            return vector_results

        keyword_ids = [result.chunk_id for result in keyword_results]
        vector_ids = [result.chunk_id for result in vector_results]

        fused_scores = reciprocal_rank_fusion(
            [keyword_ids, vector_ids],
            rrf_k=self.RRF_K,
            max_results=self.HYBRID_CANDIDATE_LIMIT,
        )

        combined_map: dict[str, SearchResultChunk] = {}
        for result in keyword_results:
            combined_map[result.chunk_id] = result
        for result in vector_results:
            if result.chunk_id not in combined_map:
                combined_map[result.chunk_id] = result

        fused_results: list[SearchResultChunk] = []
        for chunk_id, fused_score in fused_scores:
            result = combined_map.get(chunk_id)
            if not result:
                continue
            result.score = fused_score * self.RRF_SCORE_SCALE
            fused_results.append(result)

        logger.info(
            "[AiSearchService] hybrid_fused_count=%d keyword_count=%d vector_count=%d",
            len(fused_results),
            len(keyword_results),
            len(vector_results),
        )
        return fused_results

    def _fetch_chunks_by_ids(self, chunk_ids: list[str]) -> dict[str, dict]:
        if not chunk_ids:
            return {}

        placeholders = ",".join(["?"] * len(chunk_ids))
        conn = self._repo._db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT
                c.chunk_id,
                c.document_id,
                d.title,
                d.source_type,
                d.source_path,
                d.note_id,
                c.heading_path_json,
                c.chunk_text,
                c.search_text,
                c.block_type,
                c.chunk_order
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE c.chunk_id IN ({placeholders})
            """,
            chunk_ids,
        )
        rows = cursor.fetchall()
        return {row["chunk_id"]: row for row in rows}

    def _search_chunks(self, queries: list[str], threshold: float, search_type: str, question_type: str = "general") -> list[SearchResultChunk]:
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
                    c.search_text,
                    c.block_type,
                    c.chunk_order
                FROM ai_document_chunks c
                JOIN ai_documents d ON c.document_id = d.document_id
                WHERE d.title LIKE ?
                   OR c.heading_path_json LIKE ?
                   OR c.search_text LIKE ?
                   OR c.chunk_text LIKE ?
                ORDER BY c.chunk_order
            """, (like_pattern, like_pattern, like_pattern, like_pattern))
            rows = cursor.fetchall()

            for row in rows:
                score = self._calculate_score(
                    row["title"],
                    row["heading_path_json"],
                    row["search_text"] or row["chunk_text"],
                    row["block_type"],
                    sq,
                    sq_lower,
                    question_type,
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
                    c.search_text,
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

    def _apply_title_exact_match_boost(
        self, results: list[SearchResultChunk], normalized_query: str
    ) -> list[SearchResultChunk]:
        if not normalized_query:
            return results
        nq = normalized_query.lower()
        for r in results:
            if r.title and r.title.lower() == nq:
                r.score += 5.0
            elif r.title and nq in r.title.lower():
                r.score += 2.0
        return results

    def _apply_unrelated_penalty(
        self, results: list[SearchResultChunk], normalized_query: str
    ) -> list[SearchResultChunk]:
        if not normalized_query:
            return results
        query_words = set(normalized_query.lower().split())
        for r in results:
            title_lower = (r.title or "").lower()
            chunk_lower = (r.chunk_text or "").lower()
            has_any_query_word = any(w in title_lower or w in chunk_lower for w in query_words)
            if not has_any_query_word and r.score < self.UNRELATED_SCORE_THRESHOLD:
                r.score *= 0.1
        return results

    def _identify_broad_terms(self, normalized_query: str) -> list[str]:
        """Identify broad terms that should have lower search weight."""
        query_words = [w for w in normalized_query.split() if w]
        broad_terms = []
        for word in query_words:
            conn = self._repo._db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(DISTINCT c.chunk_id) as cnt FROM ai_document_chunks c JOIN ai_documents d ON c.document_id = d.document_id WHERE d.title LIKE ? OR c.search_text LIKE ? OR c.chunk_text LIKE ?",
                (f"%{word}%", f"%{word}%", f"%{word}%"),
            )
            row = cursor.fetchone()
            count = row["cnt"] if row else 0
            if count > 20:
                broad_terms.append(word)
        return broad_terms

    def _apply_broad_term_penalty(
        self, results: list[SearchResultChunk], broad_terms: list[str]
    ) -> list[SearchResultChunk]:
        """Penalize results that only match broad terms without specific context."""
        if not broad_terms:
            return results
        broad_set = set(broad_terms)
        for r in results:
            title_lower = (r.title or "").lower()
            chunk_lower = (r.chunk_text or "").lower()
            has_broad = any(w in title_lower or w in chunk_lower for w in broad_set)
            has_specific = any(
                w in title_lower or w in chunk_lower
                for w in (set(r.chunk_text.lower().split()) if r.chunk_text else set())
                - broad_set
            )
            if has_broad and not has_specific and r.score < 2.0:
                r.score *= 0.5
        return results

    def _apply_procedure_context_boost(
        self, results: list[SearchResultChunk], normalized_query: str
    ) -> list[SearchResultChunk]:
        """Boost results containing procedure context keywords."""
        for r in results:
            chunk_lower = (r.chunk_text or "").lower()
            heading_lower = " ".join(r.heading_path).lower() if r.heading_path else ""
            combined = f"{chunk_lower} {heading_lower}"
            for kw in self.PROCEDURE_CONTEXT_KEYWORDS:
                if kw in combined:
                    r.score += 0.5
                    break
        return results

    def _apply_broken_table_penalty(
        self, results: list[SearchResultChunk]
    ) -> list[SearchResultChunk]:
        """Penalize chunks containing broken table markers."""
        for r in results:
            if self._is_broken_table(r.chunk_text or ""):
                r.score *= 0.3
        return results

    def _is_broken_table(self, text: str) -> bool:
        """Check if text contains broken table markers like 'Column 1', 'Column 2'."""
        if not text:
            return False
        text_lower = text.lower()
        marker_count = sum(1 for m in self.BROKEN_TABLE_MARKERS if m in text_lower)
        return marker_count >= 2

    def _find_exact_title_matches(self, normalized_query: str) -> set[str]:
        if not normalized_query:
            return set()
        nq = normalized_query.lower()
        conn = self._repo._db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT document_id FROM ai_documents WHERE LOWER(title) = ?",
            (nq,),
        )
        rows = cursor.fetchall()
        return {row["document_id"] for row in rows}

    def _filter_by_exact_title_docs(
        self, results: list[SearchResultChunk], exact_doc_ids: set[str]
    ) -> list[SearchResultChunk]:
        if not exact_doc_ids:
            return results
        filtered = [r for r in results if r.document_id in exact_doc_ids]
        return filtered if filtered else results

    def _apply_chunk_cap_per_doc(
        self, results: list[SearchResultChunk], cap: int
    ) -> list[SearchResultChunk]:
        if cap <= 0:
            return results
        doc_counts: dict[str, int] = {}
        capped: list[SearchResultChunk] = []
        for r in results:
            doc_id = r.document_id
            count = doc_counts.get(doc_id, 0)
            if count < cap:
                capped.append(r)
                doc_counts[doc_id] = count + 1
        return capped

    def _classify_relevance(
        self, result: SearchResultChunk, normalized_query: str
    ) -> str:
        if result.score >= self.STRICT_SCORE_THRESHOLD:
            return "direct_evidence"
        if result.score >= self.RELAXED_SCORE_THRESHOLD:
            return "possible_related"
        return "unrelated"

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

    def _block_type_weight(self, block_type: Optional[str], query: str, question_type: str = "general") -> float:
        if not block_type:
            return 0.0
        base = {
            "table_row": 1.2,
            "key_value": 1.0,
            "table": 0.6,
            "paragraph": 0.2,
        }.get(block_type, 0.0)

        if self._looks_numeric_question(query) and block_type in {"table_row", "key_value"}:
            base += 0.8
        if self._looks_date_question(query) and block_type in {"table_row", "paragraph", "key_value"}:
            base += 0.4
        if question_type == "procedure_query" and block_type in {"table_row", "key_value"}:
            base += 0.6

        return base

    def _looks_numeric_question(self, query: str) -> bool:
        if not query:
            return False
        return any(token in query for token in ["금액", "요금", "가격", "비용", "원", "%", "수치", "수량", "인원"])

    def _looks_date_question(self, query: str) -> bool:
        if not query:
            return False
        return any(token in query for token in ["날짜", "일정", "기간", "시간", "마감", "부터", "까지"])

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
                   OR c.search_text LIKE ?
                   OR c.chunk_text LIKE ?
            """, (like_pattern, like_pattern, like_pattern, like_pattern))
            
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
                c.search_text,
                c.block_type,
                c.chunk_order
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE c.document_id = ?
              AND (d.title LIKE ? OR c.heading_path_json LIKE ? OR c.search_text LIKE ? OR c.chunk_text LIKE ?)
            ORDER BY c.chunk_order
        """, (document_id, like_pattern, like_pattern, like_pattern, like_pattern))
        rows = cursor.fetchall()

        results: list[SearchResultChunk] = []
        for row in rows:
            score = self._calculate_score(
                row["title"],
                row["heading_path_json"],
                row["search_text"] or row["chunk_text"],
                row["block_type"],
                query,
                query_lower,
                self.classify_question_type(query),
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
               OR c.search_text LIKE ?
               OR c.chunk_text LIKE ?
        """, (like_pattern, like_pattern, like_pattern, like_pattern))
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
              AND (d.title LIKE ? OR c.heading_path_json LIKE ? OR c.search_text LIKE ? OR c.chunk_text LIKE ?)
        """, (document_id, like_pattern, like_pattern, like_pattern, like_pattern))
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
        block_type: Optional[str],
        query: str,
        query_lower: str,
        question_type: str = "general",
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

        score += self._block_type_weight(block_type, query, question_type)

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
