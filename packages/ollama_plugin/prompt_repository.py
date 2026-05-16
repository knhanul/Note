"""SQLite repository for AI prompt metadata and overrides."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
        """Create all tables if they do not exist yet."""
        schema = """
        CREATE TABLE IF NOT EXISTS ai_prompt_db_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS ai_actions (
            action_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            prompt_id TEXT NOT NULL,
            input_scope TEXT,
            output_mode TEXT,
            enabled INTEGER DEFAULT 1,
            built_in INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_prompt_defaults (
            prompt_id TEXT NOT NULL,
            version TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content_md TEXT NOT NULL,
            variables_json TEXT,
            content_hash TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(prompt_id, version)
        );

        CREATE TABLE IF NOT EXISTS ai_prompt_overrides (
            prompt_id TEXT PRIMARY KEY,
            base_version TEXT,
            title TEXT,
            content_md TEXT NOT NULL,
            variables_json TEXT,
            content_hash TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            enabled INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ai_prompt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT NOT NULL,
            source TEXT NOT NULL,
            version TEXT,
            content_md TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """

        with self._connect() as conn:
            conn.executescript(schema)

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM ai_prompt_db_meta WHERE key = ?", (key,)).fetchone()
            return row[0] if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_prompt_db_meta(key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def list_actions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT action_id, name, description, category, prompt_id,
                       input_scope, output_mode, enabled, built_in, sort_order,
                       created_at, updated_at
                FROM ai_actions
                ORDER BY sort_order ASC, name COLLATE NOCASE ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_action(self, action_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT action_id, name, description, category, prompt_id,
                       input_scope, output_mode, enabled, built_in, sort_order,
                       created_at, updated_at
                FROM ai_actions
                WHERE action_id = ?
                """,
                (action_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def upsert_action(self, action: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_actions (
                    action_id, name, description, category, prompt_id,
                    input_scope, output_mode, enabled, built_in, sort_order,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(action_id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    category = excluded.category,
                    prompt_id = excluded.prompt_id,
                    input_scope = excluded.input_scope,
                    output_mode = excluded.output_mode,
                    enabled = excluded.enabled,
                    built_in = excluded.built_in,
                    sort_order = excluded.sort_order,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    action.get("action_id", ""),
                    action.get("name", ""),
                    action.get("description", ""),
                    action.get("category", ""),
                    action.get("prompt_id", ""),
                    action.get("input_scope", ""),
                    action.get("output_mode", "text"),
                    int(bool(action.get("enabled", True))),
                    int(bool(action.get("built_in", True))),
                    int(action.get("sort_order", 0)),
                ),
            )

    def get_active_default(self, prompt_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT prompt_id, version, title, description, content_md,
                       variables_json, content_hash, is_active, created_at
                FROM ai_prompt_defaults
                WHERE prompt_id = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (prompt_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def get_default_version(self, prompt_id: str, version: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT prompt_id, version, title, description, content_md,
                       variables_json, content_hash, is_active, created_at
                FROM ai_prompt_defaults
                WHERE prompt_id = ? AND version = ?
                """,
                (prompt_id, version),
            ).fetchone()
            return self._row_to_dict(row)

    def list_default_versions(self, prompt_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT prompt_id, version, title, description, content_md,
                       variables_json, content_hash, is_active, created_at
                FROM ai_prompt_defaults
                WHERE prompt_id = ?
                ORDER BY created_at DESC, version DESC
                """,
                (prompt_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def set_active_default(self, prompt_id: str, version: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE ai_prompt_defaults SET is_active = 0 WHERE prompt_id = ?",
                (prompt_id,),
            )
            conn.execute(
                "UPDATE ai_prompt_defaults SET is_active = 1 WHERE prompt_id = ? AND version = ?",
                (prompt_id, version),
            )

    def insert_default_version(self, record: dict[str, Any], active: bool = True) -> None:
        with self._connect() as conn:
            if active:
                conn.execute("UPDATE ai_prompt_defaults SET is_active = 0 WHERE prompt_id = ?", (record.get("prompt_id"),))
            conn.execute(
                """
                INSERT INTO ai_prompt_defaults (
                    prompt_id, version, title, description, content_md,
                    variables_json, content_hash, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    record.get("prompt_id", ""),
                    record.get("version", "1.0.0"),
                    record.get("title", ""),
                    record.get("description", ""),
                    record.get("content_md", ""),
                    record.get("variables_json", "[]"),
                    record.get("content_hash", ""),
                    int(bool(record.get("is_active", active))),
                ),
            )

    def get_override(self, prompt_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT prompt_id, base_version, title, content_md,
                       variables_json, content_hash, updated_at, enabled
                FROM ai_prompt_overrides
                WHERE prompt_id = ?
                """,
                (prompt_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def upsert_override(self, record: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_prompt_overrides (
                    prompt_id, base_version, title, content_md,
                    variables_json, content_hash, updated_at, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(prompt_id) DO UPDATE SET
                    base_version = excluded.base_version,
                    title = excluded.title,
                    content_md = excluded.content_md,
                    variables_json = excluded.variables_json,
                    content_hash = excluded.content_hash,
                    updated_at = CURRENT_TIMESTAMP,
                    enabled = excluded.enabled
                """,
                (
                    record.get("prompt_id", ""),
                    record.get("base_version", ""),
                    record.get("title", ""),
                    record.get("content_md", ""),
                    record.get("variables_json", "[]"),
                    record.get("content_hash", ""),
                    int(bool(record.get("enabled", True))),
                ),
            )

    def disable_override(self, prompt_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ai_prompt_overrides
                SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE prompt_id = ?
                """,
                (prompt_id,),
            )

    def insert_history(self, prompt_id: str, source: str, version: str | None, content_md: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_prompt_history(prompt_id, source, version, content_md)
                VALUES (?, ?, ?, ?)
                """,
                (prompt_id, source, version, content_md),
            )

    def get_prompt_summary(self, prompt_id: str) -> dict[str, Any] | None:
        action = self.get_action(prompt_id)
        if not action:
            return None

        default = self.get_active_default(action["prompt_id"])
        override = self.get_override(action["prompt_id"])
        if override and not override.get("enabled", 1):
            override = None

        return {
            "action": action,
            "default": default,
            "override": override,
        }

    def list_prompt_summaries(self) -> list[dict[str, Any]]:
        summaries = []
        for action in self.list_actions():
            default = self.get_active_default(action["prompt_id"])
            override = self.get_override(action["prompt_id"])
            if override and not override.get("enabled", 1):
                override = None

            summaries.append({
                "action": action,
                "default": default,
                "override": override,
            })
        return summaries
