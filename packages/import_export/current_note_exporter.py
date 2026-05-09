"""Compatibility wrapper for current-note export services."""

from services.current_note_export_service import CurrentNoteExportService

CurrentNoteExporter = CurrentNoteExportService

__all__ = ["CurrentNoteExporter", "CurrentNoteExportService"]
