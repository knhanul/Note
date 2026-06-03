"""SQLite persistence for AI prompt documents and action bindings."""

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_ACTION_IDS = frozenset({
    "summarize_note",
    "polish_selection",
    "extract_todo",
    "suggest_title_tags",
    "current_note_qa",
})


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

    @staticmethod
    def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}

    def ensure_schema(self) -> None:
        # Backup safety: create backup before migration
        self._create_backup_if_needed()

        expected_columns = {
            "ai_prompt_documents": {
                "prompt_doc_id", "title", "description", "content_md", "source_type",
                "readonly", "archived", "variables_json", "content_hash", "created_at", "updated_at"
            },
            "ai_actions": {
                "action_id", "name", "description", "category", "required_variables_json",
                "enabled", "sort_order", "source_type", "readonly", "archived",
                "input_mode", "use_rag", "response_length", "icon", "created_at", "updated_at"
            },
            "ai_action_prompt_bindings": {
                "action_id", "prompt_doc_id", "updated_at"
            },
            "ai_prompt_history": {
                "prompt_doc_id", "content_md"
            },
        }


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
            sort_order INTEGER DEFAULT 0,
            source_type TEXT DEFAULT 'default',
            readonly INTEGER DEFAULT 0,
            archived INTEGER DEFAULT 0,
            input_mode TEXT DEFAULT 'auto',
            use_rag INTEGER DEFAULT 0,
            response_length TEXT DEFAULT 'medium',
            icon TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            # Create tables if not exist (additive only, no drop/rename)
            conn.executescript(schema)

            # Additive migration for ai_actions - add missing columns
            current_action_cols = self._table_columns(conn, "ai_actions")
            new_action_columns = {
                "source_type": "TEXT DEFAULT 'default'",
                "readonly": "INTEGER DEFAULT 0",
                "archived": "INTEGER DEFAULT 0",
                "input_mode": "TEXT DEFAULT 'auto'",
                "use_rag": "INTEGER DEFAULT 0",
                "response_length": "TEXT DEFAULT 'medium'",
                "icon": "TEXT DEFAULT ''",
            }
            for col_name, col_def in new_action_columns.items():
                if col_name not in current_action_cols:
                    try:
                        conn.execute(f"ALTER TABLE ai_actions ADD COLUMN {col_name} {col_def}")
                        logger.info(f"[PromptRepository] Added column {col_name} to ai_actions")
                    except sqlite3.Error as e:
                        logger.warning(f"[PromptRepository] Failed to add column {col_name}: {e}")

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_prompt_documents_archived_title ON ai_prompt_documents(archived, title COLLATE NOCASE)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_prompt_history_prompt_doc_id ON ai_prompt_history(prompt_doc_id, created_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_actions_archived_enabled ON ai_actions(archived, enabled)"
            )

            # Correct default actions
            self._correct_default_actions(conn)

    def _create_backup_if_needed(self) -> None:
        """Create backup before migration if it doesn't exist."""
        if not self._db_path.exists():
            return
        backup_path = self._db_path.with_suffix(".db.backup")
        if not backup_path.exists():
            try:
                shutil.copy2(self._db_path, backup_path)
                logger.info(f"[PromptRepository] Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"[PromptRepository] Failed to create backup: {e}")

    def _correct_default_actions(self, conn: sqlite3.Connection) -> None:
        """Correct default actions with new columns."""
        current_action_cols = self._table_columns(conn, "ai_actions")
        now = datetime.now().isoformat()
        for action_id in DEFAULT_ACTION_IDS:
            use_rag = 1 if action_id == "current_note_qa" else 0
            
            # Build SET clause dynamically based on existing columns
            set_clauses = [
                "source_type = 'default'",
                "readonly = 1",
                "archived = 0",
                "input_mode = 'auto'",
                f"use_rag = {use_rag}",
                "response_length = 'medium'",
            ]
            
            # Only add updated_at if column exists
            if "updated_at" in current_action_cols:
                set_clauses.append(f"updated_at = '{now}'")
            
            set_clause = ", ".join(set_clauses)
            
            conn.execute(
                f"""
                UPDATE ai_actions
                SET {set_clause}
                WHERE action_id = ?
                """,
                (action_id,),
            )
        logger.info("[PromptRepository] Corrected default actions")

    def list_actions(self, include_archived: bool = False, enabled_only: bool = False) -> list[dict[str, Any]]:
        conditions = []
        if not include_archived:
            conditions.append("archived = 0")
        if enabled_only:
            conditions.append("enabled = 1")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self._connect() as conn:
            # Get actual columns to handle missing timestamp columns in old DB
            cols = self._table_columns(conn, "ai_actions")
            select_cols = ["action_id", "name", "description", "category", "required_variables_json",
                          "enabled", "sort_order"]
            for col in ["source_type", "readonly", "archived", "input_mode", "use_rag", "response_length", "icon", "created_at", "updated_at"]:
                if col in cols:
                    select_cols.append(col)
            
            rows = conn.execute(
                f"""
                SELECT {', '.join(select_cols)}
                FROM ai_actions
                {where_clause}
                ORDER BY sort_order ASC, name COLLATE NOCASE ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_action(self, action_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            # Get actual columns to handle missing timestamp columns in old DB
            cols = self._table_columns(conn, "ai_actions")
            select_cols = ["action_id", "name", "description", "category", "required_variables_json",
                          "enabled", "sort_order"]
            for col in ["source_type", "readonly", "archived", "input_mode", "use_rag", "response_length", "icon", "created_at", "updated_at"]:
                if col in cols:
                    select_cols.append(col)
            
            row = conn.execute(
                f"""
                SELECT {', '.join(select_cols)}
                FROM ai_actions
                WHERE action_id = ?
                """,
                (action_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def action_exists(self, action_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM ai_actions WHERE action_id = ?", (action_id,)).fetchone()
            return row is not None

    def create_action(self, record: dict[str, Any]) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO ai_actions (
                        action_id, name, description, category, required_variables_json,
                        enabled, sort_order, source_type, readonly, archived, input_mode, use_rag, response_length, icon
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.get("action_id", ""),
                        record.get("name", ""),
                        record.get("description", ""),
                        record.get("category", ""),
                        record.get("required_variables_json", "[]"),
                        int(bool(record.get("enabled", True))),
                        int(record.get("sort_order", 0)),
                        record.get("source_type", "user"),
                        int(record.get("readonly", 0)),
                        int(record.get("archived", 0)),
                        record.get("input_mode", "auto"),
                        int(record.get("use_rag", 0)),
                        record.get("response_length", "medium"),
                        record.get("icon", ""),
                    ),
                )
                return True
            except sqlite3.Error as e:
                logger.error(f"[PromptRepository] Failed to create action: {e}")
                return False

    def update_action(self, action_id: str, record: dict[str, Any]) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    UPDATE ai_actions SET
                        name = excluded.name,
                        description = excluded.description,
                        category = excluded.category,
                        required_variables_json = excluded.required_variables_json,
                        enabled = excluded.enabled,
                        sort_order = excluded.sort_order,
                        source_type = excluded.source_type,
                        readonly = excluded.readonly,
                        archived = excluded.archived,
                        input_mode = excluded.input_mode,
                        use_rag = excluded.use_rag,
                        response_length = excluded.response_length,
                        icon = excluded.icon,
                        updated_at = CURRENT_TIMESTAMP
                    FROM (SELECT ? AS action_id, ? AS name, ? AS description, ? AS category,
                                 ? AS required_variables_json, ? AS enabled, ? AS sort_order,
                                 ? AS source_type, ? AS readonly, ? AS archived,
                                 ? AS input_mode, ? AS use_rag, ? AS response_length, ? AS icon) AS excluded
                    WHERE ai_actions.action_id = excluded.action_id
                    """,
                    (
                        action_id,
                        record.get("name", ""),
                        record.get("description", ""),
                        record.get("category", ""),
                        record.get("required_variables_json", "[]"),
                        int(bool(record.get("enabled", True))),
                        int(record.get("sort_order", 0)),
                        record.get("source_type", "user"),
                        int(record.get("readonly", 0)),
                        int(record.get("archived", 0)),
                        record.get("input_mode", "auto"),
                        int(record.get("use_rag", 0)),
                        record.get("response_length", "medium"),
                        record.get("icon", ""),
                    ),
                )
                return True
            except sqlite3.Error as e:
                logger.error(f"[PromptRepository] Failed to update action: {e}")
                return False

    def archive_action(self, action_id: str, archived: bool = True) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    "UPDATE ai_actions SET archived = ?, updated_at = CURRENT_TIMESTAMP WHERE action_id = ?",
                    (1 if archived else 0, action_id),
                )
                return True
            except sqlite3.Error as e:
                logger.error(f"[PromptRepository] Failed to archive action: {e}")
                return False

    def set_action_enabled(self, action_id: str, enabled: bool) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    "UPDATE ai_actions SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE action_id = ?",
                    (1 if enabled else 0, action_id),
                )
                return True
            except sqlite3.Error as e:
                logger.error(f"[PromptRepository] Failed to set action enabled: {e}")
                return False

    def get_next_sort_order(self, step: int = 10) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT MAX(sort_order) as max_order FROM ai_actions").fetchone()
            max_order = row["max_order"] if row and row["max_order"] is not None else 0
            return max_order + step

    def swap_action_sort_order(self, action_id_a: str, action_id_b: str) -> bool:
        with self._connect() as conn:
            try:
                action_a = conn.execute("SELECT sort_order FROM ai_actions WHERE action_id = ?", (action_id_a,)).fetchone()
                action_b = conn.execute("SELECT sort_order FROM ai_actions WHERE action_id = ?", (action_id_b,)).fetchone()
                if not action_a or not action_b:
                    return False
                sort_a = action_a["sort_order"]
                sort_b = action_b["sort_order"]
                conn.execute("UPDATE ai_actions SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE action_id = ?", (sort_b, action_id_a))
                conn.execute("UPDATE ai_actions SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE action_id = ?", (sort_a, action_id_b))
                return True
            except sqlite3.Error as e:
                logger.error(f"[PromptRepository] Failed to swap sort order: {e}")
                return False

    def move_action_up(self, action_id: str) -> bool:
        with self._connect() as conn:
            action = conn.execute("SELECT sort_order FROM ai_actions WHERE action_id = ?", (action_id,)).fetchone()
            if not action:
                return False
            current_order = action["sort_order"]
            prev_action = conn.execute(
                "SELECT action_id FROM ai_actions WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1",
                (current_order,)
            ).fetchone()
            if not prev_action:
                return False
            return self.swap_action_sort_order(action_id, prev_action["action_id"])

    def move_action_down(self, action_id: str) -> bool:
        with self._connect() as conn:
            action = conn.execute("SELECT sort_order FROM ai_actions WHERE action_id = ?", (action_id,)).fetchone()
            if not action:
                return False
            current_order = action["sort_order"]
            next_action = conn.execute(
                "SELECT action_id FROM ai_actions WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1",
                (current_order,)
            ).fetchone()
            if not next_action:
                return False
            return self.swap_action_sort_order(action_id, next_action["action_id"])

    def upsert_action(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT source_type, readonly, archived, input_mode, use_rag, response_length, icon FROM ai_actions WHERE action_id = ?",
                (record.get("action_id", ""),)
            ).fetchone()

            source_type = record.get("source_type") or (existing["source_type"] if existing else "default")
            readonly = record.get("readonly") if record.get("readonly") is not None else (existing["readonly"] if existing else 0)
            archived = record.get("archived") if record.get("archived") is not None else (existing["archived"] if existing else 0)
            input_mode = record.get("input_mode") or (existing["input_mode"] if existing else "auto")
            use_rag = record.get("use_rag") if record.get("use_rag") is not None else (existing["use_rag"] if existing else 0)
            response_length = record.get("response_length") or (existing["response_length"] if existing else "medium")
            icon = record.get("icon") or (existing["icon"] if existing else "")

            conn.execute(
                """
                INSERT INTO ai_actions (
                    action_id, name, description, category, required_variables_json,
                    enabled, sort_order, source_type, readonly, archived, input_mode, use_rag, response_length, icon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(action_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    category = excluded.category,
                    required_variables_json = excluded.required_variables_json,
                    enabled = excluded.enabled,
                    sort_order = excluded.sort_order,
                    source_type = COALESCE(NULLIF(excluded.source_type, ''), ai_actions.source_type),
                    readonly = COALESCE(excluded.readonly, ai_actions.readonly),
                    archived = COALESCE(excluded.archived, ai_actions.archived),
                    input_mode = COALESCE(NULLIF(excluded.input_mode, ''), ai_actions.input_mode),
                    use_rag = COALESCE(excluded.use_rag, ai_actions.use_rag),
                    response_length = COALESCE(NULLIF(excluded.response_length, ''), ai_actions.response_length),
                    icon = COALESCE(NULLIF(excluded.icon, ''), ai_actions.icon)
                """,
                (
                    record.get("action_id", ""),
                    record.get("name", ""),
                    record.get("description", ""),
                    record.get("category", ""),
                    record.get("required_variables_json", "[]"),
                    int(bool(record.get("enabled", True))),
                    int(record.get("sort_order", 0)),
                    source_type,
                    int(readonly),
                    int(archived),
                    input_mode,
                    int(use_rag),
                    response_length,
                    icon,
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

    def delete_prompt_document(self, prompt_doc_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM ai_prompt_documents WHERE prompt_doc_id = ?", (prompt_doc_id,))
            conn.execute("DELETE FROM ai_action_prompt_bindings WHERE prompt_doc_id = ?", (prompt_doc_id,))

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

    def clear_binding(self, action_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM ai_action_prompt_bindings WHERE action_id = ?", (action_id,))

    def count_bindings_for_prompt(self, prompt_doc_id: str, include_archived_actions: bool = False) -> int:
        with self._connect() as conn:
            if include_archived_actions:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM ai_action_prompt_bindings WHERE prompt_doc_id = ?",
                    (prompt_doc_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT COUNT(*) as cnt FROM ai_action_prompt_bindings b
                    JOIN ai_actions a ON a.action_id = b.action_id
                    WHERE b.prompt_doc_id = ? AND a.archived = 0
                    """,
                    (prompt_doc_id,),
                ).fetchone()
            return row["cnt"] if row else 0

    def list_actions_bound_to_prompt(self, prompt_doc_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.action_id, a.name, a.enabled, a.archived, a.source_type, a.readonly
                FROM ai_actions a
                JOIN ai_action_prompt_bindings b ON b.action_id = a.action_id
                WHERE b.prompt_doc_id = ?
                ORDER BY a.sort_order ASC
                """,
                (prompt_doc_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_action_bindings(self, include_archived: bool = False) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for action in self.list_actions(include_archived=include_archived):
            summary = self.get_prompt_summary_for_action(action["action_id"])
            if summary:
                items.append(summary)
        return items

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
        fallback_used = False
        fallback_reason = ""

        # Fallback logic: if prompt is None, archived, or empty content
        if prompt is None:
            fallback_used = True
            fallback_reason = "prompt_not_found"
            if prompt_doc_id != action_id:
                prompt = self.get_prompt_document(action_id)
                prompt_doc_id = action_id if prompt else prompt_doc_id
        elif int(prompt.get("archived", 0)):
            fallback_used = True
            fallback_reason = "prompt_archived"
            prompt = self.get_prompt_document(action_id)
            prompt_doc_id = action_id if prompt else prompt_doc_id
        elif not prompt.get("content_md", "").strip():
            fallback_used = True
            fallback_reason = "empty_content"
            prompt = self.get_prompt_document(action_id)
            prompt_doc_id = action_id if prompt else prompt_doc_id

        # If fallback also failed, try package seed
        if prompt is None:
            fallback_used = True
            fallback_reason = fallback_reason or "all_fallbacks_failed"
            # Try to load from package prompts as last resort
            # This is handled by PromptSeedService on next startup, but we can log here
            prompt = None

        return {
            "action": action,
            "binding": binding,
            "prompt_doc_id": prompt_doc_id,
            "prompt": prompt,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        }

    def list_action_bindings(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for action in self.list_actions():
            summary = self.get_prompt_summary_for_action(action["action_id"])
            if summary:
                items.append(summary)
        return items
