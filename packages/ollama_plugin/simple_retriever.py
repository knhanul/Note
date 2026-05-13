"""Simple keyword-based retriever for finding relevant chunks."""

import logging
import re
from typing import List

from .simple_chunker import Chunk

logger = logging.getLogger(__name__)


class SimpleRetriever:
    """Retrieves relevant chunks based on keyword matching."""

    DEFAULT_TOP_K = 3

    def __init__(self, top_k: int = DEFAULT_TOP_K):
        self.top_k = top_k

    def retrieve(self, chunks: List[Chunk], query: str) -> List[Chunk]:
        """Retrieve top-k relevant chunks for the query."""
        if not chunks or not query or not query.strip():
            logger.warning("[SimpleRetriever] No chunks or query provided")
            return []

        query_terms = self._extract_keywords(query)
        if not query_terms:
            logger.warning("[SimpleRetriever] No keywords extracted from query")
            return chunks[:self.top_k]

        scored_chunks = []
        for chunk in chunks:
            score = self._calculate_score(chunk.text, query_terms)
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        result = [chunk for score, chunk in scored_chunks[:self.top_k]]

        logger.info(f"[SimpleRetriever] Retrieved {len(result)} chunks for query: {query[:50]}...")
        return result

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract keywords from text."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        stopwords = {
            '이', '그', '저', '것', '수', '등', '및', '또', '를', '을', '에', '의', '는', '가', '에서',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'to', 'of', 'in', 'for', 'on', 'with',
            'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once'
        }

        keywords = {w for w in words if len(w) >= 2 and w not in stopwords}
        return keywords

    def _calculate_score(self, text: str, query_terms: set[str]) -> float:
        """Calculate relevance score for a chunk."""
        text_lower = text.lower()
        score = 0.0

        for term in query_terms:
            count = text_lower.count(term)
            if count > 0:
                score += count

        if score > 0:
            length_factor = min(1.0, 200 / max(len(text), 1))
            score *= length_factor

        return score

    def format_context(self, chunks: List[Chunk]) -> str:
        """Format retrieved chunks as context string."""
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            snippet = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
            context_parts.append(f"[문단 {i}]\n{snippet}")

        return "\n\n".join(context_parts)
