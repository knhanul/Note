from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
NOTE_CONTROLLER_SOURCE = ROOT_DIR / "controllers" / "note_controller.py"
FOLDER_CONTROLLER_SOURCE = ROOT_DIR / "controllers" / "folder_controller.py"


class ControllerContractStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.note_source = NOTE_CONTROLLER_SOURCE.read_text(encoding="utf-8")
        cls.folder_source = FOLDER_CONTROLLER_SOURCE.read_text(encoding="utf-8")

    def test_note_controller_save_contract_names_exist(self):
        required_names = [
            "def _perform_save",
            "def _start_async_note_update",
            "def _on_async_save_finished",
            "_edit_version",
            "_last_saved_version",
            "_save_pending",
            "_pending_title",
            "_pending_content",
            "_pending_json",
            "def updateNoteWithJson",
            "def saveCurrentNote",
        ]

        for name in required_names:
            with self.subTest(name=name):
                self.assertIn(name, self.note_source)

    def test_note_controller_image_contract_names_exist(self):
        required_names = [
            "_DATA_URL_PATTERN",
            "_TOKEN_PATTERN",
            "def _store_data_urls_and_tokenize",
            "def _hydrate_image_tokens",
            "def saveBase64Image",
            "def saveLocalImage",
        ]

        for name in required_names:
            with self.subTest(name=name):
                self.assertIn(name, self.note_source)

    def test_note_controller_batch_note_contract_names_exist(self):
        required_names = [
            "def moveNotesToFolder",
            "def copyNotesToFolder",
            "def deleteNotes",
            "def _normalize_note_ids",
        ]

        for name in required_names:
            with self.subTest(name=name):
                self.assertIn(name, self.note_source)

    def test_folder_controller_contract_names_exist(self):
        required_names = [
            "SMART_FOLDER_PREFIX",
            "SMART_FOLDERS",
            "def createFolder",
            "def deleteFolder",
            "def renameFolder",
            "def moveFolder",
            "def reorderFolder",
            "def selectFolder",
            "def isSmartFolder",
            "def getFirstRegularFolderId",
            "def getDescendantIds",
            "def toggleFolderExpanded",
            "folderAddedForRename",
            "folderDeleteFailed",
        ]

        for name in required_names:
            with self.subTest(name=name):
                self.assertIn(name, self.folder_source)


if __name__ == "__main__":
    unittest.main()
