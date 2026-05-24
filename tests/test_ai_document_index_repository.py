import tempfile
import unittest
from pathlib import Path

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_index_database import AiIndexDatabase
from services.document_chunk_model import DocumentChunk, IndexedDocument


class AiDocumentIndexRepositoryTest(unittest.TestCase):
    def _make_document(
        self,
        document_id: str = "doc-1",
        source_type: str = "note",
        source_path: str | None = None,
        note_id: str | None = None,
    ) -> IndexedDocument:
        return IndexedDocument(
            document_id=document_id,
            source_type=source_type,
            source_path=source_path,
            note_id=note_id,
            title="제목",
            body_checksum="checksum",
            tags=["tag1", "tag2"],
            warnings=["w1"],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        )

    def _make_chunk(self, document_id: str, order: int) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=f"{document_id}:{order}:abc",
            document_id=document_id,
            source_type="note",
            source_path=None,
            note_id="note-1",
            title="제목",
            heading_path=["대제목"],
            chunk_text=f"본문 {order}",
            chunk_order=order,
            start_offset=order * 10,
            end_offset=order * 10 + 5,
            warnings=["cw"],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        )

    def test_database_initialization(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            conn = db.get_connection()
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            names = {row["name"] for row in rows}
            self.assertIn("ai_documents", names)
            self.assertIn("ai_document_chunks", names)
            self.assertIn("ai_embeddings", names)
            self.assertIn("ai_index_jobs", names)
            self.assertIn("ai_document_groups", names)
            self.assertIn("ai_group_documents", names)
        finally:
            db.close()

    def test_upsert_and_get_document(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            doc = self._make_document()
            repo.upsert_document(doc)

            got = repo.get_document("doc-1")
            self.assertIsNotNone(got)
            self.assertEqual(got.document_id, "doc-1")
            self.assertEqual(got.tags, ["tag1", "tag2"])
            self.assertEqual(got.warnings, ["w1"])
        finally:
            db.close()

    def test_replace_chunks(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            repo.upsert_document(self._make_document())

            chunks = [self._make_chunk("doc-1", 0), self._make_chunk("doc-1", 1)]
            repo.replace_chunks("doc-1", chunks)

            got = repo.get_chunks("doc-1")
            self.assertEqual(len(got), 2)
            self.assertEqual([c.chunk_order for c in got], [0, 1])
        finally:
            db.close()

    def test_replace_chunks_overwrites_previous_chunks(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            repo.upsert_document(self._make_document())

            repo.replace_chunks("doc-1", [self._make_chunk("doc-1", 0), self._make_chunk("doc-1", 1)])
            repo.replace_chunks("doc-1", [self._make_chunk("doc-1", 5)])

            got = repo.get_chunks("doc-1")
            self.assertEqual(len(got), 1)
            self.assertEqual(got[0].chunk_order, 5)
        finally:
            db.close()

    def test_delete_document_cascades_chunks(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            repo.upsert_document(self._make_document())
            repo.replace_chunks("doc-1", [self._make_chunk("doc-1", 0)])

            repo.delete_document("doc-1")

            self.assertIsNone(repo.get_document("doc-1"))
            self.assertEqual(repo.get_chunks("doc-1"), [])
        finally:
            db.close()

    def test_list_documents(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            repo.upsert_document(self._make_document(document_id="doc-1"))
            repo.upsert_document(self._make_document(document_id="doc-2"))

            docs = repo.list_documents()
            ids = {d.document_id for d in docs}
            self.assertEqual(ids, {"doc-1", "doc-2"})
        finally:
            db.close()

    def test_clear_all(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            repo.upsert_document(self._make_document())
            repo.replace_chunks("doc-1", [self._make_chunk("doc-1", 0)])

            conn = db.get_connection()
            with conn:
                conn.execute(
                    "INSERT INTO ai_document_groups(group_id, name, group_type) VALUES (?, ?, ?)",
                    ("g1", "그룹", "custom"),
                )
                conn.execute(
                    "INSERT INTO ai_group_documents(group_id, document_id) VALUES (?, ?)",
                    ("g1", "doc-1"),
                )
                conn.execute(
                    "INSERT INTO ai_index_jobs(job_id, job_type, status) VALUES (?, ?, ?)",
                    ("j1", "index", "queued"),
                )
                conn.execute(
                    "INSERT INTO ai_embeddings(chunk_id, embedding_model_name, status) VALUES (?, ?, ?)",
                    ("c1", "model", "pending"),
                )

            repo.clear_all()

            self.assertEqual(repo.list_documents(), [])
            self.assertEqual(repo.get_chunks("doc-1"), [])

            counts = {
                "ai_documents": conn.execute("SELECT COUNT(*) AS c FROM ai_documents").fetchone()["c"],
                "ai_document_chunks": conn.execute("SELECT COUNT(*) AS c FROM ai_document_chunks").fetchone()["c"],
                "ai_document_groups": conn.execute("SELECT COUNT(*) AS c FROM ai_document_groups").fetchone()["c"],
                "ai_group_documents": conn.execute("SELECT COUNT(*) AS c FROM ai_group_documents").fetchone()["c"],
                "ai_index_jobs": conn.execute("SELECT COUNT(*) AS c FROM ai_index_jobs").fetchone()["c"],
                "ai_embeddings": conn.execute("SELECT COUNT(*) AS c FROM ai_embeddings").fetchone()["c"],
            }
            self.assertTrue(all(v == 0 for v in counts.values()))
        finally:
            db.close()

    def test_external_file_document(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            doc = self._make_document(
                document_id="doc-ext",
                source_type="hwpx_file",
                source_path="E:/docs/sample.hwpx",
                note_id=None,
            )
            repo.upsert_document(doc)

            got = repo.get_document("doc-ext")
            self.assertIsNotNone(got)
            self.assertEqual(got.source_type, "hwpx_file")
            self.assertEqual(got.source_path, "E:/docs/sample.hwpx")
            self.assertIsNone(got.note_id)
        finally:
            db.close()

    def test_note_document(self):
        db = AiIndexDatabase(":memory:")
        try:
            db.initialize()
            repo = AiDocumentIndexRepository(db)
            doc = self._make_document(
                document_id="doc-note",
                source_type="note",
                source_path=None,
                note_id="note-abc",
            )
            repo.upsert_document(doc)

            got = repo.get_document("doc-note")
            self.assertIsNotNone(got)
            self.assertEqual(got.source_type, "note")
            self.assertEqual(got.note_id, "note-abc")
        finally:
            db.close()

    def test_db_file_path_with_tmp_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "ai_index.db"
            db = AiIndexDatabase(db_path)
            try:
                db.initialize()
                self.assertTrue(db_path.exists())
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
