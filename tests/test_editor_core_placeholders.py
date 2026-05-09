import importlib
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_CORE_DIR = ROOT_DIR / "packages" / "editor_core"


class EditorCorePlaceholdersTest(unittest.TestCase):
    def test_editor_core_placeholder_imports(self):
        module_names = [
            "packages.editor_core",
            "packages.editor_core.placeholders.save_coordinator",
            "packages.editor_core.placeholders.image_token_service",
            "packages.editor_core.placeholders.note_filter_service",
            "packages.editor_core.placeholders.selection_state",
        ]

        for module_name in module_names:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_required_documents_exist(self):
        required_docs = [
            "README.md",
            "controller_inventory.md",
            "note_controller_responsibilities.md",
            "folder_controller_responsibilities.md",
            "core_service_candidates.md",
            "state_model_plan.md",
            "save_coordinator_plan.md",
            "image_token_service_plan.md",
            "migration_candidates.md",
        ]

        for doc_name in required_docs:
            with self.subTest(document=doc_name):
                self.assertTrue((EDITOR_CORE_DIR / doc_name).is_file())


if __name__ == "__main__":
    unittest.main()
