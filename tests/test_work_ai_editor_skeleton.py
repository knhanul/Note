import importlib
from pathlib import Path
import unittest

from packages.plugin_api import PluginRegistry


ROOT_DIR = Path(__file__).resolve().parents[1]
WORK_AI_EDITOR_DIR = ROOT_DIR / "apps" / "work_ai_editor"


class WorkAiEditorSkeletonTest(unittest.TestCase):
    def test_work_ai_editor_modules_import_without_running_app(self):
        module_names = [
            "apps.work_ai_editor",
            "apps.work_ai_editor.main",
            "apps.work_ai_editor.plugins",
        ]

        for module_name in module_names:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_work_ai_editor_readme_exists(self):
        self.assertTrue((WORK_AI_EDITOR_DIR / "README.md").is_file())

    def test_work_ai_editor_main_uses_project_root_config(self):
        source = (WORK_AI_EDITOR_DIR / "main.py").read_text(encoding="utf-8")
        self.assertIn("PROJECT_ROOT", source)
        self.assertIn("create_app_config(PROJECT_ROOT, sys.argv)", source)
        self.assertIn("bootstrap_app(engine, config)", source)

    def test_plugin_helpers_register_ollama_stub_without_activation(self):
        plugins_module = importlib.import_module("apps.work_ai_editor.plugins")
        registry = plugins_module.register_work_ai_plugins(PluginRegistry())

        self.assertIsInstance(registry, PluginRegistry)
        self.assertEqual(registry.get_commands(), [])
        self.assertFalse(registry.is_active("ollama.assistant"))


if __name__ == "__main__":
    unittest.main()
