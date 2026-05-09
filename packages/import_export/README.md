# Import/Export Layer

`packages.import_export` is the planned boundary for document import, export, and format conversion logic in Note2.

## Purpose

This layer will collect reusable import/export capabilities so multiple editor apps can share the same current-note export, folder export, folder import, and HWP/HWPX conversion behavior without copying application code.

## Relationship with existing services

The current implementation is a compatibility wrapper around existing modules:

- `packages.import_export.current_note_exporter.CurrentNoteExportService` re-exports `services.current_note_export_service.CurrentNoteExportService`
- `packages.import_export.folder_exporter.FolderExportService` re-exports `services.folder_export_service.FolderExportService`
- `packages.import_export.folder_importer.FolderImportService` re-exports `services.folder_import_service.FolderImportService`
- `packages.import_export.hwp_converter.convert_hwp_to_hwpx_via_com` re-exports `services.hwp_converter.convert_hwp_to_hwpx_via_com`
- `packages.import_export.hwpx_importer.hwpx_to_markdown` and related document block types re-export `services.hwpx_importer`

The existing `services` files remain the source of truth in this step.

## Current phase

This is a compatibility-wrapper phase. No export format, import behavior, conversion behavior, file path, image path, database path, method signature, or controller signal behavior is changed.

## Current responsibilities

- Current note export: exports the currently opened note to supported formats through the existing current-note export service.
- Folder export: exports notes under folder scopes while preserving existing folder traversal and output behavior.
- Folder import: imports supported document files and folder trees into the current library using existing services.
- HWP converter: exposes the existing HWP to HWPX COM conversion helper.
- HWPX importer: exposes the existing HWPX to Markdown conversion helper and block data types.

## Future direction

QML-facing controllers should remain adapter/bridge objects. Pure conversion, file IO, metadata parsing, and format-specific import/export logic can gradually move from `services` into this package once compatibility tests exist.

## Stability rules

Refactoring this layer must not silently change existing export/import output formats. It must also not change database paths, image storage paths, library paths, or settings paths unless a separate migration is explicitly designed and tested.
