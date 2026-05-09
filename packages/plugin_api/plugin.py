"""Base plugin protocol for Note2 plugin API."""

from typing import Protocol


class Plugin(Protocol):
    """Minimal protocol implemented by plugins."""

    id: str
    name: str
    version: str

    def activate(self, context) -> None:
        """Activate the plugin with the provided context."""

    def deactivate(self) -> None:
        """Deactivate the plugin and release transient state."""
