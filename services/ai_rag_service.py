from dataclasses import dataclass, field
from typing import Any, Protocol, Optional
import re
import time
import logging

logger = logging.getLogger(__name__)

from services.ai_context_builder import ContextBundle, ContextSource
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_prompt_builder import RagPromptPayload, RagPromptSource
from services.ai_search_service import AiSearchService
from services.ai_context_builder import AiContextBuilder
from services.ai_rag_prompt_builder import AiRagPromptBuilder
from services.rag_answer_prompt_loader import RagAnswerPromptLoader


@dataclass
class RagQueryOptions:
    limit: int = 8
    neighbor_window: int = 1
    max_context_chars: int = 6000
    max_chunks: int = 8
    language: str = "ko"
    model: str | None = None
    temperature: float = 0.2
    timeout_sec: float = 300.0
    max_tokens: int | None = 4096


@dataclass
class RagCitation:
    source_id: str
    chunk_id: str
    document_id: str
    title: str | None
    source_type: str
    source_path: str | None
    note_id: str | None
    heading_path: list[str] = field(default_factory=list)
    chunk_order: int = 0
    cited_in_answer: bool = False


@dataclass
class RagAnswer:
    answer_text: str
    citations: list[RagCitation] = field(default_factory=list)
    prompt_payload: RagPromptPayload | None = None
    llm_result: LlmGenerateResult | None = None
    warnings: list[str] = field(default_factory=list)


