import importlib
from pathlib import Path
import unittest

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False


ROOT_DIR = Path(__file__).resolve().parents[1]
MARKDOWN_EDITOR_DIR = ROOT_DIR / "apps" / "markdown_editor"


class MarkdownEditorAppEntrypointTest(unittest.TestCase):
    @unittest.skipUnless(_HAS_WEBENGINE, "QtWebEngineWidgets not available")
    def test_app_packages_import_without_running_app(self):
        module_names = [
            "apps",
            "apps.markdown_editor",
            "apps.markdown_editor.main",
        ]

        for module_name in module_names:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_markdown_editor_readme_exists(self):
        self.assertTrue((MARKDOWN_EDITOR_DIR / "README.md").is_file())

    def test_markdown_editor_main_uses_project_root_config(self):
        source = (MARKDOWN_EDITOR_DIR / "main.py").read_text(encoding="utf-8")
        self.assertIn("PROJECT_ROOT", source)
        self.assertIn("create_app_config(PROJECT_ROOT, sys.argv)", source)
        self.assertIn("bootstrap_app(engine, config)", source)


if __name__ == "__main__":
    unittest.main()
