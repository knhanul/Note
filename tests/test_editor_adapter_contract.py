from pathlib import Path
import unittest

from packages.editor_core.adapters import CustomEditorAdapter, EditorAdapter, MarkdownEditorAdapter


ROOT_DIR = Path(__file__).resolve().parents[1]
ADAPTERS_DIR = ROOT_DIR / "packages" / "editor_core" / "adapters"


class EditorAdapterContractTest(unittest.TestCase):
    def test_adapter_imports(self):
        self.assertIsNotNone(EditorAdapter)
        self.assertIsNotNone(MarkdownEditorAdapter)
        self.assertIsNotNone(CustomEditorAdapter)

    def test_adapter_required_method_names_exist(self):
        required_methods = [
            "get_content",
            "set_content",
            "save",
            "focus",
            "insert_image",
            "insert_table",
            "export_markdown",
            "on_content_changed",
        ]

        for adapter_class in [EditorAdapter, MarkdownEditorAdapter, CustomEditorAdapter]:
            for method_name in required_methods:
                with self.subTest(adapter=adapter_class.__name__, method=method_name):
                    self.assertTrue(hasattr(adapter_class, method_name))

    def test_markdown_editor_adapter_is_unconnected_stub(self):
        adapter = MarkdownEditorAdapter()

        with self.assertRaises(NotImplementedError):
            adapter.get_content()
        with self.assertRaises(NotImplementedError):
            adapter.export_markdown()

    def test_custom_editor_adapter_safe_placeholder_results(self):
        adapter = CustomEditorAdapter()

        self.assertIsNone(adapter.get_content())
        self.assertFalse(adapter.save())
        self.assertEqual(adapter.export_markdown(), "")

    def test_adapter_readme_exists(self):
        self.assertTrue((ADAPTERS_DIR / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()
