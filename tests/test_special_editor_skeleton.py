import importlib
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SPECIAL_EDITOR_DIR = ROOT_DIR / "apps" / "special_editor"


class SpecialEditorSkeletonTest(unittest.TestCase):
    def test_special_editor_modules_import_without_running_app(self):
        module_names = [
            "apps.special_editor",
            "apps.special_editor.main",
            "apps.special_editor.editor_setup",
        ]

        for module_name in module_names:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_special_editor_readme_exists(self):
        self.assertTrue((SPECIAL_EDITOR_DIR / "README.md").is_file())

    def test_special_editor_main_uses_project_root_config(self):
        source = (SPECIAL_EDITOR_DIR / "main.py").read_text(encoding="utf-8")
        self.assertIn("PROJECT_ROOT", source)
        self.assertIn("create_app_config(PROJECT_ROOT, sys.argv)", source)
        self.assertIn("bootstrap_app(engine, config)", source)

    def test_editor_setup_returns_stub_adapter_without_runtime_connection(self):
        editor_setup = importlib.import_module("apps.special_editor.editor_setup")
        adapter = editor_setup.get_default_editor_adapter()
        config = editor_setup.create_special_editor_config()

        self.assertEqual(adapter.__class__.__name__, "CustomEditorAdapter")
        self.assertFalse(config.runtime_connected)
        self.assertIn("does not replace WebNoteEditor", editor_setup.describe_special_editor_mode())


if __name__ == "__main__":
    unittest.main()
