import hashlib
import logging
from pathlib import Path
from typing import Optional

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.document_chunker import (
    build_indexed_document,
    chunk_markdown_document,
    chunk_structured_document,
    _make_chunk_id,
)
from services.folder_import_service import FolderImportService
from services.hwp_policy import HWP_RAG_FILE_MESSAGE
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata
from services.chroma_vector_store import ChromaVectorStore
from services.ollama_embedding_service import OllamaEmbeddingService


logger = logging.getLogger(__name__)


class AiDocumentIndexService:
    def __init__(
        self,
        repository: AiDocumentIndexRepository,
        embedding_service: OllamaEmbeddingService | None = None,
        vector_store: ChromaVectorStore | None = None,
    ):
        self._repo = repository
        self._embedding = embedding_service
        self._vector_store = vector_store

    def index_markdown_document(
        self,
        document: MarkdownDocument,
        document_id: str,
        source_type: str,
        source_path: Optional[str] = None,
        note_id: Optional[str] = None,
    ) -> "IndexedDocument":
        indexed = build_indexed_document(
            document=document,
            document_id=document_id,
            source_type=source_type,
            source_path=source_path,
            note_id=note_id,
        )
        self._repo.upsert_document(indexed)

        chunks = chunk_markdown_document(
            document=document,
            document_id=document_id,
            source_type=source_type,
            source_path=source_path,
            note_id=note_id,
        )
        self._repo.replace_chunks(document_id, chunks)
        self._index_vectors_for_chunks(document_id, chunks)

        return indexed

    def index_note_content(
        self,
        note_id: str,
        title: Optional[str],
        content: str,
        tags: Optional[list[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> "IndexedDocument":
        document_id = _make_note_document_id(note_id)
        metadata = MarkdownMetadata(
            title=title,
            tags=tags or [],
            created_at=created_at,
            updated_at=updated_at,
        )
        document = MarkdownDocument(
            metadata=metadata,
            body_markdown=content,
        )
        return self.index_markdown_document(
            document=document,
            document_id=document_id,
            source_type="note",
            source_path=None,
            note_id=note_id,
        )

    def index_markdown_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        from packages.import_export.markdown_import_service import load_markdown_document

        path = Path(file_path).resolve()
        doc, _ = load_markdown_document(str(path))

        if document_id is None:
            document_id = _make_file_document_id("markdown_file", path)

        return self.index_markdown_document(
            document=doc,
            document_id=document_id,
            source_type="markdown_file",
            source_path=str(path),
            note_id=None,
        )

    def index_text_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        path = Path(file_path).resolve()
        content = self._read_text_with_fallback(path)

        if document_id is None:
            document_id = _make_file_document_id("text_file", path)

        document = MarkdownDocument(
            metadata=MarkdownMetadata(title=path.stem),
            body_markdown=content,
            source_path=str(path),
        )
        return self.index_markdown_document(
            document=document,
            document_id=document_id,
            source_type="text_file",
            source_path=str(path),
            note_id=None,
        )

    def index_html_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        path = Path(file_path).resolve()
        raw_html = self._read_text_with_fallback(path)
        markdown_text = FolderImportService._html_to_markdown(raw_html)

        if document_id is None:
            document_id = _make_file_document_id("html_file", path)

        document = MarkdownDocument(
            metadata=MarkdownMetadata(title=path.stem),
            body_markdown=markdown_text,
            source_path=str(path),
        )
        return self.index_markdown_document(
            document=document,
            document_id=document_id,
            source_type="html_file",
            source_path=str(path),
            note_id=None,
        )

    def index_docx_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        path = Path(file_path).resolve()
        markdown_text = FolderImportService._docx_to_markdown(path)

        if document_id is None:
            document_id = _make_file_document_id("docx_file", path)

        document = MarkdownDocument(
            metadata=MarkdownMetadata(title=path.stem),
            body_markdown=markdown_text,
            source_path=str(path),
        )
        return self.index_markdown_document(
            document=document,
            document_id=document_id,
            source_type="docx_file",
            source_path=str(path),
            note_id=None,
        )

    def index_hwpx_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        from packages.import_export.hwpx_import_service import import_hwpx_as_markdown_document
        from services.hwpx_structured_preprocessor import preprocess_hwpx_file

        path = Path(file_path).resolve()
        doc = import_hwpx_as_markdown_document(str(path))
        structured_doc = preprocess_hwpx_file(path)

        if document_id is None:
            document_id = _make_file_document_id("hwpx_file", path)

        indexed = build_indexed_document(
            document=doc,
            document_id=document_id,
            source_type="hwpx_file",
            source_path=str(path),
            note_id=None,
        )
        self._repo.upsert_document(indexed)

        chunks = chunk_markdown_document(
            document=doc,
            document_id=document_id,
            source_type="hwpx_file",
            source_path=str(path),
            note_id=None,
        )
        structured_chunks = chunk_structured_document(
            structured_document=structured_doc,
            document_id=document_id,
            source_type="hwpx_file",
            source_path=str(path),
            note_id=None,
        )
        order_offset = len(chunks)
        for sc in structured_chunks:
            sc.chunk_order += order_offset
            sc.chunk_id = _make_chunk_id(document_id, sc.chunk_order, sc.chunk_text)
        combined_chunks = chunks + structured_chunks
        logger.info(
            "[AiDocumentIndexService] HWPX parsing completed: path=%s, total_chunks=%d",
            path,
            len(combined_chunks),
        )
        self._repo.replace_chunks(document_id, combined_chunks)
        self._index_vectors_for_chunks(document_id, combined_chunks)

        return indexed

    def index_hwp_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        path = Path(file_path).resolve()
        logger.warning(
            "[AiDocumentIndexService] index_hwp_file called but HWP support is disabled: path=%s",
            path,
        )
        raise RuntimeError(HWP_RAG_FILE_MESSAGE)

    def index_pdf_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        import fitz  # PyMuPDF

        path = Path(file_path).resolve()
        logger.info(
            "[AiDocumentIndexService] Indexing PDF file: path=%s",
            path,
        )
        doc = fitz.open(str(path))
        page_texts = []
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                page_texts.append(f"[페이지 {page_index}]\n{text}")
        doc.close()
        body = "\n\n".join(page_texts)

        if not body.strip():
            logger.warning(
                "[AiDocumentIndexService] PDF text extraction returned empty: path=%s, pages=%d",
                path,
                len(page_texts),
            )

        if document_id is None:
            document_id = _make_file_document_id("pdf_file", path)

        document = MarkdownDocument(
            metadata=MarkdownMetadata(title=path.stem),
            body_markdown=body,
            source_path=str(path),
        )
        logger.info(
            "[AiDocumentIndexService] PDF indexed: path=%s, document_id=%s, body_len=%d",
            path,
            document_id,
            len(body),
        )
        return self.index_markdown_document(
            document=document,
            document_id=document_id,
            source_type="pdf_file",
            source_path=str(path),
            note_id=None,
        )

    @staticmethod
    def _read_text_with_fallback(path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"):
            try:
                return path.read_text(encoding=encoding)
            except Exception:
                continue
        return ""

    def _index_vectors_for_chunks(self, document_id: str, chunks: list) -> None:
        if not self._embedding or not self._vector_store or not self._vector_store.enabled:
            logger.warning(
                "[AiDocumentIndexService] Vector indexing skipped (vector store disabled or embedding service unavailable): "
                "document_id=%s, has_embedding=%s, has_vector_store=%s, vector_store_enabled=%s",
                document_id,
                self._embedding is not None,
                self._vector_store is not None,
                self._vector_store.enabled if self._vector_store else False,
            )
            return

        if not chunks:
            return

        texts = [(chunk.search_text or chunk.chunk_text or "").strip() for chunk in chunks]
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        try:
            self._vector_store.delete_document_chunks(document_id)
        except Exception as e:
            logger.warning("[AiDocumentIndexService] Failed to delete existing vectors: document_id=%s error=%s", document_id, e)

        try:
            def _log_progress(current: int, total: int) -> None:
                logger.info("[Embedding] Processing chunk %d/%d...", current, total)

            embeddings = self._embedding.embed_texts(
                texts,
                batch_size=16,
                progress_callback=_log_progress,
            )
            metadatas = [
                {
                    "document_id": chunk.document_id,
                    "chunk_order": int(chunk.chunk_order),
                    "source_type": chunk.source_type or "",
                }
                for chunk in chunks
            ]
            upserted = self._vector_store.upsert_chunks(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                texts=texts,
                metadatas=metadatas,
            )
            logger.info("[AiDocumentIndexService] Chroma upserted vectors: document_id=%s chunks=%d upserted=%d", document_id, len(chunks), upserted)
        except Exception as e:
            logger.warning("[AiDocumentIndexService] Vector indexing failed: document_id=%s error=%s", document_id, e)


def _make_note_document_id(note_id: str) -> str:
    return f"note:{note_id}"


def _make_file_document_id(source_type: str, file_path: Path) -> str:
    resolved = str(file_path.resolve())
    hash_digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]
    return f"file:{source_type}:{hash_digest}"


from services.document_chunk_model import IndexedDocument
