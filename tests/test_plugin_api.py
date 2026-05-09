import unittest

import packages.plugin_api as plugin_api
from packages.plugin_api import (
    Command,
    DocumentAction,
    ExamplePlugin,
    MenuAction,
    PluginContext,
    PluginRegistry,
    SidebarPanel,
)


class PluginApiTest(unittest.TestCase):
    def test_plugin_api_imports(self):
        self.assertIsNotNone(plugin_api)
        self.assertIsNotNone(PluginContext)
        self.assertIsNotNone(PluginRegistry)

    def test_context_registers_extension_points(self):
        registry = PluginRegistry()
        context = PluginContext(app_name="test", registry=registry)

        context.register_command(Command("test.command", "Test Command", lambda: "ok"))
        context.register_menu_action(MenuAction("test.menu", "Test Menu", command_id="test.command"))
        context.register_document_action(DocumentAction("test.document", "Test Document"))
        context.register_sidebar_panel(SidebarPanel("test.sidebar", "Test Sidebar"))

        self.assertEqual([command.id for command in registry.get_commands()], ["test.command"])
        self.assertEqual([action.id for action in registry.get_menu_actions()], ["test.menu"])
        self.assertEqual([action.id for action in registry.get_document_actions()], ["test.document"])
        self.assertEqual([panel.id for panel in registry.get_sidebar_panels()], ["test.sidebar"])

    def test_example_plugin_registers_command_on_activation(self):
        registry = PluginRegistry()
        context = PluginContext(app_name="test", registry=registry)
        plugin = ExamplePlugin()

        registry.register_plugin(plugin)
        activated = registry.activate_plugin(plugin.id, context)

        self.assertTrue(activated)
        self.assertTrue(registry.is_active(plugin.id))
        self.assertTrue(plugin.activated)
        commands = registry.get_commands()
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0].id, "example.say_hello")
        self.assertEqual(commands[0].handler(), "hello")

    def test_empty_registry_returns_empty_lists(self):
        registry = PluginRegistry()

        self.assertEqual(registry.get_commands(), [])
        self.assertEqual(registry.get_menu_actions(), [])
        self.assertEqual(registry.get_document_actions(), [])
        self.assertEqual(registry.get_sidebar_panels(), [])

    def test_plugin_activation_exception_does_not_break_registry(self):
        class BrokenPlugin:
            id = "broken.plugin"
            name = "Broken Plugin"
            version = "0.1.0"

            def activate(self, context):
                raise RuntimeError("boom")

            def deactivate(self):
                pass

        registry = PluginRegistry()
        plugin = BrokenPlugin()
        registry.register_plugin(plugin)

        activated = registry.activate_plugin(plugin.id, PluginContext(registry=registry))

        self.assertFalse(activated)
        self.assertFalse(registry.is_active(plugin.id))
        self.assertIsInstance(registry.get_activation_error(plugin.id), RuntimeError)
        self.assertEqual(registry.get_commands(), [])


if __name__ == "__main__":
    unittest.main()
