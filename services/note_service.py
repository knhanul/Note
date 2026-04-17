"""Note service for database operations."""
from typing import Optional, List, Dict, Any
import uuid
import json
from .database import Database


class NoteService:
    """Handles note database operations."""
    
    def __init__(self, database: Database):
        self.db = database
    
    @staticmethod
    def _parse_tags(note: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure note has a parsed 'tags' list."""
        raw = note.get('tags')
        if isinstance(raw, list):
            return note
        try:
            note['tags'] = json.loads(raw) if raw else []
        except Exception:
            note['tags'] = []
        return note

    def get_all(self, folder_id: Optional[str] = None,
                include_deleted: bool = False,
                tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all notes, optionally filtered by folder and/or tag."""
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        
        if folder_id:
            query += " AND folder_id = ?"
            params.append(folder_id)
        
        if not include_deleted:
            query += " AND deleted_at IS NULL"
        
        query += " ORDER BY updated_at DESC"
        
        notes = [self._parse_tags(n) for n in self.db.fetch_all(query, tuple(params))]

        if tag:
            # Support hierarchical prefix match: tag="dev" matches "dev/python"
            notes = [n for n in notes if any(
                t == tag or t.startswith(tag + '/') for t in n['tags']
            )]

        return notes

    def get_pinned(self, ensure_note_id: str = None) -> List[Dict[str, Any]]:
        """Get all pinned, non-deleted notes."""
        result = [self._parse_tags(n) for n in self.db.fetch_all(
            """SELECT * FROM notes
               WHERE is_pinned = 1 AND deleted_at IS NULL
               ORDER BY updated_at DESC"""
        )]

        # If ensure_note_id is provided and not in results, fetch and prepend it
        if ensure_note_id and not any(n['id'] == ensure_note_id for n in result):
            note = self.get_by_id(ensure_note_id)
            if note and not note.get('deleted_at'):
                result.insert(0, note)

        return result

    def get_recent(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get notes updated within the last N days (non-deleted)."""
        return self.db.fetch_all(
            """SELECT * FROM notes
               WHERE deleted_at IS NULL
                 AND datetime(updated_at) >= datetime('now', ?)
               ORDER BY updated_at DESC""",
            (f"-{days} days",)
        )
    
    def get_by_id(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Get note by ID."""
        note = self.db.fetch_one(
            "SELECT * FROM notes WHERE id = ? AND deleted_at IS NULL",
            (note_id,)
        )
        return self._parse_tags(note) if note else None
    
    def create(self, note_id: str, folder_id: str, title: str = "",
               content: str = "", content_json: str = "") -> bool:
        """Create a new note."""
        try:
            now = Database.now_iso()
            cursor = self.db.execute(
                """INSERT INTO notes (id, folder_id, title, content, content_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (note_id, folder_id, title, content, content_json or None, now, now)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def update(self, note_id: str, title: Optional[str] = None,
               content: Optional[str] = None,
               content_json: Optional[str] = None,
               folder_id: Optional[str] = None,
               tags: Optional[List[str]] = None) -> bool:
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
            if content_json is not None:
                updates.append("content_json = ?")
                params.append(content_json or None)
            if folder_id is not None:
                updates.append("folder_id = ?")
                params.append(folder_id)
            if tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(tags, ensure_ascii=False))
            
            if not updates:
                return False
            
            updates.append("updated_at = ?")
            params.append(Database.now_iso())
            params.append(note_id)
            
            query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL"
            cursor = self.db.execute(query, tuple(params))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
            return False
    
    def move_to_folder(self, note_id: str, folder_id: str) -> bool:
        """Move note to different folder."""
        return self.update(note_id, folder_id=folder_id)
    
    def set_pinned(self, note_id: str, is_pinned: bool) -> bool:
        """Set note pinned status."""
        try:
            pinned_val = 1 if is_pinned else 0
            # Don't update updated_at to preserve note order
            cursor = self.db.execute(
                "UPDATE notes SET is_pinned = ? WHERE id = ?",
                (pinned_val, note_id)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
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

    def search_by_terms(self, terms: List[str]) -> List[Dict[str, Any]]:
        """Search notes by multiple terms (OR condition)."""
        if not terms:
            return []
        
        # Build OR conditions for each term
        conditions = []
        params = []
        for term in terms:
            search_term = f"%{term}%"
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([search_term, search_term])
        
        sql = f"""SELECT DISTINCT * FROM notes 
                    WHERE ({' OR '.join(conditions)})
                    AND deleted_at IS NULL
                    ORDER BY updated_at DESC"""
        
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

    def get_all_tags(self, folder_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Aggregate tags and return as a depth-first tree-flattened list.

        Each item: {name (full path), display (leaf label), count (aggregate),
                    depth (int), has_children (bool)}
        Virtual parent nodes are inserted for intermediate path segments.
        """
        if folder_ids:
            placeholders = ','.join('?' * len(folder_ids))
            notes = [self._parse_tags(n) for n in self.db.fetch_all(
                f"SELECT tags FROM notes WHERE folder_id IN ({placeholders}) AND deleted_at IS NULL",
                tuple(folder_ids)
            )]
        else:
            notes = [self._parse_tags(n) for n in self.db.fetch_all(
                "SELECT tags FROM notes WHERE deleted_at IS NULL"
            )]

        # Step 1: collect direct counts per full path
        direct: Dict[str, int] = {}
        for note in notes:
            for tag in note.get('tags', []):
                tag = tag.strip()
                if tag:
                    direct[tag] = direct.get(tag, 0) + 1

        if not direct:
            return []

        # Step 2: build node map (includes virtual parents)
        # node_map[path] = {direct_count, children: set}
        node_map: Dict[str, Dict] = {}

        for tag, cnt in direct.items():
            parts = tag.split('/')
            for i in range(len(parts)):
                path = '/'.join(parts[:i + 1])
                if path not in node_map:
                    node_map[path] = {'direct_count': 0, 'children': set()}
                if i == len(parts) - 1:
                    node_map[path]['direct_count'] = cnt
                if i > 0:
                    parent = '/'.join(parts[:i])
                    node_map[parent]['children'].add(path)

        # Step 3: memoised aggregate count
        _cache: Dict[str, int] = {}

        def aggregate(path: str) -> int:
            if path in _cache:
                return _cache[path]
            total = node_map[path]['direct_count']
            for child in node_map[path]['children']:
                total += aggregate(child)
            _cache[path] = total
            return total

        # Step 4: DFS flattening (alphabetical at each level)
        result: List[Dict[str, Any]] = []

        def visit(path: str, depth: int) -> None:
            node = node_map[path]
            children = sorted(node['children'], key=str.lower)
            result.append({
                'name': path,
                'display': path.split('/')[-1],
                'count': aggregate(path),
                'depth': depth,
                'has_children': bool(children),
            })
            for child in children:
                visit(child, depth + 1)

        roots = sorted(
            (p for p in node_map if '/' not in p),
            key=str.lower
        )
        for root in roots:
            visit(root, 0)

        return result

    def update_tags(self, note_id: str, tags: List[str]) -> bool:
        """Update the tags list for a note."""
        return self.update(note_id, tags=tags)

    # Note image APIs
    def upsert_note_image(self, note_id: str, mime_type: str, data_base64: str, checksum: str) -> str:
        """Insert note image payload or reuse existing one by checksum."""
        existing = self.db.fetch_one(
            "SELECT id FROM note_images WHERE note_id = ? AND checksum = ?",
            (note_id, checksum)
        )
        if existing:
            return existing['id']

        image_id = str(uuid.uuid4())[:16]
        self.db.execute(
            """INSERT INTO note_images (id, note_id, mime_type, data_base64, checksum, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (image_id, note_id, mime_type, data_base64, checksum, Database.now_iso())
        )
        self.db.commit()
        return image_id

    def get_note_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Fetch note image by image id."""
        return self.db.fetch_one(
            "SELECT id, note_id, mime_type, data_base64, checksum FROM note_images WHERE id = ?",
            (image_id,)
        )

    def delete_unused_note_images(self, note_id: str, keep_image_ids: List[str]) -> None:
        """Delete note images not referenced by current note content."""
        keep_set = set(keep_image_ids)
        rows = self.db.fetch_all("SELECT id FROM note_images WHERE note_id = ?", (note_id,))
        for row in rows:
            image_id = row['id']
            if image_id not in keep_set:
                self.db.execute("DELETE FROM note_images WHERE id = ?", (image_id,))
        self.db.commit()