class AiRagService:
    def __init__(
        self,
        search_service: AiSearchService,
        context_builder: AiContextBuilder,
        prompt_builder: AiRagPromptBuilder,
        llm_client: LlmClient,
        default_model: str = "llama3.2:3b",
        rag_prompt_loader: Optional[RagAnswerPromptLoader] = None,
    ):
        self._search = search_service
        self._context = context_builder
        self._prompt = prompt_builder
        self._llm = llm_client
        self._default_model = default_model
        self._rag_prompt_loader = rag_prompt_loader or RagAnswerPromptLoader()
        if not self._rag_prompt_loader.is_loaded():
            self._rag_prompt_loader.load()

    def answer_question(
        self,
        question: str,
        prompt_id: str = "default_answer",
        options: RagQueryOptions | None = None,
    ) -> RagAnswer:
        if options is None:
            options = RagQueryOptions()

        warnings: list[str] = []
        start_time = time.time()

        logger.info(f"[AiRagService] RAG prompt loaded: prompt_id={prompt_id}")

        if not question or not question.strip():
            warnings.append("RAG_EMPTY_QUESTION")
            return RagAnswer(
                answer_text="",
                citations=[],
                prompt_payload=None,
                llm_result=None,
                warnings=warnings,
            )

        logger.info(f"[RAG_TIMING] Starting RAG for question: {question[:50]}...")
        search_start = time.time()
        search_results = self._search.search_keyword(
            question, limit=options.limit, fallback=True
        )
        logger.info(f"[RAG_TIMING] Search completed in {time.time() - search_start:.2f}s, results={len(search_results)}")

        if not search_results:
            warnings.append("RAG_NO_SEARCH_RESULTS")
            return RagAnswer(
                answer_text="참고문서에서 관련 내용을 찾지 못했습니다.",
                citations=[],
                prompt_payload=None,
                llm_result=None,
                warnings=warnings,
            )

        context_bundle = self._context.build_context_bundle(
            query=question,
            search_results=search_results,
            max_chars=options.max_context_chars,
            neighbor_window=options.neighbor_window,
            max_chunks=options.max_chunks,
        )

        warnings.extend(context_bundle.warnings)

        if not context_bundle.items:
            warnings.append("RAG_NO_CONTEXT")
            return RagAnswer(
                answer_text="참고문서에서 관련 내용을 찾지 못했습니다.",
                citations=context_bundle.sources,
                prompt_payload=None,
                llm_result=None,
                warnings=self._deduplicate_warnings(warnings),
            )

        # Build RAG context and sources strings
        context_text, sources, ctx_warnings = self._build_context_text_and_sources(
            context_bundle.items, options.max_context_chars
        )
        warnings.extend(ctx_warnings)

        logger.info(f"[AiRagService] RAG context length={len(context_text)}, sources count={len(sources)}")

        # Use RAG prompt loader to build custom prompts
        system_prompt, user_prompt = self._rag_prompt_loader.build_user_prompt(
            prompt_id=prompt_id,
            user_input=question,
            rag_context=context_text,
            rag_sources=self._format_sources(sources)
        )

        logger.info(f"[AiRagService] System prompt length={len(system_prompt)}, User prompt length={len(user_prompt)}")

        # Create prompt payload with custom prompts
        prompt_payload = RagPromptPayload(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_text=context_text,
            sources=sources,
            warnings=warnings,
            total_chars=len(system_prompt) + len(user_prompt),
        )

        llm_start = time.time()
        llm_options = LlmGenerateOptions(
            model=options.model or self._default_model,
            temperature=options.temperature,
            timeout_sec=options.timeout_sec,
            max_tokens=options.max_tokens,
        )

        llm_result = self._llm.generate_from_payload(prompt_payload, llm_options)
        logger.info(f"[RAG_TIMING] LLM generation completed in {time.time() - llm_start:.2f}s")

        warnings.extend(llm_result.warnings)

        citations = self._build_citations(prompt_payload, llm_result.text, warnings)

        total_time = time.time() - start_time
        logger.info(f"[RAG_TIMING] Total RAG time: {total_time:.2f}s, answer_len={len(llm_result.text)}")

        return RagAnswer(
            answer_text=llm_result.text,
            citations=citations,
            prompt_payload=prompt_payload,
            llm_result=llm_result,
            warnings=self._deduplicate_warnings(warnings),
        )

    def answer_question_in_document(
        self,
        document_id: str,
        question: str,
        options: RagQueryOptions | None = None,
    ) -> RagAnswer:
        if options is None:
            options = RagQueryOptions()

        warnings: list[str] = []

        if not question or not question.strip():
            warnings.append("RAG_EMPTY_QUESTION")
            return RagAnswer(
                answer_text="",
                citations=[],
                prompt_payload=None,
                llm_result=None,
                warnings=warnings,
            )

        search_results = self._search.search_by_document(
            document_id, question, limit=options.limit
        )

        if not search_results:
            warnings.append("RAG_NO_SEARCH_RESULTS")
            return RagAnswer(
                answer_text="",
                citations=[],
                prompt_payload=None,
                llm_result=None,
                warnings=warnings,
            )

        context_bundle = self._context.build_context_bundle(
            query=question,
            search_results=search_results,
            max_chars=options.max_context_chars,
            neighbor_window=options.neighbor_window,
            max_chunks=options.max_chunks,
        )

        warnings.extend(context_bundle.warnings)

        if not context_bundle.items:
            warnings.append("RAG_NO_CONTEXT")
            return RagAnswer(
                answer_text="",
                citations=context_bundle.sources,
                prompt_payload=None,
                llm_result=None,
                warnings=self._deduplicate_warnings(warnings),
            )

        prompt_payload = self._prompt.build_prompt(
            question=question,
            context_bundle=context_bundle,
            max_context_chars=options.max_context_chars,
            language=options.language,
        )

        warnings.extend(prompt_payload.warnings)

        llm_options = LlmGenerateOptions(
            model=options.model or self._default_model,
            temperature=options.temperature,
            timeout_sec=options.timeout_sec,
            max_tokens=options.max_tokens,
        )

        llm_result = self._llm.generate_from_payload(prompt_payload, llm_options)

        warnings.extend(llm_result.warnings)

        citations = self._build_citations(prompt_payload, llm_result.text, warnings)

        return RagAnswer(
            answer_text=llm_result.text,
            citations=citations,
            prompt_payload=prompt_payload,
            llm_result=llm_result,
            warnings=self._deduplicate_warnings(warnings),
        )

    def _build_citations(
        self, prompt_payload: RagPromptPayload, answer_text: str, warnings: list[str]
    ) -> list[RagCitation]:
        if not prompt_payload.sources:
            if answer_text:
                warnings.append("RAG_NO_CITATIONS")
            return []

        cited_ids = self._extract_cited_source_ids(answer_text)

        citations = []
        for src in prompt_payload.sources:
            citation = RagCitation(
                source_id=src.source_id,
                chunk_id=src.chunk_id,
                document_id=src.document_id,
                title=src.title,
                source_type=src.source_type,
                source_path=src.source_path,
                note_id=src.note_id,
                heading_path=src.heading_path,
                chunk_order=src.chunk_order,
                cited_in_answer=src.source_id in cited_ids,
            )
            citations.append(citation)

        for cited_id in cited_ids:
            if not any(c.source_id == cited_id for c in citations):
                warnings.append("RAG_UNKNOWN_CITATION_ID")

        return citations

    def _extract_cited_source_ids(self, answer_text: str) -> set[str]:
        if not answer_text:
            return set()

        cited = set()
        patterns = [
            r"\[S(\d+)\]",
            r"\[Source\s+(\d+)\]",
            r"(?:^|\s)S(\d+)(?:\s|$|[.,;:])",
            r"(?:^|\s)Source\s+(\d+)(?:\s|$|[.,;:])",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, answer_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                cited.add(f"S{match}")

        return cited

    def _deduplicate_warnings(self, warnings: list[str]) -> list[str]:
        seen = set()
        result = []
        for w in warnings:
            if w not in seen:
                seen.add(w)
                result.append(w)
        return result

    def _build_context_text_and_sources(
        self, items: list, max_chars: int
    ) -> tuple[str, list[RagPromptSource], list[str]]:
        """Build context text and sources list from context items."""
        warnings: list[str] = []
        blocks: list[str] = []
        sources: list[RagPromptSource] = []
        total_len = 0

        for i, item in enumerate(items):
            source_id = f"S{i + 1}"
            heading_str = " > ".join(item.heading_path) if item.heading_path else "(없음)"
            path_str = item.source.note_id or item.source.source_path or "unknown"

            block = f"""[Source {i + 1}]
Title: {item.source.title or "(제목 없음)"}
Type: {item.source.source_type}
Path: {path_str}
Heading: {heading_str}
Chunk Order: {item.chunk_order}
Content:
{item.chunk_text}"""

            block_len = len(block)

            if total_len + block_len > max_chars:
                if not blocks:
                    max_block_len = max_chars - 50
                    truncated_text = item.chunk_text[:max_block_len] + "..."
                    truncated_block = f"""[Source {i + 1}]
Title: {item.source.title or "(제목 없음)"}
Type: {item.source.source_type}
Path: {path_str}
Heading: {heading_str}
Chunk Order: {item.chunk_order}
Content:
{truncated_text}"""
                    blocks.append(truncated_block)
                    warnings.append("RAG_SOURCE_TRUNCATED")

                    sources.append(
                        RagPromptSource(
                            source_id=source_id,
                            chunk_id=item.chunk_id,
                            document_id=item.document_id,
                            title=item.source.title,
                            source_type=item.source.source_type,
                            source_path=item.source.source_path,
                            note_id=item.source.note_id,
                            heading_path=item.heading_path,
                            chunk_order=item.chunk_order,
                        )
                    )
                    total_len = sum(len(b) for b in blocks) + len(blocks) * 2
                else:
                    warnings.append("RAG_CONTEXT_TRUNCATED")
                    break
            else:
                blocks.append(block)
                total_len += block_len + 2

                sources.append(
                    RagPromptSource(
                        source_id=source_id,
                        chunk_id=item.chunk_id,
                        document_id=item.document_id,
                        title=item.source.title,
                        source_type=item.source.source_type,
                        source_path=item.source.source_path,
                        note_id=item.source.note_id,
                        heading_path=item.heading_path,
                        chunk_order=item.chunk_order,
                    )
                )

        context_text = "\n\n".join(blocks)
        return context_text, sources, warnings

    def _format_sources(self, sources: list[RagPromptSource]) -> str:
        """Format sources list for RAG_SOURCES placeholder."""
        if not sources:
            return "출처 정보 없음"

        lines = []
        for source in sources:
            title = source.title or "(제목 없음)"
            lines.append(f"- {source.source_id}: {title} ({source.source_type})")

            path_info = source.note_id or source.source_path or ""
            if path_info:
                lines.append(f"  경로: {path_info}")

            if source.heading_path:
                heading = " > ".join(source.heading_path)
                if heading and heading != "(없음)":
                    lines.append(f"  위치: {heading}")

        return "\n".join(lines)
