"""Markdown editor adapter stub.

This class represents the existing markdown/WebNoteEditor editing surface for
future adapter-based integration. It does not access QML, WebEngine, or
NoteController in the current skeleton stage.
"""

from typing import Callable


class MarkdownEditorAdapter:
    def get_content(self) -> object:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to WebNoteEditor yet.")

    def set_content(self, content: object) -> None:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to WebNoteEditor yet.")

    def save(self) -> bool:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to NoteController save yet.")

    def focus(self) -> None:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to QML focus yet.")

    def insert_image(self, image: object) -> None:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to image insertion yet.")

    def insert_table(self, table: object) -> None:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to table insertion yet.")

    def export_markdown(self) -> str:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to markdown export yet.")

    def on_content_changed(self, callback: Callable[[object], None]) -> None:
        raise NotImplementedError("MarkdownEditorAdapter is not connected to content events yet.")
