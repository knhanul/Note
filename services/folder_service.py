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

    def get_siblings(self, parent_id: Optional[str]) -> List[Dict[str, Any]]:
        """Get folders with the same parent ordered by display order."""
        if parent_id is None:
            return self.db.fetch_all(
                "SELECT * FROM folders WHERE parent_id IS NULL ORDER BY sort_order, created_at"
            )
        return self.db.fetch_all(
            "SELECT * FROM folders WHERE parent_id = ? ORDER BY sort_order, created_at",
            (parent_id,)
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
               color: Optional[str] = None,
               default_template_id: Optional[str] = None) -> bool:
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
            if default_template_id is not None:
                updates.append("default_template_id = ?")
                params.append(default_template_id)
            
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

    def move(self, folder_id: str, parent_id: Optional[str]) -> bool:
        """Move a folder to another parent folder or root."""
        try:
            cursor = self.db.execute(
                """UPDATE folders
                   SET parent_id = ?, updated_at = ?,
                       sort_order = (
                           SELECT COALESCE(MAX(sort_order), 0) + 1
                           FROM folders
                           WHERE parent_id IS ?
                       )
                   WHERE id = ?""",
                (parent_id, Database.now_iso(), parent_id, folder_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

    def reorder_within_parent(self, folder_id: str, direction: int) -> bool:
        """Move a folder up/down within the same parent."""
        try:
            print(f"[reorder_within_parent] folder_id={folder_id}, direction={direction}")
            folder = self.get_by_id(folder_id)
            if not folder:
                print(f"[reorder_within_parent] folder not found")
                return False

            parent_id = folder.get("parent_id")
            print(f"[reorder_within_parent] parent_id={parent_id}")
            siblings = self.get_siblings(parent_id)
            print(f"[reorder_within_parent] siblings count={len(siblings)}")
            ids = [item["id"] for item in siblings]
            if folder_id not in ids:
                print(f"[reorder_within_parent] folder_id not in siblings")
                return False

            current_index = ids.index(folder_id)
            target_index = current_index - 1 if direction < 0 else current_index + 1
            print(f"[reorder_within_parent] current_index={current_index}, target_index={target_index}")
            if target_index < 0 or target_index >= len(siblings):
                print(f"[reorder_within_parent] target_index out of bounds")
                return False

            siblings[current_index], siblings[target_index] = siblings[target_index], siblings[current_index]
            now = Database.now_iso()
            for index, item in enumerate(siblings, start=1):
                self.db.execute(
                    "UPDATE folders SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (index, now, item["id"])
                )
            self.db.commit()
            print(f"[reorder_within_parent] success")
            return True
        except Exception as e:
            print(f"[reorder_within_parent] exception: {e}")
            return False

    def update_placement(self, folder_id: str, parent_id: Optional[str], target_index: int) -> bool:
        """Update folder's parent and position in a single transaction."""
        try:
            print(f"[update_placement] folder_id={folder_id}, parent_id={parent_id}, target_index={target_index}")
            folder = self.get_by_id(folder_id)
            if not folder:
                print(f"[update_placement] folder not found")
                return False

            old_parent_id = folder.get("parent_id")
            print(f"[update_placement] old_parent_id={old_parent_id}")

            # First, remove the folder from its current position
            old_siblings = self.get_siblings(old_parent_id)
            print(f"[update_placement] old_siblings count={len(old_siblings)}")
            for idx, sibling in enumerate(old_siblings, start=1):
                if sibling["id"] != folder_id:
                    self.db.execute(
                        "UPDATE folders SET sort_order = ?, updated_at = ? WHERE id = ?",
                        (idx, Database.now_iso(), sibling["id"])
                    )

            # Then, update the folder's parent
            self.db.execute(
                "UPDATE folders SET parent_id = ?, updated_at = ? WHERE id = ?",
                (parent_id, Database.now_iso(), folder_id)
            )

            # Finally, re-sort the new siblings including the moved folder
            new_siblings = self.get_siblings(parent_id)
            print(f"[update_placement] new_siblings count={len(new_siblings)}")

            # If target_index is specified, move the folder to that position
            if target_index >= 0 and target_index < len(new_siblings):
                # Remove the folder from its current position in the list
                moved_folder = None
                filtered_siblings = []
                for sibling in new_siblings:
                    if sibling["id"] == folder_id:
                        moved_folder = sibling
                    else:
                        filtered_siblings.append(sibling)

                # Insert at target_index
                if moved_folder:
                    filtered_siblings.insert(target_index, moved_folder)
                    new_siblings = filtered_siblings

            for idx, sibling in enumerate(new_siblings, start=1):
                self.db.execute(
                    "UPDATE folders SET sort_order = ?, updated_at = ? WHERE id = ?",
                    (idx, Database.now_iso(), sibling["id"])
                )

            self.db.commit()
            print(f"[update_placement] success")
            return True
        except Exception as e:
            print(f"[update_placement] exception: {e}")
            self.db.rollback()
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

    def set_default_template(self, folder_id: str, template_id: Optional[str]) -> bool:
        """Set or clear the default template for a folder."""
        try:
            cursor = self.db.execute(
                "UPDATE folders SET default_template_id = ?, updated_at = ? WHERE id = ?",
                (template_id, Database.now_iso(), folder_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

    def get_default_template_id(self, folder_id: str) -> Optional[str]:
        """Get the default template id for a folder."""
        folder = self.get_by_id(folder_id)
        if not folder:
            return None
        return folder.get('default_template_id')
    
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
