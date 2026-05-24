import unittest

from services.document_chunk_model import DocumentChunk, IndexedDocument
from services.document_chunker import build_indexed_document, chunk_markdown_document
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


class DocumentChunkerTest(unittest.TestCase):
    def test_build_indexed_document_minimal(self):
        doc = MarkdownDocument(
            metadata=MarkdownMetadata(title="문서 제목", tags=["a", "b"]),
            body_markdown="# 제목\n\n본문",
            source_path="/tmp/sample.md",
            warnings=["w1"],
        )

        indexed = build_indexed_document(
            document=doc,
            document_id="doc-1",
            source_type="markdown_file",
        )

        self.assertIsInstance(indexed, IndexedDocument)
        self.assertEqual(indexed.document_id, "doc-1")
        self.assertEqual(indexed.source_type, "markdown_file")
        self.assertEqual(indexed.title, "문서 제목")
        self.assertEqual(indexed.tags, ["a", "b"])
        self.assertEqual(indexed.source_path, "/tmp/sample.md")
        self.assertEqual(indexed.warnings, ["w1"])
        self.assertTrue(indexed.body_checksum)

    def test_empty_document_returns_no_chunks(self):
        doc = MarkdownDocument(body_markdown="")
        chunks = chunk_markdown_document(
            document=doc,
            document_id="doc-empty",
            source_type="note",
        )
        self.assertEqual(chunks, [])

    def test_heading_path_is_preserved(self):
        body = "# 대제목\n본문 A\n\n## 소제목\n본문 B"
        doc = MarkdownDocument(metadata=MarkdownMetadata(title="테스트"), body_markdown=body)

        chunks = chunk_markdown_document(
            document=doc,
            document_id="doc-heading",
            source_type="note",
            target_size=300,
            min_size=20,
            max_size=500,
        )

        self.assertGreaterEqual(len(chunks), 2)
        self.assertIsInstance(chunks[0], DocumentChunk)
        self.assertIn(["대제목"], [c.heading_path for c in chunks])
        self.assertIn(["대제목", "소제목"], [c.heading_path for c in chunks])

    def test_table_block_is_kept(self):
        body = "# 표\n\n| col1 | col2 |\n| --- | --- |\n| a | b |\n| c | d |"
        doc = MarkdownDocument(body_markdown=body)

        chunks = chunk_markdown_document(
            document=doc,
            document_id="doc-table",
            source_type="hwpx_file",
            target_size=200,
            min_size=20,
            max_size=300,
        )

        self.assertTrue(chunks)
        joined = "\n\n".join(chunk.chunk_text for chunk in chunks)
        self.assertIn("| col1 | col2 |", joined)
        self.assertIn("| --- | --- |", joined)
        self.assertIn("| c | d |", joined)

    def test_list_block_is_kept(self):
        body = "# 목록\n\n- 항목1\n- 항목2\n- 항목3"
        doc = MarkdownDocument(body_markdown=body)

        chunks = chunk_markdown_document(
            document=doc,
            document_id="doc-list",
            source_type="markdown_file",
            target_size=200,
            min_size=20,
            max_size=300,
        )

        self.assertTrue(chunks)
        joined = "\n\n".join(chunk.chunk_text for chunk in chunks)
        self.assertIn("- 항목1", joined)
        self.assertIn("- 항목2", joined)
        self.assertIn("- 항목3", joined)

    def test_long_document_is_split(self):
        long_paragraph = "문장입니다. " * 500
        doc = MarkdownDocument(body_markdown=f"# 긴 문서\n\n{long_paragraph}")

        chunks = chunk_markdown_document(
            document=doc,
            document_id="doc-long",
            source_type="note",
            target_size=700,
            min_size=100,
            max_size=900,
        )

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.chunk_text), 1000)

    def test_source_and_note_fields_are_preserved(self):
        doc = MarkdownDocument(body_markdown="# 제목\n\n본문")

        chunks = chunk_markdown_document(
            document=doc,
            document_id="doc-ref",
            source_type="note",
            source_path="/tmp/note.md",
            note_id="note-123",
        )

        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertEqual(chunk.document_id, "doc-ref")
            self.assertEqual(chunk.source_type, "note")
            self.assertEqual(chunk.source_path, "/tmp/note.md")
            self.assertEqual(chunk.note_id, "note-123")


if __name__ == "__main__":
    unittest.main()
