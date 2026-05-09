"""Plugin context for Note2 plugin API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .actions import DocumentAction, MenuAction, SidebarPanel
from .command import Command
from .registry import PluginRegistry


@dataclass
class PluginContext:
    app_name: str = ""
    app_config: Optional[Any] = None
    services: Optional[Any] = None
    registry: PluginRegistry = field(default_factory=PluginRegistry)

    def register_command(self, command: Command) -> Command:
        return self.registry.register_command(command)

    def register_menu_action(self, action: MenuAction) -> MenuAction:
        return self.registry.register_menu_action(action)

    def register_document_action(self, action: DocumentAction) -> DocumentAction:
        return self.registry.register_document_action(action)

    def register_sidebar_panel(self, panel: SidebarPanel) -> SidebarPanel:
        return self.registry.register_sidebar_panel(panel)
