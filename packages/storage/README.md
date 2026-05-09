# Storage Layer

`packages.storage` is the planned storage boundary for the Note2 application.

## Purpose

This layer will collect persistence-related code for notes, folders, libraries, settings, and database access so future apps can reuse the same storage behavior without copying application code.

## Relationship with existing services

The current implementation is a compatibility wrapper around the existing `services` modules:

- `packages.storage.database.Database` re-exports `services.database.Database`
- `packages.storage.note_repository.NoteRepository` aliases `services.note_service.NoteService`
- `packages.storage.folder_repository.FolderRepository` aliases `services.folder_service.FolderService`
- `packages.storage.library_repository.LibraryRepository` aliases `services.library_service.LibraryService`
- `packages.storage.settings_repository.SettingsRepository` aliases `services.settings_service.SettingsService`

The existing `services` files remain the source of truth in this step.

## Current phase

This is a compatibility-wrapper phase. No database path, schema, settings path, library path, method signature, or runtime behavior is changed.

## Future direction

A later refactor can gradually move implementation from `services` into repository classes under `packages.storage`, while keeping temporary aliases for backward compatibility.

## Path and schema rule

Storage refactoring must not silently change existing data locations or schemas. In particular, the current behavior for `app_data`, `libraries`, `nuni_note.db`, and `nuni_note_settings.json` must remain compatible unless a separate migration is explicitly designed and tested.

## App-specific policy

App-specific storage policy should be configured through app configuration or plugin configuration. Actual persistence primitives should converge into this storage layer over time.
