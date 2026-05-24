import unittest
from dataclasses import dataclass, field
from typing import Any, Optional

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_document_index_service import AiDocumentIndexService
from services.ai_index_database import AiIndexDatabase
from services.ai_search_service import AiSearchService
from services.ai_context_builder import AiContextBuilder
from services.ai_rag_prompt_builder import AiRagPromptBuilder
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ai_rag_service import AiRagService, RagQueryOptions
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


class FakeLlmClient(LlmClient):
    def __init__(self, response_text: str = "Fake LLM response", warnings: list[str] = None):
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
            provider="fake",
            raw={"response": self.response_text},
            warnings=self.warnings,
        )

    def generate_from_payload(
        self, payload, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        return self.generate(payload.system_prompt, payload.user_prompt, options)


class AiRagServiceTest(unittest.TestCase):
    def _make_services(self, llm_client: LlmClient):
        db = AiIndexDatabase(":memory:")
        db.initialize()
        repo = AiDocumentIndexRepository(db)
        index_svc = AiDocumentIndexService(repo)
        search_svc = AiSearchService(repo)
        context_svc = AiContextBuilder(repo)
        prompt_svc = AiRagPromptBuilder()
        rag_svc = AiRagService(search_svc, context_svc, prompt_svc, llm_client)
        return rag_svc, index_svc, db

    def test_answer_question_success(self):
        fake_llm = FakeLlmClient("Python은 프로그래밍 언어입니다.")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Python Guide"),
                body_markdown="# Python\n\nPython은 high-level 프로그래밍 언어입니다.",
            )
            index_svc.index_markdown_document(doc, "doc-1", "note")

            result = rag_svc.answer_question("프로그래밍")

            self.assertEqual(result.answer_text, "Python은 프로그래밍 언어입니다.")
            self.assertGreater(len(result.citations), 0)
            self.assertIsNotNone(result.prompt_payload)
            self.assertIsNotNone(result.llm_result)
        finally:
            db.close()

    def test_answer_question_in_document(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc1 = MarkdownDocument(
                metadata=MarkdownMetadata(title="Doc 1"),
                body_markdown="# Heading\n\nContent A",
            )
            index_svc.index_markdown_document(doc1, "doc-a", "note")

            doc2 = MarkdownDocument(
                metadata=MarkdownMetadata(title="Doc 2"),
                body_markdown="# Heading\n\nContent B",
            )
            index_svc.index_markdown_document(doc2, "doc-b", "note")

            result = rag_svc.answer_question_in_document("doc-a", "Content")

            self.assertEqual(result.answer_text, "답변")
            self.assertTrue(all(c.document_id == "doc-a" for c in result.citations))
        finally:
            db.close()

    def test_empty_question(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            result = rag_svc.answer_question("")

            self.assertEqual(result.answer_text, "")
            self.assertIn("RAG_EMPTY_QUESTION", result.warnings)
            self.assertIsNone(result.llm_result)
        finally:
            db.close()

    def test_no_search_results(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            result = rag_svc.answer_question("nonexistentword12345")

            self.assertEqual(result.answer_text, "")
            self.assertIn("RAG_NO_SEARCH_RESULTS", result.warnings)
            self.assertIsNone(result.llm_result)
        finally:
            db.close()

    def test_llm_warning_propagated(self):
        fake_llm = FakeLlmClient("답변", warnings=["[OLLAMA_TIMEOUT]"])
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-warn", "note")

            result = rag_svc.answer_question("keyword")

            self.assertIn("[OLLAMA_TIMEOUT]", result.warnings)
        finally:
            db.close()

    def test_options_passed_to_llm(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-opt", "note")

            options = RagQueryOptions(model="custom-model", temperature=0.8, timeout_sec=30.0)
            result = rag_svc.answer_question("keyword", options)

            self.assertIsNotNone(fake_llm.last_options)
            self.assertEqual(fake_llm.last_options.model, "custom-model")
            self.assertEqual(fake_llm.last_options.temperature, 0.8)
            self.assertEqual(fake_llm.last_options.timeout_sec, 30.0)
        finally:
            db.close()

    def test_citations_source_linkage(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test Doc"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-link", "note", note_id="note-123")

            result = rag_svc.answer_question("keyword")

            self.assertGreater(len(result.citations), 0)
            src = result.citations[0]
            self.assertEqual(src.document_id, "doc-link")
            self.assertEqual(src.note_id, "note-123")
            self.assertEqual(src.title, "Test Doc")
        finally:
            db.close()

    def test_prompt_contains_context(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nSome content about Python.",
            )
            index_svc.index_markdown_document(doc, "doc-ctx", "note")

            result = rag_svc.answer_question("Python")

            self.assertIsNotNone(result.prompt_payload)
            self.assertIn("Python", result.prompt_payload.user_prompt)
        finally:
            db.close()

    def test_no_real_network(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-net", "note")

            result = rag_svc.answer_question("keyword")

            self.assertEqual(result.answer_text, "답변")
            self.assertIsNotNone(result.llm_result)
            self.assertEqual(result.llm_result.provider, "fake")
        finally:
            db.close()

    def test_citations_use_prompt_source_ids(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-src", "note")

            result = rag_svc.answer_question("keyword")

            self.assertGreater(len(result.citations), 0)
            self.assertTrue(all(hasattr(c, "source_id") for c in result.citations))
            self.assertTrue(all(c.source_id.startswith("S") for c in result.citations))
        finally:
            db.close()

    def test_cited_in_answer_true(self):
        fake_llm = FakeLlmClient("답변 [S1]에 따르면...")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-cite", "note")

            result = rag_svc.answer_question("keyword")

            self.assertGreater(len(result.citations), 0)
            self.assertTrue(any(c.cited_in_answer for c in result.citations))
        finally:
            db.close()

    def test_cited_in_answer_false(self):
        fake_llm = FakeLlmClient("답변입니다")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-nocite", "note")

            result = rag_svc.answer_question("keyword")

            self.assertGreater(len(result.citations), 0)
            self.assertTrue(all(not c.cited_in_answer for c in result.citations))
        finally:
            db.close()

    def test_unknown_citation_warning(self):
        fake_llm = FakeLlmClient("답변 [S99]에 따르면...")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-unknown", "note")

            result = rag_svc.answer_question("keyword")

            self.assertIn("RAG_UNKNOWN_CITATION_ID", result.warnings)
        finally:
            db.close()

    def test_no_search_results_citations_empty(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            result = rag_svc.answer_question("nonexistentword12345")

            self.assertEqual(result.citations, [])
        finally:
            db.close()

    def test_no_context_citations_empty(self):
        fake_llm = FakeLlmClient("답변")
        rag_svc, index_svc, db = self._make_services(fake_llm)
        try:
            result = rag_svc.answer_question("keyword")

            self.assertEqual(result.citations, [])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
