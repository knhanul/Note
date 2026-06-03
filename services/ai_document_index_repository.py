import json
from datetime import datetime, timezone

from services.ai_index_database import AiIndexDatabase
from services.document_chunk_model import DocumentChunk, IndexedDocument, IndexedDocumentSummary


class AiDocumentIndexRepository:
    def __init__(self, database: AiIndexDatabase):
        self._db = database

    def upsert_document(self, document: IndexedDocument) -> None:
        conn = self._db.get_connection()
        indexed_at = _utc_now_iso()

        with conn:
            conn.execute(
                """
                INSERT INTO ai_documents (
                    document_id, source_type, source_path, note_id, title,
                    body_checksum, tags_json, warnings_json,
                    created_at, updated_at, indexed_at, index_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    source_type=excluded.source_type,
                    source_path=excluded.source_path,
                    note_id=excluded.note_id,
                    title=excluded.title,
                    body_checksum=excluded.body_checksum,
                    tags_json=excluded.tags_json,
                    warnings_json=excluded.warnings_json,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    indexed_at=excluded.indexed_at,
                    index_status=excluded.index_status
                """,
                (
                    document.document_id,
                    document.source_type,
                    document.source_path,
                    document.note_id,
                    document.title,
                    document.body_checksum,
                    _to_json(document.tags),
                    _to_json(document.warnings),
                    document.created_at,
                    document.updated_at,
                    indexed_at,
                    "indexed",
                ),
            )

    def replace_chunks(self, document_id: str, chunks: list[DocumentChunk]) -> None:
        conn = self._db.get_connection()
        with conn:
            conn.execute("DELETE FROM ai_document_chunks WHERE document_id = ?", (document_id,))

            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO ai_document_chunks (
                        chunk_id, document_id, chunk_order, heading_path_json,
                        chunk_text, start_offset, end_offset, warnings_json,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.chunk_id,
                        document_id,
                        chunk.chunk_order,
                        _to_json(chunk.heading_path),
                        chunk.chunk_text,
                        chunk.start_offset,
                        chunk.end_offset,
                        _to_json(chunk.warnings),
                        chunk.created_at,
                        chunk.updated_at,
                    ),
                )

    def get_document(self, document_id: str) -> IndexedDocument | None:
        conn = self._db.get_connection()
        row = conn.execute(
            """
            SELECT document_id, source_type, source_path, note_id, title,
                   body_checksum, tags_json, warnings_json,
                   created_at, updated_at
            FROM ai_documents
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        return IndexedDocument(
            document_id=row["document_id"],
            source_type=row["source_type"],
            source_path=row["source_path"],
            note_id=row["note_id"],
            title=row["title"],
            body_checksum=row["body_checksum"],
            tags=_from_json_list(row["tags_json"]),
            warnings=_from_json_list(row["warnings_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_documents(self) -> list[IndexedDocument]:
        conn = self._db.get_connection()
        rows = conn.execute(
            """
            SELECT document_id, source_type, source_path, note_id, title,
                   body_checksum, tags_json, warnings_json,
                   created_at, updated_at
            FROM ai_documents
            ORDER BY indexed_at DESC, document_id ASC
            """
        ).fetchall()

        return [
            IndexedDocument(
                document_id=row["document_id"],
                source_type=row["source_type"],
                source_path=row["source_path"],
                note_id=row["note_id"],
                title=row["title"],
                body_checksum=row["body_checksum"],
                tags=_from_json_list(row["tags_json"]),
                warnings=_from_json_list(row["warnings_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def list_document_summaries(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[IndexedDocumentSummary], int]:
        conn = self._db.get_connection()
        total = conn.execute("SELECT COUNT(*) AS cnt FROM ai_documents").fetchone()["cnt"]

        query = (
            """
            SELECT d.document_id, d.source_type, d.source_path, d.note_id, d.title,
                   d.created_at, d.updated_at, d.indexed_at,
                   COUNT(c.chunk_id) AS chunk_count
            FROM ai_documents d
            LEFT JOIN ai_document_chunks c ON c.document_id = d.document_id
            GROUP BY d.document_id, d.source_type, d.source_path, d.note_id, d.title,
                     d.created_at, d.updated_at, d.indexed_at
            ORDER BY d.indexed_at DESC, d.document_id ASC
            LIMIT ? OFFSET ?
            """
            if limit is not None
            else
            """
            SELECT d.document_id, d.source_type, d.source_path, d.note_id, d.title,
                   d.created_at, d.updated_at, d.indexed_at,
                   COUNT(c.chunk_id) AS chunk_count
            FROM ai_documents d
            LEFT JOIN ai_document_chunks c ON c.document_id = d.document_id
            GROUP BY d.document_id, d.source_type, d.source_path, d.note_id, d.title,
                     d.created_at, d.updated_at, d.indexed_at
            ORDER BY d.indexed_at DESC, d.document_id ASC
            OFFSET ?
            """
        )

        params: tuple[int, ...]
        if limit is not None:
            params = (limit, offset)
        else:
            params = (offset,)

        rows = conn.execute(query, params).fetchall()

        summaries = [
            IndexedDocumentSummary(
                document_id=row["document_id"],
                source_type=row["source_type"],
                source_path=row["source_path"],
                note_id=row["note_id"],
                title=row["title"],
                chunk_count=row["chunk_count"] or 0,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

        return summaries, total

    def get_chunks(self, document_id: str) -> list[DocumentChunk]:
        conn = self._db.get_connection()
        rows = conn.execute(
            """
            SELECT chunk_id, document_id, chunk_order, heading_path_json,
                   chunk_text, start_offset, end_offset, warnings_json,
                   created_at, updated_at
            FROM ai_document_chunks
            WHERE document_id = ?
            ORDER BY chunk_order ASC
            """,
            (document_id,),
        ).fetchall()

        document = self.get_document(document_id)
        source_type = document.source_type if document else "unknown"
        source_path = document.source_path if document else None
        note_id = document.note_id if document else None
        title = document.title if document else None

        return [
            DocumentChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                source_type=source_type,
                source_path=source_path,
                note_id=note_id,
                title=title,
                heading_path=_from_json_list(row["heading_path_json"]),
                chunk_text=row["chunk_text"],
                chunk_order=row["chunk_order"],
                start_offset=row["start_offset"],
                end_offset=row["end_offset"],
                warnings=_from_json_list(row["warnings_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def delete_document(self, document_id: str) -> None:
        conn = self._db.get_connection()
        with conn:
            conn.execute("DELETE FROM ai_documents WHERE document_id = ?", (document_id,))

    def clear_all(self) -> None:
        conn = self._db.get_connection()
        with conn:
            conn.execute("DELETE FROM ai_group_documents")
            conn.execute("DELETE FROM ai_document_groups")
            conn.execute("DELETE FROM ai_embeddings")
            conn.execute("DELETE FROM ai_index_jobs")
            conn.execute("DELETE FROM ai_document_chunks")
            conn.execute("DELETE FROM ai_documents")

    def get_chunk_by_id(self, chunk_id: str) -> DocumentChunk | None:
        conn = self._db.get_connection()
        row = conn.execute(
            """
            SELECT c.chunk_id, c.document_id, c.chunk_order, c.heading_path_json,
                   c.chunk_text, c.start_offset, c.end_offset, c.warnings_json,
                   c.created_at, c.updated_at,
                   d.source_type, d.source_path, d.note_id, d.title
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE c.chunk_id = ?
            """,
            (chunk_id,),
        ).fetchone()

        if row is None:
            return None

        return DocumentChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            source_type=row["source_type"],
            source_path=row["source_path"],
            note_id=row["note_id"],
            title=row["title"],
            heading_path=_from_json_list(row["heading_path_json"]),
            chunk_text=row["chunk_text"],
            chunk_order=row["chunk_order"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            warnings=_from_json_list(row["warnings_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_neighbor_chunks(
        self, document_id: str, chunk_order: int, window: int = 1
    ) -> list[DocumentChunk]:
        conn = self._db.get_connection()
        rows = conn.execute(
            """
            SELECT c.chunk_id, c.document_id, c.chunk_order, c.heading_path_json,
                   c.chunk_text, c.start_offset, c.end_offset, c.warnings_json,
                   c.created_at, c.updated_at,
                   d.source_type, d.source_path, d.note_id, d.title
            FROM ai_document_chunks c
            JOIN ai_documents d ON c.document_id = d.document_id
            WHERE c.document_id = ?
              AND c.chunk_order BETWEEN ? AND ?
            ORDER BY c.chunk_order ASC
            """,
            (document_id, chunk_order - window, chunk_order + window),
        ).fetchall()

        return [
            DocumentChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                source_type=row["source_type"],
                source_path=row["source_path"],
                note_id=row["note_id"],
                title=row["title"],
                heading_path=_from_json_list(row["heading_path_json"]),
                chunk_text=row["chunk_text"],
                chunk_order=row["chunk_order"],
                start_offset=row["start_offset"],
                end_offset=row["end_offset"],
                warnings=_from_json_list(row["warnings_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]


def _to_json(value: list | dict) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
