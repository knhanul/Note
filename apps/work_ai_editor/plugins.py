"""Plugin registration helpers for the work AI editor skeleton."""

from packages.ollama_plugin import OllamaAssistantPlugin
from packages.plugin_api import PluginRegistry


def create_plugin_registry() -> PluginRegistry:
    return PluginRegistry()


def get_default_plugins() -> list[object]:
    return [OllamaAssistantPlugin()]


def register_work_ai_plugins(registry: PluginRegistry | None = None) -> PluginRegistry:
    registry = registry or create_plugin_registry()
    for plugin in get_default_plugins():
        try:
            registry.register_plugin(plugin)
        except Exception:
            continue
    return registry
