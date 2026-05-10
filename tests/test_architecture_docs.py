from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT_DIR / "docs"


class ArchitectureDocsTest(unittest.TestCase):
    def test_architecture_docs_exist(self):
        doc_files = [
            DOCS_DIR / "architecture.md",
            DOCS_DIR / "app_structure.md",
            DOCS_DIR / "package_structure.md",
            DOCS_DIR / "dependency_rules.md",
            DOCS_DIR / "development_roadmap.md",
            DOCS_DIR / "manual_regression_checklist.md",
        ]

        for doc_file in doc_files:
            with self.subTest(doc=doc_file.name):
                self.assertTrue(doc_file.is_file(), f"{doc_file.name} does not exist")

    def test_architecture_docs_contain_keywords(self):
        doc_keywords = {
            "architecture.md": ["apps", "packages", "markdown_editor", "work_ai_editor", "special_editor"],
            "app_structure.md": ["apps", "markdown_editor", "work_ai_editor", "special_editor"],
            "package_structure.md": ["packages", "plugin_api", "ollama_plugin", "EditorAdapter"],
            "dependency_rules.md": ["dependency"],
            "development_roadmap.md": ["packages"],
            "manual_regression_checklist.md": ["regression"],
        }

        for doc_file in DOCS_DIR.glob("*.md"):
            if doc_file.name not in doc_keywords:
                continue
            content = doc_file.read_text(encoding="utf-8").lower()
            for keyword in doc_keywords[doc_file.name]:
                with self.subTest(doc=doc_file.name, keyword=keyword):
                    self.assertIn(keyword.lower(), content, f"{doc_file.name} missing keyword '{keyword}'")


if __name__ == "__main__":
    unittest.main()
