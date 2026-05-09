"""Minimal plugin API package for Note2."""

from .actions import DocumentAction, MenuAction, SidebarPanel
from .command import Command
from .context import PluginContext
from .example_plugin import ExamplePlugin
from .plugin import Plugin
from .registry import PluginRegistry

__all__ = [
    "Command",
    "DocumentAction",
    "ExamplePlugin",
    "MenuAction",
    "Plugin",
    "PluginContext",
    "PluginRegistry",
    "SidebarPanel",
]
