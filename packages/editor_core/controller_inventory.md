# Controller Inventory

## Composition root

`app_bootstrap.py` creates the runtime controller graph and injects QML context properties:

- `libraryService` -> `LibraryService`
- `folderController` -> `FolderController`
- `noteController` -> `NoteController`
- `templateController` -> `TemplateController`
- `currentExportController` -> `CurrentExportController`
- `folderImportController` -> `FolderImportController`
- branding values: `appBrand`, `appName`, `appLogoPath`
- readiness flag: `folderControllerReady`

These names are public QML API and should remain stable during migration.

## NoteController

File: `controllers/note_controller.py`

Role:

- QML bridge for notes, tags, filtering, current note state, save status, clipboard/image helpers, and note CRUD.
- Coordinates `NoteService`, `FolderController`, `LibraryService`, and `ImageService`.
- Owns autosave/deferred-save worker thread state.

Services used:

- `LibraryService`
- `NoteService`
- `ImageService`
- `FolderController` as collaborator

Main QML properties:

- `allNotes`
- `filteredNotes`
- `allTags`
- `selectedTag`
- `currentFolderName`
- `saveStatus`
- `currentNoteId`
- `isDirty`
- `isSaving`
- `includeSubfolders`
- `sortField`
- `sortOrder`
- `searchKeyword`
- `filterFromDate`
- `filterToDate`
- `isFilterActive`

Main signals:

- `notesChanged`
- `filteredNotesChanged`
- `tagsChanged`
- `noteAdded`
- `noteRemoved`
- `noteUpdated`
- `noteSelected`
- `saveStatusChanged`
- `libraryChanged`

High-risk QML slots/methods:

- `updateNoteWithJson`
- `saveCurrentNote`
- `selectNote`
- `createNote`
- `getNote`
- `moveNotesToFolder`
- `copyNotesToFolder`
- `deleteNotes`
- `saveLocalImage`
- `saveBase64Image`
- `pasteImageFromClipboard`

Dangerous internals:

- `_perform_save`
- `_start_async_note_update`
- `_on_async_save_finished`
- `_edit_version`
- `_last_saved_version`
- `_save_pending`
- `_pending_title`
- `_pending_content`
- `_pending_json`
- `_store_data_urls_and_tokenize`
- `_hydrate_image_tokens`

## FolderController

File: `controllers/folder_controller.py`

Role:

- QML bridge for folder tree, smart folders, current folder selection, folder CRUD, folder hierarchy, collapsed state, and folder movement.
- Coordinates `FolderService`, `LibraryService`, and `SettingsService`.

Services used:

- `LibraryService`
- `SettingsService`
- `FolderService`

Main state:

- `_current_folder_id`
- `_folder_service`
- `_collapsed_folder_ids`
- current library database reference

Main signals:

- `foldersChanged`
- `currentFolderChanged`
- `folderAdded`
- `folderAddedForRename`
- `folderRemoved`
- `folderRenamed`
- `folderDeleteFailed`
- `libraryChanged`

Main QML properties/methods:

- `folders`
- `currentFolderId`
- `currentFolderName`
- folder create/update/delete/select helpers
- smart-folder helpers
- descendant-folder helpers
- collapse/expand helpers

High-risk behavior:

- `SMART_FOLDERS` is UI/app policy mixed into the controller.
- `folders` property mutates/enriches service rows with tree metadata for QML.
- Last selected folder restoration depends on `SettingsService`.

## TemplateController

File: `controllers/template_controller.py`

Role:

- QML bridge for template CRUD and template rendering.
- Recreates `TemplateService` on library change.
- Emits folder refresh signals when deleting templates to update folder defaults.

Services used:

- `LibraryService`
- `TemplateService`
- optional `FolderController`

Main signals:

- `templatesChanged`
- `templateAdded`
- `templateUpdated`
- `templateRemoved`

Main QML API:

- `templates`
- `getTemplate`
- `renderTemplate`
- `getDefaultExampleTemplate`
- `createTemplate`
- `updateTemplate`
- `deleteTemplate`

Risk:

- Template default/example policy belongs closer to app/core policy than QML adapter.
- Delete side effects reach into folder UI refresh.

## CurrentExportController

File: `controllers/current_export_controller.py`

Role:

- QML bridge for current-note and folder/batch export operations.
- Owns export worker/thread orchestration.
- Converts service results into QML-friendly messages.

Services used:

- `CurrentNoteExportService`
- `FolderExportService`
- `FolderService`
- `NoteService`
- `LibraryService`

Signals:

- `exportProgress`
- `exportFinished`

Main QML API:

- `safeFilename`
- `openDirectory`
- `exportCurrentNote`
- `exportCurrentNoteAsync`
- `exportFolderNotes`
- `exportFolderNotesAsync`

Risk:

- Thread ownership, progress relays, message wording, and export scope policy are mixed.

## FolderImportController

File: `controllers/folder_import_controller.py`

Role:

- QML bridge for importing directory trees into the current library.
- Owns import worker/thread orchestration.
- Refreshes folder/note/tag UI state after import.

Services used:

- `FolderImportService`
- `FolderService`
- `NoteService`
- `LibraryService`
- `FolderController`
- `NoteController`

Signals:

- `importProgress`
- `importFinished`

Main QML API:

- `importDirectory`
- `importDirectoryAsync`

Risk:

- Import execution, smart-folder parent policy, UI refresh, folder selection, and message formatting are mixed.

## Service responsibilities referenced by controllers

- `NoteService`: note CRUD, soft/hard delete, batch move/delete, pinning, search, preview, tags, note image table access.
- `FolderService`: folder CRUD, hierarchy, note counts, parent/child relationships.
- `TemplateService`: template CRUD and variable rendering.
- `ImageService`: clipboard/local image conversion and markdown image insertion helpers.
- `CurrentNoteExportService`: current editor payload export.
- `FolderImportService`: directory tree import into folders/notes.

## Public API risk rule

Any method decorated with `pyqtSlot`, any `pyqtProperty`, and any `pyqtSignal` connected from QML should be treated as public adapter API until a compatibility layer exists.
