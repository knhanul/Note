from dataclasses import dataclass, field
from typing import Optional

from services.ai_context_builder import ContextBundle, ContextItem


@dataclass
class RagPromptSource:
    source_id: str
    chunk_id: str
    document_id: str
    title: Optional[str]
    source_type: str
    source_path: Optional[str]
    note_id: Optional[str]
    heading_path: list[str] = field(default_factory=list)
    chunk_order: int = 0


@dataclass
class RagPromptPayload:
    system_prompt: str
    user_prompt: str
    context_text: str
    sources: list[RagPromptSource] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_chars: int = 0


class AiRagPromptBuilder:
    MIN_MAX_CONTEXT_CHARS = 1000
    DEFAULT_MAX_CONTEXT_CHARS = 6000

    def __init__(self):
        pass

    def build_prompt(
        self,
        question: str,
        context_bundle: ContextBundle,
        max_context_chars: int = 6000,
        language: str = "ko",
    ) -> RagPromptPayload:
        warnings = list(context_bundle.warnings)

        max_context_chars = max(max_context_chars, self.MIN_MAX_CONTEXT_CHARS)

        if not context_bundle.items:
            warnings.append("RAG_NO_CONTEXT")
            return RagPromptPayload(
                system_prompt=self._get_system_prompt(language),
                user_prompt=question,
                context_text="",
                sources=[],
                warnings=warnings,
                total_chars=0,
            )

        unique_items = self._deduplicate_items(context_bundle.items)
        if len(unique_items) < len(context_bundle.items):
            warnings.append("RAG_DUPLICATE_SOURCE_REMOVED")

        context_text, sources, ctx_warnings = self._build_context_text(
            unique_items, max_context_chars
        )
        warnings.extend(ctx_warnings)

        system_prompt = self._get_system_prompt(language)
        user_prompt = self._build_user_prompt(question, context_text)

        total_chars = len(system_prompt) + len(user_prompt)

        return RagPromptPayload(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_text=context_text,
            sources=sources,
            warnings=warnings,
            total_chars=total_chars,
        )

    def _deduplicate_items(self, items: list[ContextItem]) -> list[ContextItem]:
        seen = set()
        unique = []
        for item in items:
            if item.chunk_id not in seen:
                seen.add(item.chunk_id)
                unique.append(item)
        return unique

    def _build_context_text(
        self, items: list[ContextItem], max_chars: int
    ) -> tuple[str, list[RagPromptSource], list[str]]:
        warnings: list[str] = []
        sources: list[RagPromptSource] = []
        blocks: list[str] = []
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

                    source = RagPromptSource(
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
                    sources.append(source)
                    total_len = sum(len(b) for b in blocks) + len(blocks) * 2
                else:
                    warnings.append("RAG_CONTEXT_TRUNCATED")
                    break
            else:
                blocks.append(block)
                total_len += block_len + 2

                source = RagPromptSource(
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
                sources.append(source)

        context_text = "\n\n".join(blocks)
        return context_text, sources, warnings

    def _get_system_prompt(self, language: str) -> str:
        if language == "ko":
            return """당신은 제공된 문서를 기반으로 답변하는 AI 어시스턴트입니다.

지침:
1. 제공된 문서(context)의 내용만 근거로 답변하세요.
2. 문서에 없는 내용은 추측하지 말고, 근거가 부족하다고 명시하세요.
3. 답변에 관련 Source 번호를 함께 표시할 수 있습니다.
4. 요약 요청 시 핵심만 정리하고, 비교 요청 시 문서별 차이를 구분하세요.
5. 불확실한 내용은 반드시 명시하세요.
6. 절차/방법 질문인 경우, 다음 형식으로 답변하세요:
   - 결론: 핵심 내용을 1-2문장으로 요약
   - 절차/단계: 번호 순서로 단계 정리
   - 비교 표: 비용/방안 비교가 있는 경우 마크다운 표로 정리
   - 추가 확인 사항: 주의점이나 확인이 필요한 항목
7. 표(table)가 포함된 경우, 마크다운 표 형식을 유지하고 행이 잘리지 않도록 하세요.
8. 기술적 용어(RAG, chunk, embedding 등)를 사용하지 말고 업무 사용자가 이해하기 쉬운 표현을 사용하세요."""
        else:
            return """You are an AI assistant that answers based on provided documents.

Guidelines:
1. Answer only based on the provided context.
2. Do not guess if the information is insufficient; explicitly state when you lack evidence.
3. You may include relevant Source numbers in your answer.
4. For summaries, provide only key points. For comparisons, highlight differences between sources.
5. Clearly indicate when you are uncertain.
6. For procedure/method questions, structure your answer as:
   - Conclusion: 1-2 sentence summary
   - Steps: numbered procedural steps
   - Comparison table: markdown table for cost/option comparisons
   - Additional notes: caveats and items to verify
7. Preserve markdown table formatting and avoid splitting table rows.
8. Use business-friendly language, not technical jargon."""

    def _build_user_prompt(self, question: str, context_text: str) -> str:
        return f"""질문:
{question}

참고 문서:
{context_text}

답변할 때:
- 핵심 답변을 먼저 작성
- 절차/방법 질문인 경우: 결론 → 절차/단계 → 비교 표(있는 경우) → 추가 확인 사항 순서로 작성
- 표(table)가 있는 경우 마크다운 표 형식으로 정리
- 필요한 경우 근거 Source 번호를 함께 표시
- 업무 사용자가 이해하기 쉬운 표현 사용
- 근거가 부족하면 부족하다고 말하기"""
