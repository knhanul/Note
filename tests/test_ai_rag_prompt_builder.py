import unittest

from services.ai_context_builder import ContextBundle, ContextItem, ContextSource
from services.ai_rag_prompt_builder import AiRagPromptBuilder, RagPromptPayload


class AiRagPromptBuilderTest(unittest.TestCase):
    def _make_builder(self):
        return AiRagPromptBuilder()

    def _make_context_item(self, chunk_id, document_id, title, chunk_text, is_primary=False):
        source = ContextSource(
            chunk_id=chunk_id,
            document_id=document_id,
            title=title,
            source_type="note",
            source_path=None,
            note_id="note-123",
            heading_path=["Heading 1", "Heading 2"],
            chunk_order=1,
            score=1.0,
        )
        return ContextItem(
            chunk_id=chunk_id,
            document_id=document_id,
            heading_path=["Heading 1", "Heading 2"],
            chunk_text=chunk_text,
            chunk_order=1,
            is_primary=is_primary,
            source=source,
        )

    def test_build_prompt_basic(self):
        builder = self._make_builder()
        item = self._make_context_item("c1", "doc1", "Test Doc", "Content here.")
        bundle = ContextBundle(
            query="test",
            items=[item],
            sources=[],
            warnings=[],
            total_chars=100,
        )

        payload = builder.build_prompt("What is this?", bundle)

        self.assertIsInstance(payload, RagPromptPayload)
        self.assertTrue(len(payload.system_prompt) > 0)
        self.assertTrue(len(payload.user_prompt) > 0)
        self.assertTrue(len(payload.context_text) > 0)

    def test_source_blocks_created(self):
        builder = self._make_builder()
        item1 = self._make_context_item("c1", "doc1", "Doc 1", "First content.")
        item2 = self._make_context_item("c2", "doc2", "Doc 2", "Second content.")
        bundle = ContextBundle(
            query="test",
            items=[item1, item2],
            sources=[],
            warnings=[],
            total_chars=100,
        )

        payload = builder.build_prompt("What is this?", bundle)

        self.assertIn("[Source 1]", payload.context_text)
        self.assertIn("[Source 2]", payload.context_text)

    def test_source_linkage_preserved(self):
        builder = self._make_builder()
        item = self._make_context_item("c1", "doc1", "Test Doc", "Content here.")
        bundle = ContextBundle(
            query="test",
            items=[item],
            sources=[],
            warnings=[],
            total_chars=100,
        )

        payload = builder.build_prompt("What is this?", bundle)

        self.assertEqual(len(payload.sources), 1)
        src = payload.sources[0]
        self.assertEqual(src.chunk_id, "c1")
        self.assertEqual(src.document_id, "doc1")
        self.assertEqual(src.note_id, "note-123")
        self.assertEqual(src.title, "Test Doc")

    def test_question_included(self):
        builder = self._make_builder()
        item = self._make_context_item("c1", "doc1", "Test", "Content.")
        bundle = ContextBundle(query="test", items=[item], sources=[], warnings=[], total_chars=50)

        payload = builder.build_prompt("What is Python?", bundle)

        self.assertIn("What is Python?", payload.user_prompt)

    def test_context_included(self):
        builder = self._make_builder()
        item = self._make_context_item("c1", "doc1", "Test", "This is Python content.")
        bundle = ContextBundle(query="test", items=[item], sources=[], warnings=[], total_chars=50)

        payload = builder.build_prompt("What is this?", bundle)

        self.assertIn("This is Python content.", payload.context_text)

    def test_max_context_chars_respected(self):
        builder = self._make_builder()
        long_content = "word " * 2000
        item = self._make_context_item("c1", "doc1", "Test", long_content)
        bundle = ContextBundle(query="test", items=[item], sources=[], warnings=[], total_chars=10000)

        payload = builder.build_prompt("What is this?", bundle, max_context_chars=3000)

        self.assertLessEqual(len(payload.context_text), 3100)
        has_warning = any(
            w in ["RAG_CONTEXT_TRUNCATED", "RAG_SOURCE_TRUNCATED"] for w in payload.warnings
        )
        self.assertTrue(has_warning)

    def test_duplicate_source_removed(self):
        builder = self._make_builder()
        item1 = self._make_context_item("c1", "doc1", "Test", "Content 1.")
        item2 = self._make_context_item("c1", "doc1", "Test", "Content 1.")
        bundle = ContextBundle(
            query="test", items=[item1, item2], sources=[], warnings=[], total_chars=100
        )

        payload = builder.build_prompt("What is this?", bundle)

        self.assertEqual(len(payload.sources), 1)
        self.assertIn("RAG_DUPLICATE_SOURCE_REMOVED", payload.warnings)

    def test_empty_context_bundle(self):
        builder = self._make_builder()
        bundle = ContextBundle(query="test", items=[], sources=[], warnings=[], total_chars=0)

        payload = builder.build_prompt("What is this?", bundle)

        self.assertIsInstance(payload, RagPromptPayload)
        self.assertIn("RAG_NO_CONTEXT", payload.warnings)

    def test_korean_system_prompt(self):
        builder = self._make_builder()
        item = self._make_context_item("c1", "doc1", "Test", "Content.")
        bundle = ContextBundle(query="test", items=[item], sources=[], warnings=[], total_chars=50)

        payload = builder.build_prompt("What is this?", bundle, language="ko")

        self.assertIn("제공된 문서", payload.system_prompt)
        self.assertIn("근거로 답변", payload.system_prompt)

    def test_no_llm_call(self):
        builder = self._make_builder()
        item = self._make_context_item("c1", "doc1", "Test", "Content.")
        bundle = ContextBundle(query="test", items=[item], sources=[], warnings=[], total_chars=50)

        payload = builder.build_prompt("What is this?", bundle)

        self.assertFalse(hasattr(payload, "response"))
        self.assertFalse(hasattr(payload, "llm_response"))
        self.assertFalse(hasattr(payload, "answer"))


if __name__ == "__main__":
    unittest.main()
