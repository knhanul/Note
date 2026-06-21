"""Builder for AI action execution context."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000
MAX_SELECTION_LENGTH = 2000
MAX_QUESTION_LENGTH = 1000
MAX_CHAT_HISTORY_LENGTH = 3000
MAX_CONTEXT_LENGTH = 6000


class ActionExecutionContextBuilder:
    """Builds execution context for AI actions based on input mode and available data."""

    @staticmethod
    def build_context_for_action(
        action: dict[str, Any],
        prompt_doc: dict[str, Any] | None,
        user_input: str,
        current_note: dict[str, Any] | None,
        selection: str,
        chat_history: list[dict[str, Any]] | None = None,
        retriever=None,
    ) -> dict[str, str]:
        """Build context dictionary for action execution."""
        content = current_note.get("content", "") if current_note else ""
        structured_content = None
        if current_note:
            structured_content = current_note.get("structured_content")
            if structured_content is None:
                metadata = current_note.get("metadata") or {}
                if isinstance(metadata, dict):
                    structured_content = metadata.get("structured_content")

        if structured_content and user_input:
            try:
                from services.hwpx_evidence_pack_builder import build_evidence_pack

                evidence = build_evidence_pack(structured_content, user_input)
                if evidence.content:
                    content = evidence.content
                    logger.info(
                        "[ActionExecutionContextBuilder] evidence_pack blocks=%s content_len=%s",
                        len(evidence.used_block_ids),
                        len(evidence.content),
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("[ActionExecutionContextBuilder] evidence_pack failed: %s", exc)
        title = current_note.get("title", "") if current_note else ""
        tags = current_note.get("tags", "") if current_note else ""

        context = {
            "current_note": content[:MAX_CONTENT_LENGTH],
            "content": content[:MAX_CONTENT_LENGTH],
            "CONTENT": content[:MAX_CONTENT_LENGTH],
            "SELECTION": selection[:MAX_SELECTION_LENGTH] if selection else "",
            "QUESTION": user_input[:MAX_QUESTION_LENGTH] if user_input else "",
            "USER_INPUT": user_input[:MAX_QUESTION_LENGTH] if user_input else "",
            "CHAT_MESSAGE": user_input[:MAX_QUESTION_LENGTH] if user_input else "",
            "CHAT_HISTORY": "",
            "TITLE": title,
            "TAGS": tags,
            "CONTEXT": "",
        }

        if chat_history:
            history_text = ""
            for msg in chat_history[-10:]:
                role = msg.get("role", "user")
                text = msg.get("text", "")
                history_text += f"{role}: {text}\n"
            context["CHAT_HISTORY"] = history_text[:MAX_CHAT_HISTORY_LENGTH]

        input_mode = action.get("input_mode", "auto")
        if input_mode == "auto" and prompt_doc:
            from .prompt_variable_analyzer import PromptVariableAnalyzer

            content_md = prompt_doc.get("content_md", "")
            input_mode = PromptVariableAnalyzer.infer_input_mode(content_md)

        if action.get("use_rag") and retriever and content:
            try:
                chunks = []
                if hasattr(retriever, "retrieve") and hasattr(retriever, "format_context"):
                    if user_input and user_input.strip():
                        from .simple_chunker import SimpleChunker

                        chunker = SimpleChunker()
                        chunks = chunker.chunk_text(content)
                    retrieved = retriever.retrieve(chunks, user_input or "")
                    context["CONTEXT"] = retriever.format_context(retrieved)[:MAX_CONTEXT_LENGTH]
            except Exception as e:
                logger.warning(f"[ActionExecutionContextBuilder] RAG retrieval failed: {e}")
                context["CONTEXT"] = ""

        logger.info(
            f"[ActionExecutionContextBuilder] Context built: action_id={action.get('action_id')}, "
            f"input_mode={input_mode}, content_len={len(context.get('CONTENT', ''))}, "
            f"user_input_len={len(context.get('USER_INPUT', ''))}, selection_len={len(context.get('SELECTION', ''))}"
        )

        return context

    @staticmethod
    def validate_execution_preconditions(
        action: dict[str, Any],
        inferred_input_mode: str,
        current_note: dict[str, Any] | None,
        user_input: str,
        selection: str,
    ) -> dict[str, Any]:
        """Validate if execution preconditions are met for the given input mode."""
        errors: list[str] = []
        warnings: list[str] = []

        has_note = bool(current_note and current_note.get("content"))
        has_user_input = bool(user_input and user_input.strip())
        has_selection = bool(selection and selection.strip())

        if inferred_input_mode == "chat_only":
            pass

        elif inferred_input_mode == "note_required":
            if not has_note:
                errors.append("현재 노트를 선택한 뒤 실행해주세요.")

        elif inferred_input_mode == "note_and_chat":
            if not has_note:
                errors.append("현재 노트를 선택한 뒤 실행해주세요.")
            if not has_user_input:
                errors.append("이 기능은 입력창에 질문이 필요합니다.")

        elif inferred_input_mode == "selection_required":
            if not has_selection:
                errors.append("이 기능은 선택한 문장이 필요합니다.")
                if not has_note:
                    warnings.append("선택 문장 기능은 현재 노트도 함께 제공됩니다.")

        elif inferred_input_mode == "auto":
            if not has_note and not has_user_input:
                errors.append("현재 노트를 선택하거나 질문을 입력해주세요.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "has_note": has_note,
            "has_user_input": has_user_input,
            "has_selection": has_selection,
        }
