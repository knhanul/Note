import sqlite3
from pathlib import Path


class AiIndexDatabase:
    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path not in (None, ":memory:") else db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn

        if self._db_path is None:
            self._db_path = Path("ai_index.db")

        if self._db_path == ":memory:":
            conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            path = Path(self._db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(path), check_same_thread=False)

        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        self._conn = conn
        return conn

    def get_connection(self) -> sqlite3.Connection:
        return self.connect()

    def initialize(self) -> None:
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_documents (
                document_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_path TEXT,
                note_id TEXT,
                title TEXT,
                body_checksum TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]',
                warnings_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT,
                indexed_at TEXT,
                index_status TEXT NOT NULL DEFAULT 'indexed'
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_document_chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_order INTEGER NOT NULL,
                heading_path_json TEXT NOT NULL DEFAULT '[]',
                chunk_text TEXT NOT NULL,
                start_offset INTEGER,
                end_offset INTEGER,
                warnings_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(document_id) REFERENCES ai_documents(document_id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_embeddings (
                chunk_id TEXT NOT NULL,
                embedding_model_name TEXT NOT NULL,
                vector_blob_or_json BLOB,
                dimensions INTEGER,
                created_at TEXT,
                updated_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                PRIMARY KEY(chunk_id, embedding_model_name)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_index_jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                scope_type TEXT,
                scope_ref TEXT,
                status TEXT NOT NULL,
                processed_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_document_groups (
                group_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                group_type TEXT NOT NULL DEFAULT 'custom',
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_group_documents (
                group_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                PRIMARY KEY(group_id, document_id),
                FOREIGN KEY(group_id) REFERENCES ai_document_groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY(document_id) REFERENCES ai_documents(document_id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_documents_note_id ON ai_documents(note_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_documents_source_type ON ai_documents(source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_documents_source_path ON ai_documents(source_path)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_document_chunks_document_order ON ai_document_chunks(document_id, chunk_order)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_index_jobs_status ON ai_index_jobs(status)")

        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
