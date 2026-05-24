import unittest

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_document_index_service import AiDocumentIndexService
from services.ai_index_database import AiIndexDatabase
from services.ai_search_service import AiSearchService
from services.ai_context_builder import AiContextBuilder
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


class AiContextBuilderTest(unittest.TestCase):
    def _make_services(self):
        db = AiIndexDatabase(":memory:")
        db.initialize()
        repo = AiDocumentIndexRepository(db)
        index_svc = AiDocumentIndexService(repo)
        search_svc = AiSearchService(repo)
        context_svc = AiContextBuilder(repo)
        return context_svc, search_svc, index_svc, db

    def test_empty_search_results(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            bundle = context_svc.build_context_bundle("test", [])
            self.assertEqual(bundle.items, [])
            self.assertEqual(bundle.sources, [])
            self.assertEqual(bundle.total_chars, 0)
            self.assertIn("CONTEXT_NO_SEARCH_RESULTS", bundle.warnings)
        finally:
            db.close()

    def test_primary_chunk_included(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test Doc"),
                body_markdown="# Heading\n\nThis is a paragraph about Python.",
            )
            index_svc.index_markdown_document(doc, "doc-1", "note")

            results = search_svc.search_keyword("Python")
            bundle = context_svc.build_context_bundle("Python", results)

            self.assertGreater(len(bundle.items), 0)
            self.assertTrue(any(item.is_primary for item in bundle.items))
            self.assertTrue(any("Python" in item.chunk_text for item in bundle.items))
        finally:
            db.close()

    def test_neighbor_chunks_included(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Multi Chunk Doc"),
                body_markdown="# H1\n\nPara 1.\n\n## H2\n\nPara 2 keyword.\n\n## H3\n\nPara 3.",
            )
            index_svc.index_markdown_document(doc, "doc-neigh", "note")

            results = search_svc.search_keyword("keyword")
            bundle = context_svc.build_context_bundle("keyword", results, neighbor_window=1)

            self.assertGreater(len(bundle.items), 1)
        finally:
            db.close()

    def test_neighbor_window_zero(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# H1\n\nPara 1.\n\n## H2\n\nPara 2 keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-zero", "note")

            results = search_svc.search_keyword("keyword")
            bundle = context_svc.build_context_bundle("keyword", results, neighbor_window=0)

            self.assertEqual(len(bundle.items), 1)
            self.assertTrue(bundle.items[0].is_primary)
        finally:
            db.close()

    def test_duplicate_chunks_removed(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# H1\n\nPara 1 keyword.\n\n## H2\n\nPara 2.",
            )
            index_svc.index_markdown_document(doc, "doc-dup", "note")

            results = search_svc.search_keyword("keyword")
            results_dup = results + results

            bundle = context_svc.build_context_bundle("keyword", results_dup, neighbor_window=1)

            chunk_ids = [item.chunk_id for item in bundle.items]
            self.assertEqual(len(chunk_ids), len(set(chunk_ids)))
        finally:
            db.close()

    def test_source_linkage_preserved(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-link", "note", note_id="note-123")

            results = search_svc.search_keyword("keyword")
            bundle = context_svc.build_context_bundle("keyword", results)

            self.assertGreater(len(bundle.sources), 0)
            src = bundle.sources[0]
            self.assertEqual(src.source_type, "note")
            self.assertEqual(src.note_id, "note-123")
            self.assertEqual(src.document_id, "doc-link")
            self.assertEqual(src.title, "Test")
        finally:
            db.close()

    def test_max_chunks_respected(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            for i in range(10):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nContent with keyword {i}.",
                )
                index_svc.index_markdown_document(doc, f"doc-max-{i}", "note")

            results = search_svc.search_keyword("keyword")
            bundle = context_svc.build_context_bundle("keyword", results, max_chunks=3)

            self.assertLessEqual(len(bundle.items), 3)
        finally:
            db.close()

    def test_max_chars_respected(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            long_content = "word " * 2000
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Long Doc"),
                body_markdown=f"# Heading\n\n{long_content}",
            )
            index_svc.index_markdown_document(doc, "doc-chars", "note")

            results = search_svc.search_keyword("word")
            max_c = 3000
            bundle = context_svc.build_context_bundle("word", results, max_chars=max_c)

            self.assertLessEqual(bundle.total_chars, max_c + 10)
        finally:
            db.close()

    def test_multiple_documents(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            for i in range(3):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nContent with keyword {i}.",
                )
                index_svc.index_markdown_document(doc, f"doc-multi-{i}", "note")

            results = search_svc.search_keyword("keyword")
            bundle = context_svc.build_context_bundle("keyword", results)

            doc_ids = {item.document_id for item in bundle.items}
            self.assertGreater(len(doc_ids), 1)
        finally:
            db.close()

    def test_context_ordering(self):
        context_svc, search_svc, index_svc, db = self._make_services()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# H1\n\nPara 1.\n\n## H2\n\nPara 2 keyword.\n\n## H3\n\nPara 3.",
            )
            index_svc.index_markdown_document(doc, "doc-order", "note")

            results = search_svc.search_keyword("keyword")
            bundle = context_svc.build_context_bundle("keyword", results, neighbor_window=1)

            for i in range(len(bundle.items) - 1):
                self.assertLessEqual(
                    (bundle.items[i].document_id, bundle.items[i].chunk_order),
                    (bundle.items[i + 1].document_id, bundle.items[i + 1].chunk_order),
                )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
