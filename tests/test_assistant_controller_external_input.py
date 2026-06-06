import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ollama_plugin.assistant_controller import AssistantController


class AssistantControllerExternalInputTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._tmp_path = Path(self._tmp.name)
        self.controller = AssistantController(app_data_dir=self._tmp_path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_load_external_document_json_text_success(self):
        txt_path = self._tmp_path / "sample.txt"
        txt_path.write_text("hello external text", encoding="utf-8")

        payload = json.loads(self.controller.loadExternalDocumentJson(str(txt_path)))

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_type"], "text")
        self.assertIn("hello external text", payload["content"])
        self.assertEqual(payload["source_path"], str(txt_path.resolve()))

    def test_load_external_document_json_unsupported_extension(self):
        bin_path = self._tmp_path / "sample.bin"
        bin_path.write_bytes(b"\x00\x01")

        payload = json.loads(self.controller.loadExternalDocumentJson(str(bin_path)))

        self.assertFalse(payload["ok"])
        self.assertIn("지원하지 않는 파일 형식", payload["error"])

    def test_load_external_folder_json_merges_supported_documents(self):
        folder = self._tmp_path / "docs"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "a.txt").write_text("alpha", encoding="utf-8")
        (folder / "empty.txt").write_text("", encoding="utf-8")
        sub = folder / "sub"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / "b.txt").write_text("beta", encoding="utf-8")

        payload = json.loads(self.controller.loadExternalFolderJson(str(folder)))

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["source_type"], "external_folder")
        self.assertEqual(payload["processed_count"], 2)
        self.assertEqual(payload["selected_count"], 3)
        self.assertGreaterEqual(payload["total_supported_count"], 3)
        self.assertEqual(payload.get("failed_count"), 1)
        self.assertEqual(len(payload.get("failed_files", [])), 1)
        self.assertEqual(payload["failed_files"][0]["path"], "empty.txt")
        self.assertIn("## a.txt", payload["content"])
        self.assertIn("## sub/b.txt", payload["content"])

    def test_load_external_folder_json_without_supported_documents(self):
        folder = self._tmp_path / "emptydocs"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "image.png").write_bytes(b"fake")

        payload = json.loads(self.controller.loadExternalFolderJson(str(folder)))

        self.assertFalse(payload["ok"])
        self.assertIn("지원되는 문서 파일이 없습니다", payload["error"])
        self.assertEqual(payload.get("failed_count"), 0)
        self.assertEqual(payload.get("failed_files"), [])


if __name__ == "__main__":
    unittest.main()
