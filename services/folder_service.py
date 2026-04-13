"""Folder service for database operations."""
from typing import Optional, List, Dict, Any
from .database import Database


class FolderService:
    """Handles folder database operations."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all folders ordered by sort_order."""
        return self.db.fetch_all(
            "SELECT * FROM folders ORDER BY sort_order, created_at"
        )
    
    def get_by_id(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """Get folder by ID."""
        return self.db.fetch_one(
            "SELECT * FROM folders WHERE id = ?",
            (folder_id,)
        )
    
    def create(self, folder_id: str, name: str, color: str = "#3B82F6") -> bool:
        """Create a new folder."""
        try:
            now = Database.now_iso()
            cursor = self.db.execute(
                """INSERT INTO folders (id, name, color, created_at, updated_at, sort_order)
                   VALUES (?, ?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM folders))""",
                (folder_id, name, color, now, now)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[FolderService] Create error: {e}")
            return False
    
    def update(self, folder_id: str, name: Optional[str] = None, 
               color: Optional[str] = None) -> bool:
        """Update folder name and/or color."""
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if color is not None:
                updates.append("color = ?")
                params.append(color)
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            params.append(Database.now_iso())
            params.append(folder_id)
            
            query = f"UPDATE folders SET {', '.join(updates)} WHERE id = ?"
            cursor = self.db.execute(query, tuple(params))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[FolderService] Update error: {e}")
            return False
    
    def delete(self, folder_id: str) -> bool:
        """Delete a folder (cascades to notes via FK)."""
        try:
            cursor = self.db.execute(
                "DELETE FROM folders WHERE id = ?",
                (folder_id,)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[FolderService] Delete error: {e}")
            return False
    
    def get_note_count(self, folder_id: str) -> int:
        """Get count of non-deleted notes in folder."""
        result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM notes WHERE folder_id = ? AND deleted_at IS NULL",
            (folder_id,)
        )
        return result['count'] if result else 0
    
    def exists(self, folder_id: str) -> bool:
        """Check if folder exists."""
        result = self.db.fetch_one(
            "SELECT 1 FROM folders WHERE id = ?",
            (folder_id,)
        )
        return result is not None
