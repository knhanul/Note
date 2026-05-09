"""Editor adapter contract for future editor implementations."""

from typing import Callable, Protocol


class EditorAdapter(Protocol):
    def get_content(self) -> object:
        """Return the current editor content."""

    def set_content(self, content: object) -> None:
        """Replace the current editor content."""

    def save(self) -> bool:
        """Request a save through the adapter."""

    def focus(self) -> None:
        """Focus the editor surface."""

    def insert_image(self, image: object) -> None:
        """Insert an image into the editor."""

    def insert_table(self, table: object) -> None:
        """Insert a table into the editor."""

    def export_markdown(self) -> str:
        """Export the current document as markdown."""

    def on_content_changed(self, callback: Callable[[object], None]) -> None:
        """Register a content changed callback."""
