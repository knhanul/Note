import unittest
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional
from unittest.mock import MagicMock, patch

from services.ai_rag_application_service import AiRagApplicationService, FakeLlmClient
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_service import RagQueryOptions


class TestLlmClient(LlmClient):
    def __init__(self, response_text: str = "Test response", warnings: list[str] = None):
        self.response_text = response_text
        self.warnings = warnings or []
        self.last_options: Optional[LlmGenerateOptions] = None

    def generate(
        self, system_prompt: str, user_prompt: str, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        self.last_options = options
        return LlmGenerateResult(
            text=self.response_text,
            model=options.model if options else "llama3.2:3b",
            provider="test",
            raw={"response": self.response_text},
            warnings=self.warnings,
        )

    def generate_from_payload(
        self, payload, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        return self.generate(payload.system_prompt, payload.user_prompt, options)


class AiRagApplicationServiceTest(unittest.TestCase):
    def test_initialize_and_close(self):
        svc = AiRagApplicationService(db_path=":memory:")
        svc.initialize()
        svc.close()

    def test_initialize_multiple_times(self):
        svc = AiRagApplicationService(db_path=":memory:")
        svc.initialize()
        svc.initialize()
        svc.close()

    def test_index_current_note(self):
        llm = TestLlmClient("답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            result = svc.index_current_note(
                note_id="note-123",
                title="Test Note",
                content="# Test\n\nThis is a test note.",
                tags=["test", "sample"],
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.document_id, "note:note-123")
        finally:
            svc.close()

    def test_search_after_index(self):
        llm = TestLlmClient("답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            svc.index_current_note(
                note_id="note-search",
                title="Search Test",
                content="Python programming language",
            )
            results = svc.search_index("Python")
            self.assertGreater(len(results), 0)
        finally:
            svc.close()

    def test_ask_indexed_documents(self):
        llm = TestLlmClient("Python은 프로그래밍 언어입니다.")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            svc.index_current_note(
                note_id="note-ask",
                title="Python Guide",
                content="# Python\n\nPython은 high-level 프로그래밍 언어입니다.",
            )
            answer = svc.ask_indexed_documents("프로그래밍")
            self.assertEqual(answer.answer_text, "Python은 프로그래밍 언어입니다.")
            self.assertGreater(len(answer.citations), 0)
        finally:
            svc.close()

    def test_ask_indexed_document(self):
        llm = TestLlmClient("답변입니다")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            svc.index_current_note(
                note_id="note-doc",
                title="Doc Title",
                content="Some content here",
            )
            answer = svc.ask_indexed_document("note:note-doc", "content")
            self.assertEqual(answer.answer_text, "답변입니다")
            self.assertTrue(all("note:note-doc" in c.document_id for c in answer.citations))
        finally:
            svc.close()

    def test_get_last_answer(self):
        llm = TestLlmClient("마지막 답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            svc.index_current_note(
                note_id="note-last",
                title="Last Test",
                content="Content here",
            )
            answer = svc.ask_indexed_documents("Content")
            last = svc.get_last_answer()
            self.assertIsNotNone(last)
            self.assertEqual(last.answer_text, answer.answer_text)
        finally:
            svc.close()

    def test_get_citations_for_last_answer(self):
        llm = TestLlmClient("답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            citations = svc.get_citations_for_last_answer()
            self.assertEqual(citations, [])

            svc.index_current_note(
                note_id="note-cite",
                title="Cite Test",
                content="Content",
            )
            svc.ask_indexed_documents("Content")

            citations = svc.get_citations_for_last_answer()
            self.assertGreater(len(citations), 0)
        finally:
            svc.close()

    def test_clear_index(self):
        llm = TestLlmClient("답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            svc.index_current_note(
                note_id="note-clear",
                title="Clear Test",
                content="Content",
            )
            results = svc.search_index("Content")
            self.assertGreater(len(results), 0)

            svc.clear_index()
            results = svc.search_index("Content")
            self.assertEqual(len(results), 0)
        finally:
            svc.close()

    def test_index_markdown_file(self):
        llm = TestLlmClient("답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write("# Test\n\nMarkdown content here")
                f.flush()
                path = f.name

            try:
                result = svc.index_markdown_file(path)
                self.assertIsNotNone(result)
                self.assertTrue(result.document_id.startswith("file:markdown_file:"))
            finally:
                Path(path).unlink()
        finally:
            svc.close()

    def test_index_external_files_supports_text_html_docx(self):
        llm = TestLlmClient("답변")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                txt_path = tmp_path / "notes.txt"
                html_path = tmp_path / "page.html"
                docx_path = tmp_path / "report.docx"
                txt_path.write_text("plain text", encoding="utf-8")
                html_path.write_text("<html><body>body</body></html>", encoding="utf-8")
                docx_path.write_bytes(b"fake-docx")

                def make_doc(document_id: str):
                    return MagicMock(document_id=document_id)

                with patch.object(svc._index_service, "index_text_file", return_value=make_doc("text-id")) as mock_text, \
                     patch.object(svc._index_service, "index_html_file", return_value=make_doc("html-id")) as mock_html, \
                     patch.object(svc._index_service, "index_docx_file", return_value=make_doc("docx-id")) as mock_docx:
                    result = svc.index_external_files([txt_path, html_path, docx_path])

                self.assertEqual(result["indexed_count"], 3)
                self.assertEqual(result["failed_count"], 0)
                self.assertEqual(result["document_ids"], ["text-id", "html-id", "docx-id"])
                mock_text.assert_called_once()
                mock_html.assert_called_once()
                mock_docx.assert_called_once()
        finally:
            svc.close()

    def test_no_real_ollama_call(self):
        llm = TestLlmClient("No network call")
        svc = AiRagApplicationService(db_path=":memory:", llm_client=llm)
        svc.initialize()
        try:
            svc.index_current_note(
                note_id="note-net",
                title="Net Test",
                content="Content",
            )
            answer = svc.ask_indexed_documents("Content")
            self.assertIsNotNone(answer.llm_result)
            self.assertEqual(answer.llm_result.provider, "test")
        finally:
            svc.close()


if __name__ == "__main__":
    unittest.main()
