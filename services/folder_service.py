"""Folder service for database operations."""
from typing import Optional, List, Dict, Any
from .database import Database


class FolderService:
    """Handles folder database operations."""
    
    def __init__(self, database: Database):
        self.db = database

    def _get_descendant_ids(self, folder_id: str) -> List[str]:
        """Get all descendant folder IDs in post-order (children before parent)."""
        descendants: List[str] = []
        children = self.db.fetch_all(
            "SELECT id FROM folders WHERE parent_id = ?",
            (folder_id,)
        )

        for child in children:
            child_id = child["id"]
            descendants.extend(self._get_descendant_ids(child_id))
            descendants.append(child_id)

        return descendants

    def get_descendant_ids(self, folder_id: str) -> List[str]:
        """Public: list all descendant folder IDs (excluding `folder_id` itself)."""
        if not folder_id:
            return []
        return self._get_descendant_ids(folder_id)
    
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
    
    def create(self, folder_id: str, name: str, color: str = "#3B82F6", parent_id: Optional[str] = None) -> bool:
        """Create a new folder."""
        try:
            now = Database.now_iso()
            cursor = self.db.execute(
                """INSERT INTO folders (id, name, color, created_at, updated_at, sort_order, parent_id)
                   VALUES (?, ?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM folders), ?)""",
                (folder_id, name, color, now, now, parent_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
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
        except Exception:
            return False
    
    def delete(self, folder_id: str) -> bool:
        """Delete a folder and all descendants (notes cascade via FK)."""
        try:
            descendant_ids = self._get_descendant_ids(folder_id)

            for child_id in descendant_ids:
                self.db.execute(
                    "DELETE FROM folders WHERE id = ?",
                    (child_id,)
                )

            cursor = self.db.execute(
                "DELETE FROM folders WHERE id = ?",
                (folder_id,)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def get_note_count(self, folder_id: str) -> int:
        """Get count of non-deleted notes in folder."""
        result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM notes WHERE folder_id = ? AND deleted_at IS NULL",
            (folder_id,)
        )
        return result['count'] if result else 0
    
    def has_children(self, folder_id: str) -> bool:
        """Check if folder has sub-folders."""
        result = self.db.fetch_one(
            "SELECT 1 FROM folders WHERE parent_id = ? LIMIT 1",
            (folder_id,)
        )
        return result is not None

    def has_notes(self, folder_id: str) -> bool:
        """Check if folder has non-deleted notes."""
        return self.get_note_count(folder_id) > 0

    def exists(self, folder_id: str) -> bool:
        """Check if folder exists."""
        result = self.db.fetch_one(
            "SELECT 1 FROM folders WHERE id = ?",
            (folder_id,)
        )
        return result is not None
