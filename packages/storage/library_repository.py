"""Compatibility wrapper for the existing library storage service."""

from services.library_service import LibraryService

LibraryRepository = LibraryService

__all__ = ["LibraryRepository", "LibraryService"]
