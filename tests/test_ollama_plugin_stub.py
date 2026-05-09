from pathlib import Path
import unittest

import packages.ollama_plugin as ollama_plugin
from packages.ollama_plugin import OllamaAssistantPlugin, OllamaClient, OllamaSettings
from packages.plugin_api import PluginContext, PluginRegistry


ROOT_DIR = Path(__file__).resolve().parents[1]
OLLAMA_PLUGIN_DIR = ROOT_DIR / "packages" / "ollama_plugin"


class OllamaPluginStubTest(unittest.TestCase):
    def test_ollama_plugin_imports(self):
        self.assertIsNotNone(ollama_plugin)
        self.assertIsNotNone(OllamaSettings)
        self.assertIsNotNone(OllamaClient)
        self.assertIsNotNone(OllamaAssistantPlugin)

    def test_ollama_settings_defaults_do_not_touch_files(self):
        settings = OllamaSettings()

        self.assertEqual(settings.base_url, "http://localhost:11434")
        self.assertEqual(settings.model_name, "")
        self.assertEqual(settings.timeout_sec, 30)

    def test_ollama_client_is_network_free_stub(self):
        client = OllamaClient(OllamaSettings(model_name="stub-model"))

        self.assertEqual(client.settings.model_name, "stub-model")
        self.assertEqual(client.list_models(), [])
        with self.assertRaises(NotImplementedError):
            client.generate("hello")
        with self.assertRaises(NotImplementedError):
            client.chat([])

    def test_ollama_assistant_plugin_registers_mock_commands(self):
        registry = PluginRegistry()
        context = PluginContext(app_name="work_ai_editor", registry=registry)
        plugin = OllamaAssistantPlugin()

        registry.register_plugin(plugin)
        activated = registry.activate_plugin(plugin.id, context)

        self.assertTrue(activated)
        self.assertTrue(plugin.activated)
        command_ids = [command.id for command in registry.get_commands()]
        self.assertIn("ollama.assistant.mock_summarize", command_ids)
        self.assertIn("ollama.assistant.mock_answer_selection", command_ids)
        self.assertIn("ollama.assistant.mock_work_assist", command_ids)
        for command in registry.get_commands():
            self.assertIn("not implemented yet", command.handler().lower())

    def test_ollama_docs_exist(self):
        self.assertTrue((OLLAMA_PLUGIN_DIR / "schema_draft.md").is_file())
        self.assertTrue((OLLAMA_PLUGIN_DIR / "workflow_plan.md").is_file())


if __name__ == "__main__":
    unittest.main()
