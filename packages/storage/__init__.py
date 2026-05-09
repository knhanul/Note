"""Storage compatibility layer for Note2.

This package currently re-exports the existing services-based storage classes
without changing database paths, schemas, or method signatures.
"""

from .database import Database
from .folder_repository import FolderRepository, FolderService
from .library_repository import LibraryRepository, LibraryService
from .note_repository import NoteRepository, NoteService
from .settings_repository import SettingsRepository, SettingsService

__all__ = [
    "Database",
    "NoteRepository",
    "NoteService",
    "FolderRepository",
    "FolderService",
    "LibraryRepository",
    "LibraryService",
    "SettingsRepository",
    "SettingsService",
]
