"""Plugin registry for Note2 plugin API."""

from __future__ import annotations

from typing import Dict, List, Optional

from .actions import DocumentAction, MenuAction, SidebarPanel
from .command import Command


class PluginRegistry:
    """In-memory registry for plugins and extension contributions."""

    def __init__(self) -> None:
        self._plugins: Dict[str, object] = {}
        self._active_plugins: set[str] = set()
        self._activation_errors: Dict[str, Exception] = {}
        self._commands: Dict[str, Command] = {}
        self._menu_actions: Dict[str, MenuAction] = {}
        self._document_actions: Dict[str, DocumentAction] = {}
        self._sidebar_panels: Dict[str, SidebarPanel] = {}

    def register_plugin(self, plugin: object) -> object:
        plugin_id = getattr(plugin, "id", "")
        if not plugin_id:
            raise ValueError("plugin.id is required")
        self._plugins[plugin_id] = plugin
        return plugin

    def activate_plugin(self, plugin_or_id: object, context: Optional[object] = None) -> bool:
        plugin = self._resolve_plugin(plugin_or_id)
        if plugin is None:
            return False

        plugin_id = getattr(plugin, "id")
        if context is None:
            from .context import PluginContext

            context = PluginContext(registry=self)

        try:
            plugin.activate(context)
        except Exception as exc:  # noqa: BLE001
            self._activation_errors[plugin_id] = exc
            return False

        self._activation_errors.pop(plugin_id, None)
        self._active_plugins.add(plugin_id)
        return True

    def deactivate_plugin(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return False

        try:
            plugin.deactivate()
        except Exception as exc:  # noqa: BLE001
            self._activation_errors[plugin_id] = exc
            return False

        self._active_plugins.discard(plugin_id)
        return True

    def register_command(self, command: Command) -> Command:
        self._commands[command.id] = command
        return command

    def register_menu_action(self, action: MenuAction) -> MenuAction:
        self._menu_actions[action.id] = action
        return action

    def register_document_action(self, action: DocumentAction) -> DocumentAction:
        self._document_actions[action.id] = action
        return action

    def register_sidebar_panel(self, panel: SidebarPanel) -> SidebarPanel:
        self._sidebar_panels[panel.id] = panel
        return panel

    def get_commands(self) -> List[Command]:
        return list(self._commands.values())

    def get_menu_actions(self) -> List[MenuAction]:
        return list(self._menu_actions.values())

    def get_document_actions(self) -> List[DocumentAction]:
        return list(self._document_actions.values())

    def get_sidebar_panels(self) -> List[SidebarPanel]:
        return list(self._sidebar_panels.values())

    def get_activation_error(self, plugin_id: str) -> Optional[Exception]:
        return self._activation_errors.get(plugin_id)

    def is_active(self, plugin_id: str) -> bool:
        return plugin_id in self._active_plugins

    def _resolve_plugin(self, plugin_or_id: object) -> Optional[object]:
        if isinstance(plugin_or_id, str):
            return self._plugins.get(plugin_or_id)
        plugin_id = getattr(plugin_or_id, "id", "")
        if plugin_id and plugin_id not in self._plugins:
            self.register_plugin(plugin_or_id)
        return plugin_or_id
