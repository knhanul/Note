"""SQLite persistence for AI prompt documents and action bindings."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class PromptRepository:
    """Low-level persistence layer for AI prompt storage."""

    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return dict(row)

    def ensure_schema(self) -> None:
        expected_columns = {
            "ai_prompt_documents": {
                "prompt_doc_id", "title", "description", "content_md", "source_type",
                "readonly", "archived", "variables_json", "content_hash", "created_at", "updated_at"
            },
            "ai_actions": {
                "action_id", "name", "description", "category", "required_variables_json",
                "enabled", "sort_order"
            },
            "ai_action_prompt_bindings": {
                "action_id", "prompt_doc_id", "updated_at"
            },
            "ai_prompt_history": {
                "prompt_doc_id", "content_md"
            },
        }

        def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
            rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            return {row[1] for row in rows}

        schema = """
        CREATE TABLE IF NOT EXISTS ai_prompt_documents (
            prompt_doc_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            content_md TEXT NOT NULL,
            source_type TEXT NOT NULL,
            readonly INTEGER DEFAULT 0,
            archived INTEGER DEFAULT 0,
            variables_json TEXT,
            content_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_actions (
            action_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            required_variables_json TEXT,
            enabled INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ai_action_prompt_bindings (
            action_id TEXT PRIMARY KEY,
            prompt_doc_id TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(action_id) REFERENCES ai_actions(action_id) ON DELETE CASCADE,
            FOREIGN KEY(prompt_doc_id) REFERENCES ai_prompt_documents(prompt_doc_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ai_prompt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_doc_id TEXT NOT NULL,
            content_md TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(prompt_doc_id) REFERENCES ai_prompt_documents(prompt_doc_id) ON DELETE CASCADE
        );
        """

        with self._connect() as conn:
            for table_name, required in expected_columns.items():
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                    (table_name,),
                ).fetchall()
                if rows:
                    current_columns = table_columns(conn, table_name)
                    if not required.issubset(current_columns):
                        legacy_name = f"{table_name}_legacy"
                        conn.execute(f"DROP TABLE IF EXISTS {legacy_name}")
                        conn.execute(f"ALTER TABLE {table_name} RENAME TO {legacy_name}")
            conn.executescript(schema)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_prompt_documents_archived_title ON ai_prompt_documents(archived, title COLLATE NOCASE)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_prompt_history_prompt_doc_id ON ai_prompt_history(prompt_doc_id, created_at DESC)"
            )

    def list_actions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT action_id, name, description, category, required_variables_json,
                       enabled, sort_order
                FROM ai_actions
                ORDER BY sort_order ASC, name COLLATE NOCASE ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_action(self, action_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT action_id, name, description, category, required_variables_json,
                       enabled, sort_order
                FROM ai_actions
                WHERE action_id = ?
                """,
                (action_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def upsert_action(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_actions (
                    action_id, name, description, category, required_variables_json,
                    enabled, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(action_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    category = excluded.category,
                    required_variables_json = excluded.required_variables_json,
                    enabled = excluded.enabled,
                    sort_order = excluded.sort_order
                """,
                (
                    record.get("action_id", ""),
                    record.get("name", ""),
                    record.get("description", ""),
                    record.get("category", ""),
                    record.get("required_variables_json", "[]"),
                    int(bool(record.get("enabled", True))),
                    int(record.get("sort_order", 0)),
                ),
            )

    def list_prompt_documents(self, include_archived: bool = False) -> list[dict[str, Any]]:
        where_clause = "" if include_archived else "WHERE archived = 0"
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT prompt_doc_id, title, description, content_md, source_type,
                       readonly, archived, variables_json, content_hash,
                       created_at, updated_at
                FROM ai_prompt_documents
                {where_clause}
                ORDER BY archived ASC, source_type ASC, title COLLATE NOCASE ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_prompt_document(self, prompt_doc_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT prompt_doc_id, title, description, content_md, source_type,
                       readonly, archived, variables_json, content_hash,
                       created_at, updated_at
                FROM ai_prompt_documents
                WHERE prompt_doc_id = ?
                """,
                (prompt_doc_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def upsert_prompt_document(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_prompt_documents (
                    prompt_doc_id, title, description, content_md, source_type,
                    readonly, archived, variables_json, content_hash,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(prompt_doc_id) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    content_md = excluded.content_md,
                    source_type = excluded.source_type,
                    readonly = excluded.readonly,
                    archived = excluded.archived,
                    variables_json = excluded.variables_json,
                    content_hash = excluded.content_hash,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    record.get("prompt_doc_id", ""),
                    record.get("title", ""),
                    record.get("description", ""),
                    record.get("content_md", ""),
                    record.get("source_type", "user"),
                    int(bool(record.get("readonly", 0))),
                    int(bool(record.get("archived", 0))),
                    record.get("variables_json", "[]"),
                    record.get("content_hash", ""),
                ),
            )

    def archive_prompt_document(self, prompt_doc_id: str, archived: bool = True) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_prompt_documents
                SET archived = ?, updated_at = CURRENT_TIMESTAMP
                WHERE prompt_doc_id = ?
                """,
                (1 if archived else 0, prompt_doc_id),
            )

    def get_binding(self, action_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT b.action_id, b.prompt_doc_id, b.updated_at,
                       d.title AS prompt_title,
                       d.description AS prompt_description,
                       d.source_type AS prompt_source_type,
                       d.readonly AS prompt_readonly,
                       d.archived AS prompt_archived,
                       d.variables_json AS prompt_variables_json,
                       d.content_md AS prompt_content_md,
                       d.content_hash AS prompt_content_hash,
                       d.created_at AS prompt_created_at,
                       d.updated_at AS prompt_updated_at
                FROM ai_action_prompt_bindings b
                LEFT JOIN ai_prompt_documents d ON d.prompt_doc_id = b.prompt_doc_id
                WHERE b.action_id = ?
                """,
                (action_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def set_binding(self, action_id: str, prompt_doc_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_action_prompt_bindings (action_id, prompt_doc_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(action_id) DO UPDATE SET
                    prompt_doc_id = excluded.prompt_doc_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (action_id, prompt_doc_id),
            )

    def reset_binding(self, action_id: str) -> None:
        self.set_binding(action_id, action_id)

    def insert_history(self, prompt_doc_id: str, content_md: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_prompt_history(prompt_doc_id, content_md)
                VALUES (?, ?)
                """,
                (prompt_doc_id, content_md),
            )

    def get_prompt_summary_for_action(self, action_id: str) -> dict[str, Any] | None:
        action = self.get_action(action_id)
        if not action:
            return None

        binding = self.get_binding(action_id)
        prompt_doc_id = binding["prompt_doc_id"] if binding else action_id
        prompt = self.get_prompt_document(prompt_doc_id)

        if prompt is None and prompt_doc_id != action_id:
            prompt = self.get_prompt_document(action_id)
            prompt_doc_id = action_id if prompt else prompt_doc_id

        return {
            "action": action,
            "binding": binding,
            "prompt_doc_id": prompt_doc_id,
            "prompt": prompt,
        }

    def list_action_bindings(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for action in self.list_actions():
            summary = self.get_prompt_summary_for_action(action["action_id"])
            if summary:
                items.append(summary)
        return items
