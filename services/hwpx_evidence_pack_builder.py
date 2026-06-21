from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from services.hwpx_structured_preprocessor import StructuredBlock, StructuredDocument


logger = logging.getLogger(__name__)

MAX_EVIDENCE_LENGTH = 3500

QUESTION_STOPWORDS = {
    "관련",
    "내용",
    "정보",
    "자료",
    "사항",
    "알려줘",
    "알려주세요",
    "설명",
    "설명해줘",
    "정리",
    "정리해줘",
    "대해서",
    "관련해서",
    "무엇",
    "어떻게",
}


@dataclass
class EvidencePackResult:
    content: str
    used_block_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_evidence_pack(
    structured_data: dict[str, Any] | None,
    question: str,
    max_chars: int = MAX_EVIDENCE_LENGTH,
) -> EvidencePackResult:
    if not structured_data:
        return EvidencePackResult(content="", warnings=["HWPX_STRUCTURED_MISSING"])

    document = StructuredDocument.from_dict(structured_data)
    if not document.blocks:
        return EvidencePackResult(content="", warnings=["HWPX_STRUCTURED_EMPTY"])

    normalized_question = _normalize_query(question)
    tokens = _extract_tokens(normalized_question)

    scored = _score_blocks(document.blocks, tokens, normalized_question)
    if not scored:
        return EvidencePackResult(content="", warnings=["HWPX_EVIDENCE_EMPTY"])

    content_lines: list[str] = []
    used_ids: list[str] = []

    for block in scored:
        block_text = _format_block(block)
        if not block_text:
            continue
        if _would_exceed(content_lines, block_text, max_chars):
            break
        content_lines.append(block_text)
        used_ids.append(block.block_id)

    return EvidencePackResult(content="\n\n".join(content_lines).strip(), used_block_ids=used_ids)


def _normalize_query(question: str) -> str:
    if not question:
        return ""
    value = question.lower()
    for stop in QUESTION_STOPWORDS:
        value = value.replace(stop, " ")
    return re.sub(r"\s+", " ", value).strip()


def _extract_tokens(question: str) -> list[str]:
    if not question:
        return []
    tokens = [token.strip(".,!?()[]{}\"'“”‘’·") for token in question.split()]
    return [token for token in tokens if token and token not in QUESTION_STOPWORDS]


def _score_blocks(blocks: list[StructuredBlock], tokens: list[str], question: str) -> list[StructuredBlock]:
    scored: list[tuple[float, StructuredBlock]] = []

    for block in blocks:
        search_text = (block.search_text or "").lower()
        if not search_text:
            continue
        score = 0.0
        for token in tokens:
            if token and token in search_text:
                score += 1.0
        score += _block_weight(block, question)
        if score > 0:
            scored.append((score, block))

    if not scored:
        # fall back to top blocks for summary
        for block in blocks[:10]:
            scored.append((1.0, block))

    scored.sort(key=lambda item: (-item[0], item[1].order))
    return [block for _, block in scored[:30]]


def _block_weight(block: StructuredBlock, question: str) -> float:
    base = {
        "table_row": 1.6,
        "key_value": 1.4,
        "table": 1.2,
        "paragraph": 1.0,
        "heading": 0.9,
        "list_item": 0.9,
    }.get(block.block_type, 0.5)

    if _looks_numeric_question(question) and block.block_type in {"table_row", "key_value"}:
        base += 0.6

    if _looks_date_question(question) and block.block_type in {"table_row", "paragraph", "key_value"}:
        base += 0.4

    return base


def _looks_numeric_question(question: str) -> bool:
    if not question:
        return False
    return any(token in question for token in ["금액", "요금", "가격", "비용", "원", "%", "수치", "수량", "인원"])


def _looks_date_question(question: str) -> bool:
    if not question:
        return False
    return any(token in question for token in ["날짜", "일정", "기간", "시간", "마감", "부터", "까지"])


def _format_block(block: StructuredBlock) -> str:
    label = block.block_type.replace("_", " ")
    heading = " > ".join(block.heading_path) if block.heading_path else ""
    header_line = f"[Block {block.order} | {label}]"
    if heading:
        header_line += f" Section: {heading}"

    body = block.markdown or block.normalized_text or block.raw_text
    body = body.strip()
    if not body:
        return ""

    return f"{header_line}\n{body}"


def _would_exceed(lines: list[str], addition: str, max_chars: int) -> bool:
    current = len("\n\n".join(lines))
    return current + len(addition) + 2 > max_chars
