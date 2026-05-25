from dataclasses import dataclass, field
from typing import Any, Protocol
import re

from services.ai_context_builder import ContextBundle, ContextSource
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_prompt_builder import RagPromptPayload
from services.ai_search_service import AiSearchService
from services.ai_context_builder import AiContextBuilder
from services.ai_rag_prompt_builder import AiRagPromptBuilder


@dataclass
class RagQueryOptions:
    limit: int = 8
    neighbor_window: int = 1
    max_context_chars: int = 6000
    max_chunks: int = 8
    language: str = "ko"
    model: str | None = None
    temperature: float = 0.2
    timeout_sec: float = 60.0


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
    ):
        self._search = search_service
        self._context = context_builder
        self._prompt = prompt_builder
        self._llm = llm_client

    def answer_question(
        self,
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

        search_results = self._search.search_keyword(
            question, limit=options.limit, fallback=True
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
            model=options.model or "llama3.2:3b",
            temperature=options.temperature,
            timeout_sec=options.timeout_sec,
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
            model=options.model or "llama3.2:3b",
            temperature=options.temperature,
            timeout_sec=options.timeout_sec,
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
