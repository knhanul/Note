"""Prompt renderer for substituting variables in prompt templates."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class PromptRenderer:
    """Renders prompt templates by substituting variables."""

    VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    def __init__(self):
        self._custom_filters: dict[str, callable] = {}

    def register_filter(self, name: str, func: callable) -> None:
        """Register a custom filter function."""
        self._custom_filters[name] = func
        logger.info(f"[PromptRenderer] Registered filter: {name}")

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Render a prompt template with the given context."""
        if not template:
            return ""

        result = template

        for match in self.VARIABLE_PATTERN.finditer(template):
            var_name = match.group(1)
            if var_name in context:
                value = context[var_name]
                replacement = self._apply_filters(var_name, value, context)
                result = result.replace(match.group(0), str(replacement))
            else:
                result = result.replace(match.group(0), "")

        return result

    def _apply_filters(self, var_name: str, value: Any, context: dict[str, Any]) -> str:
        """Apply any registered filters to the value."""
        filter_key = f"{var_name}_filter"
        if filter_key in context and context[filter_key] in self._custom_filters:
            filter_func = self._custom_filters[context[filter_key]]
            return filter_func(value)

        if var_name.endswith("_truncate"):
            truncate_length = context.get(f"{var_name}_length", 1000)
            return str(value)[:truncate_length]

        return value

    def extract_variables(self, template: str) -> list[str]:
        """Extract all variable names from a template."""
        return self.VARIABLE_PATTERN.findall(template)

    def validate_context(self, template: str, context: dict[str, Any]) -> list[str]:
        """Validate that all required variables are in the context."""
        required_vars = self.extract_variables(template)
        missing_vars = []

        for var in required_vars:
            if var not in context:
                missing_vars.append(var)

        return missing_vars
