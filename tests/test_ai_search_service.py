import unittest

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_document_index_service import AiDocumentIndexService
from services.ai_index_database import AiIndexDatabase
from services.ai_search_service import AiSearchService
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


class AiSearchServiceTest(unittest.TestCase):
    def _make_service(self):
        db = AiIndexDatabase(":memory:")
        db.initialize()
        repo = AiDocumentIndexRepository(db)
        index_svc = AiDocumentIndexService(repo)
        search_svc = AiSearchService(repo)
        return search_svc, index_svc, db

    def test_empty_query(self):
        search_svc, index_svc, db = self._make_service()
        try:
            result = search_svc.search_keyword("")
            self.assertEqual(result, [])

            result = search_svc.search_keyword("   ")
            self.assertEqual(result, [])
        finally:
            db.close()

    def test_search_chunk_text(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test Doc"),
                body_markdown="# Heading\n\nThis is a paragraph about Python programming.",
            )
            index_svc.index_markdown_document(doc, "doc-1", "note")

            results = search_svc.search_keyword("Python")
            self.assertGreater(len(results), 0)
            self.assertTrue(any("Python" in r.chunk_text for r in results))
        finally:
            db.close()

    def test_search_title(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Unique Title Here"),
                body_markdown="# Heading\n\nSome content.",
            )
            index_svc.index_markdown_document(doc, "doc-2", "note")

            results = search_svc.search_keyword("Unique")
            self.assertGreater(len(results), 0)
            self.assertEqual(results[0].title, "Unique Title Here")
        finally:
            db.close()

    def test_search_heading_path(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Doc"),
                body_markdown="# Main Heading\n\n## Sub Section\n\nContent here.",
            )
            index_svc.index_markdown_document(doc, "doc-3", "note")

            results = search_svc.search_keyword("Sub")
            self.assertGreater(len(results), 0)
            self.assertTrue(any("Sub Section" in r.heading_path for r in results))
        finally:
            db.close()

    def test_limit_respected(self):
        search_svc, index_svc, db = self._make_service()
        try:
            for i in range(10):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nContent {i} keyword.",
                )
                index_svc.index_markdown_document(doc, f"doc-{i}", "note")

            results = search_svc.search_keyword("keyword", limit=3)
            self.assertLessEqual(len(results), 3)
        finally:
            db.close()

    def test_source_linkage_preserved(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent",
            )
            index_svc.index_markdown_document(doc, "doc-link", "note", note_id="note-123")

            results = search_svc.search_keyword("Content")
            self.assertGreater(len(results), 0)
            r = results[0]
            self.assertEqual(r.document_id, "doc-link")
            self.assertEqual(r.source_type, "note")
            self.assertEqual(r.note_id, "note-123")
            self.assertEqual(r.title, "Test")
        finally:
            db.close()

    def test_score_ordering(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc_title = MarkdownDocument(
                metadata=MarkdownMetadata(title="Python Guide"),
                body_markdown="# Heading\n\nSome content.",
            )
            index_svc.index_markdown_document(doc_title, "doc-title", "note")

            doc_body = MarkdownDocument(
                metadata=MarkdownMetadata(title="Other Doc"),
                body_markdown="# Heading\n\nThis mentions Python in the body.",
            )
            index_svc.index_markdown_document(doc_body, "doc-body", "note")

            results = search_svc.search_keyword("Python")
            self.assertGreater(len(results), 0)
            self.assertEqual(results[0].document_id, "doc-title")
            self.assertEqual(results[0].score, 5.0)
        finally:
            db.close()

    def test_search_by_document(self):
        search_svc, index_svc, db = self._make_service()
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

            results = search_svc.search_by_document("doc-a", "Content")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].document_id, "doc-a")
        finally:
            db.close()

    def test_no_result(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nSome content.",
            )
            index_svc.index_markdown_document(doc, "doc-x", "note")

            results = search_svc.search_keyword("nonexistentword12345")
            self.assertEqual(results, [])
        finally:
            db.close()

    def test_multiple_documents(self):
        search_svc, index_svc, db = self._make_service()
        try:
            for i in range(3):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nShared keyword content {i}.",
                )
                index_svc.index_markdown_document(doc, f"doc-multi-{i}", "note")

            results = search_svc.search_keyword("keyword")
            self.assertGreaterEqual(len(results), 2)
            doc_ids = {r.document_id for r in results}
            self.assertGreater(len(doc_ids), 1)
        finally:
            db.close()

    def test_pagination_offset_limit(self):
        search_svc, index_svc, db = self._make_service()
        try:
            for i in range(5):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nContent with keyword {i}.",
                )
                index_svc.index_markdown_document(doc, f"doc-pag-{i}", "note")

            results_0 = search_svc.search_keyword("keyword", limit=2, offset=0)
            results_2 = search_svc.search_keyword("keyword", limit=2, offset=2)

            self.assertEqual(len(results_0), 2)
            self.assertEqual(len(results_2), 2)
            ids_0 = {r.document_id for r in results_0}
            ids_2 = {r.document_id for r in results_2}
            self.assertEqual(ids_0 & ids_2, set())
        finally:
            db.close()

    def test_limit_max_clamp(self):
        search_svc, index_svc, db = self._make_service()
        try:
            for i in range(3):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nKeyword content.",
                )
                index_svc.index_markdown_document(doc, f"doc-max-{i}", "note")

            results = search_svc.search_keyword("keyword", limit=500)
            self.assertLessEqual(len(results), 100)
        finally:
            db.close()

    def test_negative_offset(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-neg", "note")

            results = search_svc.search_keyword("keyword", limit=10, offset=-5)
            self.assertGreater(len(results), 0)
        finally:
            db.close()

    def test_count_keyword(self):
        search_svc, index_svc, db = self._make_service()
        try:
            for i in range(3):
                doc = MarkdownDocument(
                    metadata=MarkdownMetadata(title=f"Doc {i}"),
                    body_markdown=f"# Heading\n\nContent with keyword {i}.",
                )
                index_svc.index_markdown_document(doc, f"doc-count-{i}", "note")

            count = search_svc.count_keyword("keyword")
            self.assertEqual(count, 3)
        finally:
            db.close()

    def test_count_by_document(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nContent with keyword one two three.",
            )
            index_svc.index_markdown_document(doc, "doc-cnt", "note")

            count = search_svc.count_by_document("doc-cnt", "keyword")
            self.assertEqual(count, 1)
        finally:
            db.close()

    def test_snippet_contains_query_context(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test"),
                body_markdown="# Heading\n\nThis is some context before the keyword and some context after it.",
            )
            index_svc.index_markdown_document(doc, "doc-snippet", "note")

            results = search_svc.search_keyword("keyword")
            self.assertGreater(len(results), 0)
            self.assertIsNotNone(results[0].snippet)
            self.assertIn("keyword", results[0].snippet.lower())
        finally:
            db.close()

    def test_title_only_match_snippet_fallback(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Python Guide"),
                body_markdown="# Heading\n\nSome content without the keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-title-only", "note")

            results = search_svc.search_keyword("Python")
            self.assertGreater(len(results), 0)
            self.assertIsNotNone(results[0].snippet)
        finally:
            db.close()

    def test_wildcard_query_safe(self):
        search_svc, index_svc, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="Test%Doc"),
                body_markdown="# Heading\n\nContent with 100% keyword.",
            )
            index_svc.index_markdown_document(doc, "doc-wild", "note")

            results = search_svc.search_keyword("100%")
            self.assertGreaterEqual(len(results), 0)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
