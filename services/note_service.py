"""Note service for database operations."""
from typing import Optional, List, Dict, Any
from .database import Database


class NoteService:
    """Handles note database operations."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def get_all(self, folder_id: Optional[str] = None, 
                include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Get all notes, optionally filtered by folder."""
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        
        if folder_id:
            query += " AND folder_id = ?"
            params.append(folder_id)
        
        if not include_deleted:
            query += " AND deleted_at IS NULL"
        
        query += " ORDER BY is_pinned DESC, updated_at DESC"
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_by_id(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Get note by ID."""
        return self.db.fetch_one(
            "SELECT * FROM notes WHERE id = ? AND deleted_at IS NULL",
            (note_id,)
        )
    
    def create(self, note_id: str, folder_id: str, title: str = "", 
               content: str = "") -> bool:
        """Create a new note."""
        try:
            now = Database.now_iso()
            cursor = self.db.execute(
                """INSERT INTO notes (id, folder_id, title, content, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (note_id, folder_id, title, content, now, now)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[NoteService] Create error: {e}")
            return False
    
    def update(self, note_id: str, title: Optional[str] = None,
               content: Optional[str] = None, 
               folder_id: Optional[str] = None) -> bool:
        """Update note fields."""
        try:
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if content is not None:
                updates.append("content = ?")
                params.append(content)
            if folder_id is not None:
                updates.append("folder_id = ?")
                params.append(folder_id)
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            params.append(Database.now_iso())
            params.append(note_id)
            
            query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL"
            cursor = self.db.execute(query, tuple(params))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[NoteService] Update error: {e}")
            return False
    
    def soft_delete(self, note_id: str) -> bool:
        """Soft delete a note (sets deleted_at)."""
        try:
            now = Database.now_iso()
            cursor = self.db.execute(
                "UPDATE notes SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL",
                (now, note_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[NoteService] Soft delete error: {e}")
            return False
    
    def hard_delete(self, note_id: str) -> bool:
        """Permanently delete a note."""
        try:
            cursor = self.db.execute(
                "DELETE FROM notes WHERE id = ?",
                (note_id,)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[NoteService] Hard delete error: {e}")
            return False
    
    def restore(self, note_id: str) -> bool:
        """Restore a soft-deleted note."""
        try:
            cursor = self.db.execute(
                "UPDATE notes SET deleted_at = NULL WHERE id = ?",
                (note_id,)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[NoteService] Restore error: {e}")
            return False
    
    def move_to_folder(self, note_id: str, folder_id: str) -> bool:
        """Move note to different folder."""
        return self.update(note_id, folder_id=folder_id)
    
    def set_pinned(self, note_id: str, is_pinned: bool) -> bool:
        """Set note pinned status."""
        try:
            cursor = self.db.execute(
                "UPDATE notes SET is_pinned = ?, updated_at = ? WHERE id = ?",
                (1 if is_pinned else 0, Database.now_iso(), note_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[NoteService] Set pinned error: {e}")
            return False
    
    def search(self, query: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search notes by title or content."""
        search_term = f"%{query}%"
        sql = """SELECT * FROM notes 
                   WHERE (title LIKE ? OR content LIKE ?) 
                   AND deleted_at IS NULL"""
        params = [search_term, search_term]
        
        if folder_id:
            sql += " AND folder_id = ?"
            params.append(folder_id)
        
        sql += " ORDER BY updated_at DESC"
        
        return self.db.fetch_all(sql, tuple(params))
    
    def exists(self, note_id: str) -> bool:
        """Check if note exists and is not deleted."""
        result = self.db.fetch_one(
            "SELECT 1 FROM notes WHERE id = ? AND deleted_at IS NULL",
            (note_id,)
        )
        return result is not None
    
    def get_preview_text(self, content: str, max_length: int = 100) -> str:
        """Extract preview text from content."""
        # Remove markdown syntax for preview
        text = content.replace('#', '').replace('*', '').replace('`', '')
        text = ' '.join(text.split())  # Normalize whitespace
        
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'
