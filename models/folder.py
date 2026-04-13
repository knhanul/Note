"""Folder model for Nuni Note."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Folder:
    """Represents a folder in the note-taking app."""
    
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    color: str = "#3B82F6"  # Default blue
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    note_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert folder to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'note_count': self.note_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Folder':
        """Create folder from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            name=data['name'],
            color=data.get('color', '#3B82F6'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now(),
            note_count=data.get('note_count', 0)
        )
    
    def update_name(self, new_name: str) -> None:
        """Update folder name."""
        self.name = new_name
        self.updated_at = datetime.now()
