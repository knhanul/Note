import hashlib
from pathlib import Path
from typing import Optional

from services.ai_document_index_repository import AiDocumentIndexRepository
from services.document_chunker import build_indexed_document, chunk_markdown_document
from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


class AiDocumentIndexService:
    def __init__(self, repository: AiDocumentIndexRepository):
        self._repo = repository

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

    def index_hwpx_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        from packages.import_export.hwpx_import_service import import_hwpx_as_markdown_document

        path = Path(file_path).resolve()
        doc = import_hwpx_as_markdown_document(str(path))

        if document_id is None:
            document_id = _make_file_document_id("hwpx_file", path)

        return self.index_markdown_document(
            document=doc,
            document_id=document_id,
            source_type="hwpx_file",
            source_path=str(path),
            note_id=None,
        )

    def index_hwp_file(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
    ) -> "IndexedDocument":
        from packages.import_export.hwp_import_service import convert_hwp_to_markdown_text
        from services.markdown_document_model import MarkdownDocument

        path = Path(file_path).resolve()
        markdown_text, warnings = convert_hwp_to_markdown_text(str(path))

        metadata = MarkdownMetadata(title=path.stem)
        document = MarkdownDocument(
            metadata=metadata,
            body_markdown=markdown_text,
            source_path=str(path),
            warnings=warnings,
        )

        if document_id is None:
            document_id = _make_file_document_id("hwp_file", path)

        return self.index_markdown_document(
            document=document,
            document_id=document_id,
            source_type="hwp_file",
            source_path=str(path),
            note_id=None,
        )


def _make_note_document_id(note_id: str) -> str:
    return f"note:{note_id}"


def _make_file_document_id(source_type: str, file_path: Path) -> str:
    resolved = str(file_path.resolve())
    hash_digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]
    return f"file:{source_type}:{hash_digest}"


from services.document_chunk_model import IndexedDocument
