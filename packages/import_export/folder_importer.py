"""Compatibility wrapper for folder import services."""

from services.folder_import_service import FolderImportService

FolderImporter = FolderImportService

__all__ = ["FolderImporter", "FolderImportService"]
