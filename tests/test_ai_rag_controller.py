import unittest
import json
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly from the module file to avoid circular import through __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ai_rag_controller",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "controllers", "ai_rag_controller.py")
)
ai_rag_controller_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_rag_controller_module)
AiRagController = ai_rag_controller_module.AiRagController
FakeAppService = ai_rag_controller_module.FakeAppService

from services.ai_rag_service import RagAnswer, RagCitation
from services.ai_search_service import SearchResultChunk


class AiRagControllerTest(unittest.TestCase):
    def test_initialize_emits_status(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)

        status_values = []
        ctrl.indexStatusChanged.connect(lambda s: status_values.append(s))

        ctrl.initialize()

        self.assertTrue(fake_svc.is_initialized())
        self.assertIn("ready", status_values)

    def test_initialize_multiple_times(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)

        ctrl.initialize()
        ctrl.initialize()

        self.assertTrue(fake_svc.is_initialized())

    def test_close_emits_status(self):
        fake_svc = FakeAppService()
        fake_svc.initialize()
        ctrl = AiRagController(app_service=fake_svc)

        status_values = []
        ctrl.indexStatusChanged.connect(lambda s: status_values.append(s))

        ctrl.close()

        self.assertTrue(fake_svc.is_closed())
        self.assertIn("closed", status_values)

    def test_index_current_note_calls_service(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        status_values = []
        ctrl.indexStatusChanged.connect(lambda s: status_values.append(s))

        ctrl.indexCurrentNote("note-123", "Test Note", "# Test\n\nContent here", "[]")

        self.assertIn("note:note-123", fake_svc._indexed_docs)
        self.assertIn("indexed_current_note", status_values)

    def test_index_current_note_with_tags(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        ctrl.indexCurrentNote("note-456", "Tagged Note", "Content", '["tag1", "tag2"]')

        self.assertIn("note:note-456", fake_svc._indexed_docs)

    def test_index_current_note_malformed_tags_json(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        error_values = []
        ctrl.errorOccurred.connect(lambda e: error_values.append(e))

        ctrl.indexCurrentNote("note-789", "Note", "Content", "not valid json")

        self.assertIn("note:note-789", fake_svc._indexed_docs)

    def test_search_indexed_documents(self):
        fake_svc = FakeAppService()
        fake_svc.initialize()
        fake_svc.index_current_note("note-1", "Python Guide", "Python content")
        ctrl = AiRagController(app_service=fake_svc)

        results_json = None
        ctrl.searchResultsChanged.connect(lambda: setattr(ctrl, '_results_captured', True))

        ctrl.searchIndexedDocuments("Python")

        results_json = ctrl.getSearchResultsJson()
        results = json.loads(results_json)
        self.assertGreater(len(results), 0)

    def test_search_indexed_documents_empty_query(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        ctrl.searchIndexedDocuments("")

        results_json = ctrl.getSearchResultsJson()
        results = json.loads(results_json)
        self.assertEqual(len(results), 0)

    def test_ask_indexed_documents(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        answer_text = None
        ctrl.ragAnswerReady.connect(lambda t: setattr(ctrl, '_answer_captured', t))

        ctrl.askIndexedDocuments("What is Python?")

        answer = ctrl.getLastAnswerText()
        self.assertEqual(answer, "Fake answer from FakeAppService")

    def test_ask_indexed_documents_empty_question(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        error_values = []
        ctrl.errorOccurred.connect(lambda e: error_values.append(e))

        ctrl.askIndexedDocuments("")

        self.assertGreater(len(error_values), 0)

    def test_ask_indexed_documents_returns_citations(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        ctrl.askIndexedDocuments("Question")

        citations_json = ctrl.getLastCitationsJson()
        citations = json.loads(citations_json)
        self.assertGreater(len(citations), 0)
        self.assertEqual(citations[0]["source_id"], "S1")

    def test_ask_indexed_document(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        ctrl.askIndexedDocument("note:note-123", "What is this?")

        answer = ctrl.getLastAnswerText()
        self.assertIn("note:note-123", answer)

    def test_ask_indexed_document_empty_document_id(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        error_values = []
        ctrl.errorOccurred.connect(lambda e: error_values.append(e))

        ctrl.askIndexedDocument("", "Question")

        self.assertGreater(len(error_values), 0)

    def test_clear_index(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()
        fake_svc.index_current_note("note-1", "Test", "Content")

        status_values = []
        ctrl.indexStatusChanged.connect(lambda s: status_values.append(s))

        ctrl.clearIndex()

        self.assertEqual(len(fake_svc._indexed_docs), 0)
        self.assertIn("cleared", status_values)
        self.assertEqual(ctrl.getLastAnswerText(), "")

    def test_clear_index_resets_search_results(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()
        fake_svc.index_current_note("note-1", "Test", "Content")
        ctrl.searchIndexedDocuments("Test")

        ctrl.clearIndex()

        results_json = ctrl.getSearchResultsJson()
        results = json.loads(results_json)
        self.assertEqual(len(results), 0)

    def test_indexing_progress_signal_emitted(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        payloads = []
        ctrl.indexingProgressChanged.connect(lambda payload: payloads.append(payload))

        paths = json.dumps(["/tmp/file1.md", "/tmp/file2.md"])
        ctrl.indexExternalFilesJson(paths)

        self.assertGreater(len(payloads), 0)
        first = json.loads(payloads[0])
        self.assertIn("label", first)
        self.assertIn("current", first)

    def test_get_last_warnings_json(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        warnings_json = ctrl.getLastWarningsJson()
        warnings = json.loads(warnings_json)
        self.assertEqual(warnings, [])

    def test_json_serialization_ensure_ascii_false(self):
        fake_svc = FakeAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        ctrl.askIndexedDocuments("Question")

        citations_json = ctrl.getLastCitationsJson()
        self.assertTrue(len(citations_json) > 0)
        parsed = json.loads(citations_json)
        self.assertIsInstance(parsed, list)

    def test_service_exception_handled(self):
        class FailingAppService:
            def initialize(self):
                pass
            def index_current_note(self, **kwargs):
                raise RuntimeError("Intentional failure")
            def search_index(self, *args, **kwargs):
                raise RuntimeError("Search failed")
            def ask_indexed_documents(self, *args, **kwargs):
                raise RuntimeError("Ask failed")
            def ask_indexed_document(self, *args, **kwargs):
                raise RuntimeError("Ask doc failed")
            def clear_index(self):
                raise RuntimeError("Clear failed")
            def close(self):
                pass

        fake_svc = FailingAppService()
        ctrl = AiRagController(app_service=fake_svc)
        ctrl.initialize()

        error_count = [0]
        ctrl.errorOccurred.connect(lambda e: error_count.__setitem__(0, error_count[0] + 1))

        ctrl.indexCurrentNote("note-1", "Test", "Content")
        self.assertEqual(error_count[0], 1)

        ctrl.searchIndexedDocuments("query")
        self.assertEqual(error_count[0], 2)

        ctrl.askIndexedDocuments("question")
        self.assertEqual(error_count[0], 3)

        ctrl.askIndexedDocument("doc-id", "question")
        self.assertEqual(error_count[0], 4)

        ctrl.clearIndex()
        self.assertEqual(error_count[0], 5)


if __name__ == "__main__":
    unittest.main()
