from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = ROOT_DIR / "packages"


class DependencyRulesStaticTest(unittest.TestCase):
    def test_editor_core_does_not_import_ollama_plugin(self):
        editor_core_dir = PACKAGES_DIR / "editor_core"
        for py_file in editor_core_dir.rglob("*.py"):
            if py_file.name.startswith("__pycache__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            with self.subTest(file=py_file.relative_to(ROOT_DIR)):
                self.assertNotIn("from packages.ollama_plugin", content)
                self.assertNotIn("import packages.ollama_plugin", content)

    def test_editor_core_does_not_import_apps(self):
        editor_core_dir = PACKAGES_DIR / "editor_core"
        for py_file in editor_core_dir.rglob("*.py"):
            if py_file.name.startswith("__pycache__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            with self.subTest(file=py_file.relative_to(ROOT_DIR)):
                self.assertNotIn("from apps.", content)
                self.assertNotIn("import apps.", content)

    def test_plugin_api_does_not_import_ollama_plugin(self):
        plugin_api_dir = PACKAGES_DIR / "plugin_api"
        for py_file in plugin_api_dir.rglob("*.py"):
            if py_file.name.startswith("__pycache__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            with self.subTest(file=py_file.relative_to(ROOT_DIR)):
                self.assertNotIn("from packages.ollama_plugin", content)
                self.assertNotIn("import packages.ollama_plugin", content)

    def test_storage_does_not_import_qml_or_qt_qml(self):
        storage_dir = PACKAGES_DIR / "storage"
        for py_file in storage_dir.rglob("*.py"):
            if py_file.name.startswith("__pycache__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            with self.subTest(file=py_file.relative_to(ROOT_DIR)):
                self.assertNotIn("from PyQt6.QtQml", content)
                self.assertNotIn("from qml", content)
                self.assertNotIn("import qml", content)

    def test_ollama_plugin_does_not_import_requests_or_httpx(self):
        ollama_dir = PACKAGES_DIR / "ollama_plugin"
        for py_file in ollama_dir.rglob("*.py"):
            if py_file.name.startswith("__pycache__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            with self.subTest(file=py_file.relative_to(ROOT_DIR)):
                self.assertNotIn("import requests", content)
                self.assertNotIn("from requests", content)
                self.assertNotIn("import httpx", content)
                self.assertNotIn("from httpx", content)

    def test_ollama_plugin_has_no_actual_network_calls(self):
        ollama_dir = PACKAGES_DIR / "ollama_plugin"
        for py_file in ollama_dir.rglob("*.py"):
            if py_file.name.startswith("__pycache__"):
                continue
            content = py_file.read_text(encoding="utf-8")
            with self.subTest(file=py_file.relative_to(ROOT_DIR)):
                self.assertNotIn("requests.get", content)
                self.assertNotIn("requests.post", content)
                self.assertNotIn("httpx.get", content)
                self.assertNotIn("httpx.post", content)
                self.assertNotIn("urllib.request", content)


if __name__ == "__main__":
    unittest.main()
