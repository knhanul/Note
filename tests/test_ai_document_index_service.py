import tempfile
import unittest
from pathlib import Path

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_index_database import AiIndexDatabase
from services.ai_document_index_service import AiDocumentIndexService
from services.document_chunk_model import IndexedDocument
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


class AiDocumentIndexServiceTest(unittest.TestCase):
    def _make_service(self) -> tuple[AiDocumentIndexService, AiIndexDatabase]:
        db = AiIndexDatabase(":memory:")
        db.initialize()
        repo = AiDocumentIndexRepository(db)
        service = AiDocumentIndexService(repo)
        return service, db

    def test_index_markdown_document(self):
        service, db = self._make_service()
        try:
            doc = MarkdownDocument(
                metadata=MarkdownMetadata(title="제목", tags=["t1"]),
                body_markdown="# Heading\n\nParagraph",
            )
            indexed = service.index_markdown_document(
                document=doc,
                document_id="doc-1",
                source_type="note",
            )

            self.assertIsInstance(indexed, IndexedDocument)
            self.assertEqual(indexed.document_id, "doc-1")
            self.assertEqual(indexed.source_type, "note")

            retrieved = service._repo.get_document("doc-1")
            self.assertIsNotNone(retrieved)

            chunks = service._repo.get_chunks("doc-1")
            self.assertGreater(len(chunks), 0)
        finally:
            db.close()

    def test_index_note_content(self):
        service, db = self._make_service()
        try:
            indexed = service.index_note_content(
                note_id="note-123",
                title="노트 제목",
                content="# 제목\n\n본문",
                tags=["tag1", "tag2"],
            )

            self.assertTrue(indexed.document_id.startswith("note:note-123"))
            self.assertEqual(indexed.source_type, "note")
            self.assertEqual(indexed.note_id, "note-123")
            self.assertEqual(indexed.title, "노트 제목")
            self.assertEqual(indexed.tags, ["tag1", "tag2"])
        finally:
            db.close()

    def test_index_markdown_file(self):
        service, db = self._make_service()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                md_path = Path(tmp) / "test.md"
                md_path.write_text("---\ntitle: Test\n---\n\n# Heading\n\nContent", encoding="utf-8")

                indexed = service.index_markdown_file(md_path)

                self.assertEqual(indexed.source_type, "markdown_file")
                self.assertIn("test.md", indexed.source_path or "")

                chunks = service._repo.get_chunks(indexed.document_id)
                self.assertGreater(len(chunks), 0)
        finally:
            db.close()

    def test_index_hwpx_file(self):
        service, db = self._make_service()
        try:
            from tests.helpers.hwpx_fixture_builder import create_minimal_hwpx

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                hwpx_path = create_minimal_hwpx(tmp_path, "테스트 문단")

                indexed = service.index_hwpx_file(hwpx_path)

                self.assertEqual(indexed.source_type, "hwpx_file")
                self.assertIn("hwpx", indexed.source_path or "")

                chunks = service._repo.get_chunks(indexed.document_id)
                self.assertGreater(len(chunks), 0)
        finally:
            db.close()

    def test_replace_same_document(self):
        service, db = self._make_service()
        try:
            doc1 = MarkdownDocument(
                metadata=MarkdownMetadata(title="V1"),
                body_markdown="# Heading\n\nVersion 1",
            )
            service.index_markdown_document(doc1, "doc-replace", "note")

            doc2 = MarkdownDocument(
                metadata=MarkdownMetadata(title="V2"),
                body_markdown="# Heading\n\nVersion 2",
            )
            indexed = service.index_markdown_document(doc2, "doc-replace", "note")

            self.assertEqual(indexed.title, "V2")

            chunks = service._repo.get_chunks("doc-replace")
            self.assertTrue(any("Version 2" in c.chunk_text for c in chunks))
        finally:
            db.close()

    def test_empty_document(self):
        service, db = self._make_service()
        try:
            doc = MarkdownDocument(body_markdown="")
            indexed = service.index_markdown_document(doc, "doc-empty", "note")

            retrieved = service._repo.get_document("doc-empty")
            self.assertIsNotNone(retrieved)

            chunks = service._repo.get_chunks("doc-empty")
            self.assertEqual(len(chunks), 0)
        finally:
            db.close()

    def test_warnings_preserved(self):
        service, db = self._make_service()
        try:
            doc = MarkdownDocument(
                body_markdown="# Heading",
                warnings=["[TEST] warning message"],
            )
            indexed = service.index_markdown_document(doc, "doc-warn", "note")

            self.assertIn("[TEST] warning message", indexed.warnings)
        finally:
            db.close()

    def test_no_embedding_side_effects(self):
        service, db = self._make_service()
        try:
            doc = MarkdownDocument(body_markdown="# Heading\n\nContent")
            service.index_markdown_document(doc, "doc-no-emb", "note")

            conn = db.get_connection()
            emb_count = conn.execute(
                "SELECT COUNT(*) AS c FROM ai_embeddings"
            ).fetchone()["c"]
            self.assertEqual(emb_count, 0)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
