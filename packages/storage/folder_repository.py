"""Compatibility wrapper for the existing folder storage service."""

from services.folder_service import FolderService

FolderRepository = FolderService

__all__ = ["FolderRepository", "FolderService"]
