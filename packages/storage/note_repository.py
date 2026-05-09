"""Compatibility wrapper for the existing note storage service."""

from services.note_service import NoteService

NoteRepository = NoteService

__all__ = ["NoteRepository", "NoteService"]
