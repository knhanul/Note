from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol, Optional
import re
import time
import logging

logger = logging.getLogger(__name__)

from services.ai_context_builder import ContextBundle, ContextSource
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_prompt_builder import RagPromptPayload, RagPromptSource
from services.ai_search_service import AiSearchService, SearchResultChunk
from services.ai_context_builder import AiContextBuilder
from services.ai_rag_prompt_builder import AiRagPromptBuilder
from services.rag_answer_prompt_loader import RagAnswerPromptLoader, RagAnswerPrompt


@dataclass
class RagQueryOptions:
    limit: int = 5
    neighbor_window: int = 1
    max_context_chars: int = 4000
    max_chunks: int = 5
    max_chunk_chars: int = 1000
    max_chunks_per_doc: int = 2
    language: str = "ko"
    model: str | None = None
    temperature: float = 0.2
    timeout_sec: float = 300.0
    max_tokens: int | None = 4096
    is_low_mode: bool = False
    on_token: Optional[Callable[[str], None]] = None


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
    CONTEXT_TECHNICAL_LINE_PATTERNS = (
        re.compile(r"^\s*\[[^\]]*등록[^\]]*\]"),
        re.compile(r"^\s*파일\s*색인\s*실패"),
        re.compile(r"^\s*지원하지\s*않는\s*파일\s*형식"),
        re.compile(r"^\s*HWP\s*파일.*(직접\s*색인|제외|지원\s*대상)"),
    )

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

        if options.is_low_mode:
            options.max_context_chars = min(options.max_context_chars, 3000)
            options.max_chunks = min(options.max_chunks, 4)
            options.max_chunk_chars = min(options.max_chunk_chars, 900)
            logger.info(f"[AiRagService] Low mode enabled: max_context_chars={options.max_context_chars}, max_chunks={options.max_chunks}")

        warnings: list[str] = []
        start_time = time.time()

        logger.info(f"[AiRagService] RAG prompt loaded: prompt_id={prompt_id}, is_low_mode={options.is_low_mode}")

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
        
        question_type = self._search.classify_question_type(question)
        normalized_query = self._search.normalize_query(question)
        generated_queries = self._search.generate_search_queries(normalized_query, question_type)
        
        logger.info(f"[AiRagService] question_type={question_type}, original_query='{question}', normalized_query='{normalized_query}', generated_search_queries={generated_queries}")
        
        term_counts = self._search.check_index_terms(normalized_query)
        
        search_start = time.time()
        search_results = self._search.search_keyword(
            question, limit=options.limit, fallback=False
        )
        logger.info(f"[RAG_TIMING] Search completed in {time.time() - search_start:.2f}s, results={len(search_results)}")

        direct_evidence_results = [r for r in search_results if r.relevance_tier == "direct_evidence"]
        possible_related_results = [r for r in search_results if r.relevance_tier == "possible_related"]
        excluded_unrelated = [r for r in search_results if r.relevance_tier == "unrelated"]

        logger.info(
            "[AiRagService] search_classification: direct=%d, possible_related=%d, excluded_unrelated=%d",
            len(direct_evidence_results), len(possible_related_results), len(excluded_unrelated),
        )

        context_results = direct_evidence_results if direct_evidence_results else possible_related_results

        if not context_results:
            has_possible_related = False
            no_result_reason = "RAG_NO_SEARCH_RESULTS"
            
            if any(count > 0 for count in term_counts.values()):
                no_result_reason = "RAG_NO_DIRECT_EVIDENCE"
            else:
                no_result_reason = "RAG_INDEX_MAY_BE_INCOMPLETE"
            
            warnings.append(no_result_reason)
            no_results_msg = self._build_no_results_message(question, normalized_query, generated_queries, term_counts, no_result_reason)
            logger.warning(f"[AiRagService] no_result_reason={no_result_reason}, no_result_answer_len={len(no_results_msg)}")
            return RagAnswer(
                answer_text=no_results_msg,
                citations=[],
                prompt_payload=None,
                llm_result=None,
                warnings=warnings,
            )

        context_bundle = self._context.build_context_bundle(
            query=question,
            search_results=context_results,
            max_chars=options.max_context_chars,
            neighbor_window=options.neighbor_window,
            max_chunks=options.max_chunks,
        )

        warnings.extend(context_bundle.warnings)

        if not context_bundle.items:
            if context_results:
                fallback_text, fallback_citations, fallback_warnings = self._build_fallback_answer(
                    question=question,
                    normalized_query=normalized_query,
                    search_results=context_results,
                    context_bundle=context_bundle,
                    question_type=question_type,
                )
                warnings.extend(fallback_warnings)
                warnings.append("RAG_CONTEXT_EMPTY_FALLBACK")
                fallback_result = LlmGenerateResult(
                    text=fallback_text,
                    model=options.model or self._default_model,
                    provider="fallback",
                    raw={"reason": "context_empty_fallback"},
                    warnings=[],
                )
                logger.warning(f"[AiRagService] context empty but search results exist, using fallback answer_len={len(fallback_text)}")
                return RagAnswer(
                    answer_text=fallback_text,
                    citations=fallback_citations,
                    prompt_payload=None,
                    llm_result=fallback_result,
                    warnings=self._finalize_warnings(warnings, fallback_citations),
                )

            warnings.append("RAG_NO_CONTEXT")
            return RagAnswer(
                answer_text="참고문서에서 관련 내용을 찾지 못했습니다.",
                citations=context_bundle.sources,
                prompt_payload=None,
                llm_result=None,
                warnings=self._finalize_warnings(warnings, context_bundle.sources),
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
            on_token=options.on_token,
        )

        llm_result = self._llm.generate_from_payload(prompt_payload, llm_options)
        logger.info(f"[RAG_TIMING] LLM generation completed in {time.time() - llm_start:.2f}s, answer_len={len(llm_result.text)}")

        warnings.extend(llm_result.warnings)

        citations = self._build_citations(prompt_payload, llm_result.text, warnings)
        is_valid, validation_reason = self._validate_answer_quality(llm_result.text, prompt_id, citations)
        retry_used = False

        if not is_valid:
            logger.warning(f"[AiRagService] Answer validation failed: answer_len={len(llm_result.text)}, reason={validation_reason}")
            warnings.append(f"RAG_ANSWER_VALIDATION_FAILED:{validation_reason}")

            original_prompt_obj = self._rag_prompt_loader.get_prompt(prompt_id)
            retry_result = None
            retry_citations: list[RagCitation] = []

            if original_prompt_obj:
                retry_system_prompt = self._build_retry_prompt(prompt_id, original_prompt_obj)
                retry_user_prompt = user_prompt

                logger.info(f"[AiRagService] Retrying RAG answer with strict prompt")

                retry_payload = RagPromptPayload(
                    system_prompt=retry_system_prompt,
                    user_prompt=retry_user_prompt,
                    context_text=context_text,
                    sources=sources,
                    warnings=warnings,
                    total_chars=len(retry_system_prompt) + len(retry_user_prompt),
                )

                retry_options = LlmGenerateOptions(
                    model=llm_options.model,
                    temperature=llm_options.temperature,
                    timeout_sec=llm_options.timeout_sec,
                    max_tokens=llm_options.max_tokens,
                )
                retry_result = self._llm.generate_from_payload(retry_payload, retry_options)
                logger.info(f"[AiRagService] Retry completed: answer_len={len(retry_result.text)}")
                warnings.extend(retry_result.warnings)
                retry_citations = self._build_citations(retry_payload, retry_result.text, warnings)

                retry_valid, retry_reason = self._validate_answer_quality(retry_result.text, prompt_id, retry_citations)
                if retry_valid:
                    llm_result = retry_result
                    citations = retry_citations
                    retry_used = True
                    logger.info(f"[AiRagService] Retry successful: answer_len={len(llm_result.text)}")
                else:
                    logger.warning(f"[AiRagService] Retry failed: reason={retry_reason}")
                    warnings.append(f"RAG_RETRY_FAILED:{retry_reason}")

            if not retry_used:
                fallback_text, fallback_citations, fallback_warnings = self._build_fallback_answer(
                    question=question,
                    normalized_query=normalized_query,
                    search_results=context_results,
                    context_bundle=context_bundle,
                    question_type=question_type,
                )
                warnings.extend(fallback_warnings)
                warnings.append("RAG_FALLBACK_USED")
                llm_result = LlmGenerateResult(
                    text=fallback_text,
                    model=llm_options.model,
                    provider="fallback",
                    raw={
                        "reason": validation_reason,
                        "retry_used": retry_used,
                        "search_result_count": len(context_results),
                    },
                    warnings=[],
                )
                citations = fallback_citations
                logger.info(f"[AiRagService] Fallback answer generated: answer_len={len(fallback_text)}")

        processed_text, rep_count = self._remove_repeated_sentences(llm_result.text)
        if rep_count > 0:
            logger.warning(f"[AiRagService] Removed {rep_count} repeated sentences from answer")
            warnings.append(f"RAG_REPETITION_REMOVED:{rep_count}")
            llm_result = LlmGenerateResult(
                text=processed_text,
                model=llm_result.model,
                provider=llm_result.provider,
                raw=llm_result.raw,
                warnings=llm_result.warnings,
            )
            citations = self._rebuild_citations_after_postprocess(citations, processed_text)

        citation_valid = self._validate_citations(citations, processed_text)
        logger.info(f"[AiRagService] citation_validation_result={citation_valid}")
        if not citation_valid:
            warnings.append("RAG_CITATION_MISMATCH")

        logger.info(f"[AiRagService] output_style=business_readable")
        logger.info(f"[AiRagService] Final answer: answer_len={len(llm_result.text)}, retry_used={retry_used}, citations={len(citations)}")

        total_time = time.time() - start_time
        logger.info(f"[RAG_TIMING] Total RAG time: {total_time:.2f}s, answer_len={len(llm_result.text)}")

        final_warnings = self._finalize_warnings(warnings, citations)
        user_visible, hidden_technical = self._filter_user_visible_warnings(final_warnings)
        logger.info(f"[AiRagService] user_visible_warnings={user_visible}")
        logger.info(f"[AiRagService] hidden_technical_warnings={hidden_technical}")
        logger.info(f"[AiRagService] final_answer_quality={'passed' if is_valid or retry_used else 'fallback_used'}")

        return RagAnswer(
            answer_text=llm_result.text,
            citations=citations,
            prompt_payload=prompt_payload,
            llm_result=llm_result,
            warnings=user_visible,
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
                warnings=self._finalize_warnings(warnings, context_bundle.sources),
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
            on_token=options.on_token,
        )

        llm_result = self._llm.generate_from_payload(prompt_payload, llm_options)

        warnings.extend(llm_result.warnings)

        citations = self._build_citations(prompt_payload, llm_result.text, warnings)

        return RagAnswer(
            answer_text=llm_result.text,
            citations=citations,
            prompt_payload=prompt_payload,
            llm_result=llm_result,
            warnings=self._finalize_warnings(warnings, citations),
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

    def _finalize_warnings(self, warnings: list[str], citations: list[RagCitation]) -> list[str]:
        final_warnings = self._deduplicate_warnings(warnings)
        if any(c.cited_in_answer for c in citations):
            final_warnings = [w for w in final_warnings if not w.startswith("RAG_NO_CITATIONS")]
        return final_warnings

    TECHNICAL_WARNING_PREFIXES = (
        "RAG_ANSWER_VALIDATION_FAILED",
        "RAG_RETRY_FAILED",
        "RAG_REPETITION_REMOVED",
        "RAG_CITATION_MISMATCH",
        "RAG_DUPLICATE_SOURCE_REMOVED",
        "RAG_SOURCE_TRUNCATED",
        "RAG_CONTEXT_TRUNCATED",
        "CONTEXT_EXCLUDED_BROKEN_TABLES",
        "CONTEXT_PRIMARY_CHUNK_TRUNCATED",
        "CONTEXT_CHUNK_TRUNCATED",
        "CONTEXT_MAX_CHARS_REACHED",
    )

    USER_VISIBLE_WARNING_MAP = {
        "RAG_FALLBACK_USED": "참고문서 기반 요약입니다. 세부 내용은 원문을 확인하세요.",
        "RAG_CONTEXT_EMPTY_FALLBACK": "참고문서 기반 요약입니다. 세부 내용은 원문을 확인하세요.",
        "RAG_NO_CONTEXT": "참고문서에서 관련 내용을 찾지 못했습니다.",
        "RAG_NO_SEARCH_RESULTS": "검색 결과가 없습니다.",
        "RAG_NO_DIRECT_EVIDENCE": "직접적인 근거 문서를 찾지 못했습니다.",
        "RAG_INDEX_MAY_BE_INCOMPLETE": "색인이 완료되지 않았을 수 있습니다.",
        "RAG_HWP_SOURCE_QUALITY": "HWP 파일은 텍스트 추출 품질이 낮을 수 있습니다. HWPX 변환을 권장합니다.",
        "RAG_UNKNOWN_CITATION_ID": "답변에 알 수 없는 출처 번호가 포함되어 있습니다.",
        "RAG_POSSIBLE_RELATED_ONLY": "관련 가능 문서는 있으나, 직접적인 근거는 확인되지 않았습니다.",
        "RAG_EMPTY_QUESTION": "질문이 비어 있습니다.",
    }

    def _filter_user_visible_warnings(self, warnings: list[str]) -> tuple[list[str], list[str]]:
        """Split warnings into user-visible and hidden technical warnings."""
        user_visible: list[str] = []
        hidden: list[str] = []
        for w in warnings:
            is_technical = any(w.startswith(prefix) for prefix in self.TECHNICAL_WARNING_PREFIXES)
            if is_technical:
                hidden.append(w)
            elif w.startswith("OLLAMA_") or w.startswith("[OLLAMA_"):
                user_visible.append(w)
            elif w in self.USER_VISIBLE_WARNING_MAP:
                user_visible.append(self.USER_VISIBLE_WARNING_MAP[w])
            else:
                hidden.append(w)
        user_visible = list(dict.fromkeys(user_visible))
        return user_visible, hidden

    def _reconstruct_broken_tables(self, text: str) -> str:
        """Attempt to reconstruct broken markdown tables into proper format."""
        if not text:
            return text
        lines = text.split("\n")
        reconstructed: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("|") and i + 1 < len(lines):
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_line.startswith("|") and ("---" in next_line or "--" in next_line):
                    reconstructed.append(lines[i])
                    reconstructed.append(lines[i + 1])
                    i += 2
                    while i < len(lines) and lines[i].strip().startswith("|"):
                        reconstructed.append(lines[i])
                        i += 1
                    continue
            if "Column 1" in line and "Column 2" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if parts:
                    header = "| " + " | ".join(parts) + " |"
                    separator = "| " + " | ".join(["---"] * len(parts)) + " |"
                    reconstructed.append(header)
                    reconstructed.append(separator)
                    i += 1
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#"):
                        row_parts = [p.strip() for p in lines[i].split("|") if p.strip()]
                        if row_parts:
                            row = "| " + " | ".join(row_parts) + " |"
                            reconstructed.append(row)
                        i += 1
                    continue
            reconstructed.append(lines[i])
            i += 1
        return "\n".join(reconstructed)

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
            clean_chunk_text = self._sanitize_context_content(item.chunk_text or "")

            if not clean_chunk_text:
                warnings.append("RAG_CONTEXT_CHUNK_SKIPPED_NOISY")
                continue

            block = f"""[Source {i + 1}]
Title: {item.source.title or "(제목 없음)"}
Type: {item.source.source_type}
Path: {path_str}
Heading: {heading_str}
Chunk Order: {item.chunk_order}
Content:
{clean_chunk_text}"""

            block_len = len(block)

            if total_len + block_len > max_chars:
                if not blocks:
                    max_block_len = max_chars - 50
                    truncated_text = clean_chunk_text[:max_block_len] + "..."
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

    def _sanitize_context_content(self, text: str) -> str:
        if not text:
            return ""

        lines = text.splitlines()
        cleaned_lines: list[str] = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue

            if self._is_technical_context_line(stripped):
                continue

            if self._is_markdown_divider_line(stripped):
                prev_stripped = cleaned_lines[-1].strip() if cleaned_lines else ""
                if prev_stripped.startswith("|"):
                    cleaned_lines.append(line)
                    continue
                continue

            if self._is_meaningless_table_row(stripped):
                continue

            cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _is_technical_context_line(self, line: str) -> bool:
        return any(pattern.search(line) for pattern in self.CONTEXT_TECHNICAL_LINE_PATTERNS)

    def _is_markdown_divider_line(self, line: str) -> bool:
        return bool(re.match(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$", line))

    def _is_meaningless_table_row(self, line: str) -> bool:
        if not line.startswith("|"):
            return False

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            return False

        non_empty = [cell for cell in cells if cell]
        if not non_empty:
            return True

        if all(re.fullmatch(r"[A-Za-z]", cell) for cell in non_empty):
            return True

        if all(not re.search(r"[0-9A-Za-z가-힣]", cell) for cell in non_empty):
            return True

        return False

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

    def _build_no_results_message(self, question: str, normalized_query: str, generated_queries: list[str], term_counts: dict[str, int], no_result_reason: str) -> str:
        """Build a helpful message when no relevant documents are found."""
        
        not_found_terms = [term for term, count in term_counts.items() if count == 0]
        
        if no_result_reason == "RAG_INDEX_MAY_BE_INCOMPLETE":
            status_section = """### 검색 결과 상태

* 직접 근거 문서: 없음 (색인된 문서에서 검색어 미발견)
* 관련 가능 문서: 없음
* 최근 문서 임의 사용: 하지 않음"""
        else:
            status_section = """### 검색 결과 상태

* 직접 근거 문서: 없음
* 관련 가능 문서: 없음
* 최근 문서 임의 사용: 하지 않음"""
        
        return f"""### 답변

현재 색인된 참고문서에서 "{normalized_query}"에 대한 직접적인 내용은 확인되지 않았습니다.

### 확인되지 않은 항목

* {", ".join(not_found_terms[:5]) if not_found_terms else "검색어와 관련된 내용"}

{status_section}

### 다시 검색할 때 추천 표현

* {", ".join(generated_queries[:6])}

### 추가 등록이 필요한 문서

* 관련 내용을 포함한 HWPX, DOCX, PDF, TXT, MD 파일을 참고문서로 등록해 주세요.
* HWP 파일은 별도 HWPX 변환 프로그램으로 HWPX로 변환한 뒤 등록해 주세요."""

    def _validate_answer_quality(
        self,
        answer_text: str,
        prompt_id: str,
        citations: list[RagCitation] | None = None,
    ) -> tuple[bool, str]:
        """Validate if the generated answer meets quality standards."""
        stripped = (answer_text or "").strip()
        if len(stripped) < 80:
            return False, "too_short"

        answer_lower = stripped.lower()
        greeting_patterns = [
            "안녕하세요", "네", "알겠습니다", "감사합니다",
            "질문해 주셔서", "도움을 드리겠습니다", "반갑습니다",
        ]

        if any(answer_lower.startswith(p) for p in greeting_patterns):
            return False, "greeting_only"

        evasive_patterns = [
            "어떤 정보가 필요하신가요",
            "무엇이 필요하신가요",
            "더 구체적으로",
            "좀 더 자세히",
            "질문을 다시",
            "다시 말씀",
            "참고문서에서 확인되지 않습니다",
        ]
        if any(pattern in answer_lower for pattern in evasive_patterns):
            return False, "evasive_reply"

        if answer_text.strip().endswith("?") and len(stripped) < 180:
            return False, "question_only"

        if citations is not None and citations and not any(c.cited_in_answer for c in citations):
            logger.info("[AiRagService] Answer has no cited sources, but keeping LLM answer (model may omit citations)")

        if prompt_id == "evidence_based_answer" and "[근거" not in answer_text and "근거:" not in answer_text:
            return False, "no_evidence"

        if prompt_id == "checklist" and "[ ]" not in answer_text and "체크" not in answer_lower:
            return False, "no_checklist"

        technical_terms = ["rag_", "chunk_id", "embedding", "context_bundle", "search_result_chunk"]
        for term in technical_terms:
            if term in answer_lower:
                return False, "technical_term_in_answer"

        broken_table_markers = ["column 1", "column 2", "column 3"]
        marker_count = sum(1 for m in broken_table_markers if m in answer_lower)
        if marker_count >= 2:
            return False, "broken_table_in_answer"

        if "[Source" in stripped and "Content:" in stripped and "Chunk Order:" in stripped:
            return False, "raw_chunk_dump"

        return True, "valid"

    def _collect_hwp_warnings(
        self,
        context_bundle: ContextBundle,
        search_results: list[SearchResultChunk],
    ) -> list[str]:
        warnings: list[str] = []

        def has_hwp_source(source_type: str | None, source_path: str | None) -> bool:
            if not source_type and not source_path:
                return False
            if source_type == "hwp_file":
                return True
            if source_path:
                try:
                    return Path(source_path).suffix.lower() == ".hwp"
                except Exception:
                    return ".hwp" in str(source_path).lower()
            return False

        if any(has_hwp_source(src.source_type, src.source_path) for src in context_bundle.sources):
            warnings.append("RAG_HWP_SOURCE_QUALITY")
        elif any(has_hwp_source(result.source_type, result.source_path) for result in search_results):
            warnings.append("RAG_HWP_SOURCE_QUALITY")

        return warnings

    def _build_fallback_answer(
        self,
        question: str,
        normalized_query: str,
        search_results: list[SearchResultChunk],
        context_bundle: ContextBundle,
        question_type: str = "general",
    ) -> tuple[str, list[RagCitation], list[str]]:
        groups = self._group_fallback_sources(search_results, context_bundle)
        warnings: list[str] = []

        if not groups:
            return "참고문서에서 관련 내용을 찾지 못했습니다.", [], ["RAG_NO_CONTEXT"]

        lines: list[str] = []
        lines.append("### 📌 요약")
        lines.append("")
        lines.append(
            f'참고문서에서 "{normalized_query}"와 관련된 자료가 확인되었습니다. 아래에 주요 내용을 정리합니다.'
        )
        lines.append("")
        lines.append("### 📊 상세 내용")
        lines.append("")

        citations: list[RagCitation] = []

        for index, group in enumerate(groups, start=1):
            source_id = f"S{index}"
            group["source_id"] = source_id
            title = group["title"] or "제목 없음"

            lines.append(f"* [{source_id}] {title}")
            lines.append("")

            snippets = group["snippets"][:3]
            if snippets:
                for snippet in snippets:
                    clean_snippet = self._sanitize_context_content(snippet)
                    if clean_snippet:
                        lines.append(f"  * {clean_snippet}")
            else:
                lines.append("  * 본문 내용이 충분하지 않습니다.")
            lines.append("")

            first_chunk = group["chunks"][0] if group["chunks"] else None
            citations.append(
                RagCitation(
                    source_id=source_id,
                    chunk_id=first_chunk["chunk_id"] if first_chunk else f"{group['document_id']}:0",
                    document_id=group["document_id"],
                    title=title,
                    source_type=group.get("source_type") or "unknown",
                    source_path=group.get("source_path"),
                    note_id=group.get("note_id"),
                    heading_path=first_chunk["heading_path"] if first_chunk else [],
                    chunk_order=first_chunk["chunk_order"] if first_chunk else 0,
                    cited_in_answer=True,
                )
            )

        lines.append("### 🔗 참고 출처")
        lines.append("")
        for group in groups:
            source_id = group["source_id"]
            lines.append(f"* [{source_id}] {group['title'] or '제목 없음'}")

        return "\n".join(lines), citations, warnings

    def _group_fallback_sources(
        self,
        search_results: list[SearchResultChunk],
        context_bundle: ContextBundle,
    ) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}

        def ensure_group(document_id: str, source_type: str | None, source_path: str | None, note_id: str | None, title: str | None) -> dict[str, Any]:
            group = grouped.get(document_id)
            if group is None:
                group = {
                    "document_id": document_id,
                    "source_type": source_type or "unknown",
                    "source_path": source_path,
                    "note_id": note_id,
                    "title": title,
                    "chunks": [],
                    "snippets": [],
                    "chunk_count": 0,
                }
                grouped[document_id] = group
            if not group.get("title") and title:
                group["title"] = title
            if not group.get("source_path") and source_path:
                group["source_path"] = source_path
            if not group.get("note_id") and note_id:
                group["note_id"] = note_id
            if source_type and group.get("source_type") == "unknown":
                group["source_type"] = source_type
            return group

        for item in context_bundle.items:
            group = ensure_group(
                item.document_id,
                item.source.source_type,
                item.source.source_path,
                item.source.note_id,
                item.source.title,
            )
            chunk_text = (item.chunk_text or "").strip()
            group["chunk_count"] += 1
            group["chunks"].append(
                {
                    "chunk_id": item.chunk_id,
                    "chunk_order": item.chunk_order,
                    "heading_path": item.heading_path,
                    "text": chunk_text,
                }
            )
            snippet = self._extract_fallback_snippet(chunk_text)
            if snippet:
                group["snippets"].append(snippet)

        for result in search_results:
            group = ensure_group(result.document_id, result.source_type, result.source_path, result.note_id, result.title)
            if any(chunk["chunk_id"] == result.chunk_id for chunk in group["chunks"]):
                continue
            chunk_text = (result.snippet or result.chunk_text or "").strip()
            group["chunk_count"] += 1
            group["chunks"].append(
                {
                    "chunk_id": result.chunk_id,
                    "chunk_order": result.chunk_order,
                    "heading_path": result.heading_path,
                    "text": chunk_text,
                }
            )
            snippet = self._extract_fallback_snippet(chunk_text)
            if snippet:
                group["snippets"].append(snippet)

        groups = list(grouped.values())
        groups.sort(key=lambda g: (-g["chunk_count"], g["title"] or "", g["document_id"]))
        return groups

    def _extract_fallback_snippet(self, text: str, max_len: int = 180) -> str:
        if not text:
            return ""

        lines = text.splitlines()
        has_table = any(line.strip().startswith("|") for line in lines)
        if has_table:
            table_lines = [l.strip() for l in lines if l.strip()]
            result = "\n".join(table_lines)
            if len(result) <= max_len:
                return result
            return result[: max_len - 3].rstrip() + "..."

        cleaned = " ".join(text.split())
        if len(cleaned) <= max_len:
            return cleaned
        return cleaned[: max_len - 3].rstrip() + "..."

    def _shorten_source_path(self, source_path: str | None, note_id: str | None) -> str:
        if note_id:
            return f"note_id:{note_id}"
        if not source_path:
            return "(경로 없음)"

        try:
            path = Path(source_path)
            parts = path.parts
            if len(parts) <= 2:
                return str(path)
            return str(Path(*parts[-2:]))
        except Exception:
            return str(source_path)

    def _build_retry_prompt(self, prompt_id: str, original_prompt: RagAnswerPrompt) -> str:
        """Build a stricter prompt for retry."""
        retry_instructions = """

[중요 재시도 지시]
이전 답변은 부적절했습니다. 다음을 반드시 지켜주세요:
1. 인사말만 하지 마세요.
2. 아래 참고문서에 근거해 답변 형식을 반드시 채우세요.
3. 참고문서에서 확인되지 않는 내용은 없다고 명확히 말하세요.
4. 답변에는 최소 3개 이상의 의미 있는 문장을 포함하세요.
5. 출처가 있는 경우 [S1], [S2]처럼 표시하세요.
6. 가능한 경우 핵심 문장 끝에 [S1] 형식의 출처를 표시하고, 어려우면 마지막에 "참고 출처" 섹션을 추가하세요."""

        return original_prompt.system_prompt + retry_instructions

    def _remove_repeated_sentences(self, answer_text: str) -> tuple[str, int]:
        """Detect and remove repeated sentences from answer text.
        
        Returns (cleaned_text, removed_count).
        """
        if not answer_text:
            return answer_text, 0

        lines = answer_text.split("\n")
        seen_sentences: dict[str, int] = {}
        cleaned_lines: list[str] = []
        removed_count = 0

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("---") or stripped.startswith("* [S"):
                cleaned_lines.append(line)
                continue

            normalized = re.sub(r"\s+", " ", stripped).strip().lower()
            if len(normalized) < 15:
                cleaned_lines.append(line)
                continue

            if normalized in seen_sentences:
                seen_sentences[normalized] += 1
                removed_count += 1
                logger.debug(f"[AiRagService] Repeated sentence removed: {stripped[:60]}...")
                continue

            seen_sentences[normalized] = 1
            cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines)
        return cleaned_text, removed_count

    def _validate_citations(
        self, citations: list[RagCitation], answer_text: str
    ) -> bool:
        """Validate that cited source IDs in answer match actual evidence citations."""
        if not citations or not answer_text:
            return True

        cited_ids = self._extract_cited_source_ids(answer_text)
        if not cited_ids:
            return True

        valid_source_ids = {c.source_id for c in citations}
        unknown_ids = cited_ids - valid_source_ids
        if unknown_ids:
            logger.warning(f"[AiRagService] Unknown citation IDs in answer: {unknown_ids}")
            return False
        return True

    def _rebuild_citations_after_postprocess(
        self, citations: list[RagCitation], answer_text: str
    ) -> list[RagCitation]:
        """Rebuild cited_in_answer flags after text post-processing."""
        cited_ids = self._extract_cited_source_ids(answer_text)
        updated = []
        for c in citations:
            updated.append(
                RagCitation(
                    source_id=c.source_id,
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    title=c.title,
                    source_type=c.source_type,
                    source_path=c.source_path,
                    note_id=c.note_id,
                    heading_path=c.heading_path,
                    chunk_order=c.chunk_order,
                    cited_in_answer=c.source_id in cited_ids,
                )
            )
        return updated
