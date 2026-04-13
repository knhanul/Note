"""Note model for Nuni Note."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class Note:
    """Represents a note in the note-taking app."""
    
    title: str
    content: str = ""
    folder_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_pinned: bool = False
    
    def to_dict(self) -> dict:
        """Convert note to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'folder_id': self.folder_id,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_pinned': self.is_pinned
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Note':
        """Create note from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            title=data['title'],
            content=data.get('content', ''),
            folder_id=data.get('folder_id'),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now(),
            is_pinned=data.get('is_pinned', False)
        )
    
    def move_to_folder(self, folder_id: Optional[str]) -> None:
        """Move note to a different folder."""
        self.folder_id = folder_id
        self.updated_at = datetime.now()
    
    def update_content(self, title: str, content: str) -> None:
        """Update note content."""
        self.title = title
        self.content = content
        self.updated_at = datetime.now()
