"""Analyzer for AI prompt variables."""

import re
from typing import Any

NOTE_VARIABLES = {"CONTENT", "SELECTION", "TITLE", "TAGS", "CONTEXT"}
CHAT_VARIABLES = {"QUESTION", "USER_INPUT", "CHAT_MESSAGE", "CHAT_HISTORY"}
ALL_KNOWN_VARIABLES = NOTE_VARIABLES | CHAT_VARIABLES


class PromptVariableAnalyzer:
    """Analyzes prompt content to extract and classify variables."""

    VARIABLE_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

    @staticmethod
    def extract_variables(content_md: str) -> list[str]:
        """Extract all variable names from prompt content."""
        if not content_md:
            return []
        matches = PromptVariableAnalyzer.VARIABLE_PATTERN.findall(content_md)
        normalized = [m.strip().upper() for m in matches if m and m.strip()]
        return sorted(set(normalized))

    @staticmethod
    def analyze_variables(content_md: str) -> dict[str, Any]:
        """Analyze variables in prompt content and classify them."""
        variables = PromptVariableAnalyzer.extract_variables(content_md)

        note_vars = [v for v in variables if v in NOTE_VARIABLES]
        chat_vars = [v for v in variables if v in CHAT_VARIABLES]
        unknown_vars = [v for v in variables if v not in ALL_KNOWN_VARIABLES]

        needs_note = len(note_vars) > 0
        needs_chat = len(chat_vars) > 0
        needs_selection = "SELECTION" in variables
        needs_context = "CONTEXT" in variables

        return {
            "variables": variables,
            "note_variables": note_vars,
            "chat_variables": chat_vars,
            "unknown_variables": unknown_vars,
            "needs_note": needs_note,
            "needs_chat": needs_chat,
            "needs_selection": needs_selection,
            "needs_context": needs_context,
        }

    @staticmethod
    def infer_input_mode(content_md: str, explicit_input_mode: str = "auto") -> str:
        """Infer input mode based on prompt variables."""
        if explicit_input_mode and explicit_input_mode != "auto":
            return explicit_input_mode

        analysis = PromptVariableAnalyzer.analyze_variables(content_md)

        if analysis["needs_selection"]:
            return "selection_required"

        if analysis["needs_note"] and analysis["needs_chat"]:
            return "note_and_chat"

        if analysis["needs_note"]:
            return "note_required"

        if analysis["needs_chat"]:
            return "chat_only"

        return "chat_only"

    @staticmethod
    def build_validation_result(
        action_id: str,
        prompt_doc_id: str,
        content_md: str,
        explicit_input_mode: str = "auto",
    ) -> dict[str, Any]:
        """Build a comprehensive validation result for an action-prompt pair."""
        analysis = PromptVariableAnalyzer.analyze_variables(content_md)
        inferred_mode = PromptVariableAnalyzer.infer_input_mode(content_md, explicit_input_mode)

        missing_required = []
        unknown_warning = []

        if analysis["unknown_variables"]:
            unknown_warning = analysis["unknown_variables"]

        return {
            "ok": True,
            "action_id": action_id,
            "prompt_doc_id": prompt_doc_id,
            "variables": analysis["variables"],
            "note_variables": analysis["note_variables"],
            "chat_variables": analysis["chat_variables"],
            "unknown_variables": analysis["unknown_variables"],
            "missing_required_variables": missing_required,
            "inferred_input_mode": inferred_mode,
            "explicit_input_mode": explicit_input_mode,
            "needs_note": analysis["needs_note"],
            "needs_chat": analysis["needs_chat"],
            "needs_selection": analysis["needs_selection"],
            "needs_context": analysis["needs_context"],
            "warnings": unknown_warning,
        }
