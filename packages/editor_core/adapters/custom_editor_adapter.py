"""Custom editor adapter stub for future special-purpose editors."""

from typing import Callable


class CustomEditorAdapter:
    def get_content(self) -> object:
        return None

    def set_content(self, content: object) -> None:
        raise NotImplementedError("CustomEditorAdapter has no runtime editor implementation yet.")

    def save(self) -> bool:
        return False

    def focus(self) -> None:
        raise NotImplementedError("CustomEditorAdapter has no runtime focus target yet.")

    def insert_image(self, image: object) -> None:
        raise NotImplementedError("CustomEditorAdapter has no image insertion implementation yet.")

    def insert_table(self, table: object) -> None:
        raise NotImplementedError("CustomEditorAdapter has no table insertion implementation yet.")

    def export_markdown(self) -> str:
        return ""

    def on_content_changed(self, callback: Callable[[object], None]) -> None:
        raise NotImplementedError("CustomEditorAdapter has no content event source yet.")
