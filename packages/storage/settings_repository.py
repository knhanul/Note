"""Compatibility wrapper for the existing settings persistence service."""

from services.settings_service import SettingsService

SettingsRepository = SettingsService

__all__ = ["SettingsRepository", "SettingsService"]
