import json
import io
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.ollama_plugin.assistant_controller import AssistantController
from packages.ollama_plugin.ai_worker import AIWorker


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

    def _stream_response(self, chunks):
        response = io.BytesIO(b"".join(
            (json.dumps(chunk) + "\n").encode("utf-8") for chunk in chunks
        ))
        response.status = 200
        return response

    def test_fast_worker_delivers_tokens_and_result_before_finished(self):
        events = []
        self.controller.tokenReceived.connect(lambda text: events.append(("token", text)))
        self.controller.resultReady.connect(lambda text: events.append(("result", text)))
        self.controller.runningChanged.connect(lambda running: events.append(("running", running)))
        settings = self.controller._settings_manager.settings
        settings.chat_model = "test-model"
        self.controller._worker_manager._pool = Mock()
        self.controller._worker_manager._pool.start.side_effect = lambda worker: worker.run()
        response = self._stream_response([
            {"response": "첫 답변", "done": False},
            {"response": " 완료", "done": True},
        ])
        with patch.object(self.controller, "_load_settings", return_value=settings), \
             patch("urllib.request.urlopen", return_value=response):
            self.controller._run_ai_task("질문")
        self.assertEqual(events, [
            ("running", True), ("token", "첫 답변"), ("token", " 완료"),
            ("result", "첫 답변 완료"), ("running", False),
        ])
        self.assertFalse(self.controller.isRunning)

    def test_stream_error_preserves_partial_answer_without_success(self):
        results, errors, finished = [], [], []
        self.controller.resultReady.connect(results.append)
        self.controller.errorOccurred.connect(errors.append)
        worker = AIWorker("질문", "test-model")
        worker.signals.tokenReceived.connect(self.controller._on_token_received)
        worker.signals.errorOccurred.connect(self.controller._on_error)
        worker.signals.finished.connect(self.controller._on_worker_finished)
        worker.signals.finished.connect(lambda: finished.append(True))
        response = self._stream_response([
            {"response": "부분 답변", "done": False},
            {"error": "model stopped"},
        ])
        with patch("urllib.request.urlopen", return_value=response) as request:
            worker.run()
        self.assertEqual(self.controller._response_text, "부분 답변")
        self.assertEqual(results, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("model stopped", errors[0])
        self.assertEqual(finished, [True])
        request.assert_called_once()

    def test_cancel_does_not_retry_or_report_success(self):
        worker = AIWorker("질문", "test-model")
        finished, results, errors = [], [], []
        worker.signals.tokenReceived.connect(lambda _: worker.cancel())
        worker.signals.finished.connect(lambda: finished.append(True))
        worker.signals.resultReady.connect(results.append)
        worker.signals.errorOccurred.connect(errors.append)
        with patch("urllib.request.urlopen", return_value=self._stream_response([
            {"response": "부분 답변", "done": False},
            {"response": "나머지", "done": True},
        ])) as request:
            worker.run()
        request.assert_called_once()
        self.assertEqual(finished, [True])
        self.assertEqual(results, [])
        self.assertEqual(errors, [])

    def test_warmup_uses_generation_context_options(self):
        settings = self.controller._settings_manager.settings
        settings.chat_model = "test-model"
        settings.num_ctx = 3072
        settings.num_thread = 4
        with patch("threading.Thread") as thread, \
             patch("urllib.request.urlopen", return_value=io.BytesIO(b"{}")) as request:
            thread.return_value.start.side_effect = lambda: thread.call_args.kwargs["target"]()
            self.controller.warmupModel()
        payload = json.loads(request.call_args.args[0].data)
        self.assertEqual(payload["prompt"], "")
        self.assertEqual(payload["options"]["num_ctx"], 3072)
        self.assertEqual(payload["options"]["num_thread"], 4)


if __name__ == "__main__":
    unittest.main()
