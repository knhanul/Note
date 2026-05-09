"""Editor setup helpers for the special editor skeleton."""

from dataclasses import dataclass

from packages.editor_core.adapters import CustomEditorAdapter, EditorAdapter


@dataclass(frozen=True)
class SpecialEditorConfig:
    mode: str = "special_editor_skeleton"
    adapter_name: str = "custom_editor_stub"
    runtime_connected: bool = False


def get_default_editor_adapter() -> EditorAdapter:
    return CustomEditorAdapter()


def create_special_editor_config() -> SpecialEditorConfig:
    return SpecialEditorConfig()


def describe_special_editor_mode() -> str:
    return "Special editor skeleton uses adapter stubs only and does not replace WebNoteEditor."
