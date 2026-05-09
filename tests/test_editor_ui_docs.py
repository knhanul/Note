from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_UI_DIR = ROOT_DIR / "packages" / "editor_ui"


class EditorUiDocsTest(unittest.TestCase):
    def test_required_documents_exist(self):
        required_docs = [
            "README.md",
            "qml_inventory.md",
            "theme_contract.md",
            "context_properties.md",
            "component_classification.md",
            "migration_candidates.md",
            "shell_plan.md",
        ]

        for doc_name in required_docs:
            with self.subTest(document=doc_name):
                self.assertTrue((EDITOR_UI_DIR / doc_name).is_file())

    def test_docs_contain_boundary_keywords(self):
        combined_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in EDITOR_UI_DIR.glob("*.md")
        ).lower()
        keywords = ["context property", "main.qml", "webnoteeditor", "theme", "migration"]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.assertIn(keyword, combined_text)


if __name__ == "__main__":
    unittest.main()
