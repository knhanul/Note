"""Compatibility wrapper for folder export services."""

from services.folder_export_service import FolderExportService

FolderExporter = FolderExportService

__all__ = ["FolderExporter", "FolderExportService"]
