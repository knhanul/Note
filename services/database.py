"""SQLite database service for Nuni Note application."""
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    """Manages SQLite database connection and schema."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database with optional custom path."""
        if db_path is None:
            # Store in program directory (where main.py is located)
            prog_dir = Path(__file__).parent.parent
            db_path = prog_dir / "nuni_note.db"
        
        self.db_path = str(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            # Return rows as dictionaries
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def init_schema(self):
        """Initialize database schema with tables."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Folders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#3B82F6',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                parent_id TEXT DEFAULT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (parent_id) REFERENCES folders (id) ON DELETE SET NULL
            )
        """)
        
        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                folder_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                content_format TEXT DEFAULT 'markdown',
                summary TEXT DEFAULT '',
                is_pinned INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT DEFAULT NULL,
                FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE
            )
        """)
        
        # Tags table (for future expansion)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#64748B',
                created_at TEXT NOT NULL
            )
        """)
        
        # Note-Tag relationship table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id TEXT NOT NULL,
                tag_id TEXT NOT NULL,
                PRIMARY KEY (note_id, tag_id),
                FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
        """)

        # Note images table (stores image payloads separately from notes.content)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_images (
                id TEXT PRIMARY KEY,
                note_id TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                data_base64 TEXT NOT NULL,
                checksum TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes (folder_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes (updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_deleted ON notes (deleted_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_images_note ON note_images (note_id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_note_images_note_checksum ON note_images (note_id, checksum)")
        
        conn.commit()

        # Migration: add content_json column if not present
        try:
            cursor.execute("ALTER TABLE notes ADD COLUMN content_json TEXT DEFAULT NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    def execute(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        return cursor
    
    def executemany(self, query: str, parameters: List[tuple]) -> sqlite3.Cursor:
        """Execute a SQL query with multiple parameter sets."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, parameters)
        return cursor
    
    def fetch_one(self, query: str, parameters: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row as dictionary."""
        cursor = self.execute(query, parameters)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        cursor = self.execute(query, parameters)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def commit(self):
        """Commit current transaction."""
        if self._connection:
            self._connection.commit()
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        return {
            'folders': self.fetch_one("SELECT COUNT(*) as count FROM folders")['count'],
            'notes': self.fetch_one("SELECT COUNT(*) as count FROM notes WHERE deleted_at IS NULL")['count'],
            'deleted_notes': self.fetch_one("SELECT COUNT(*) as count FROM notes WHERE deleted_at IS NOT NULL")['count'],
        }
    
    @staticmethod
    def now_iso() -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
