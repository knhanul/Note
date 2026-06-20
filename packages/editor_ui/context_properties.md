# QML Context Properties

## Source of truth

`app_bootstrap.py` currently injects QML context properties in `configure_qml_engine()`.

## Current context property list

- `libraryService`: instance of `LibraryService`
- `folderController`: instance of `FolderController`
- `noteController`: instance of `NoteController`
- `templateController`: instance of `TemplateController`
- `currentExportController`: instance of `CurrentExportController`
- `folderImportController`: instance of `FolderImportController`
- `appName`: display app name from `AppConfig`
- `appLogoPath`: logo path string from `AppConfig`

`settingsService` is created in Python but is not currently injected as a QML context property in `app_bootstrap.py`.

## Main.qml usage pattern

`Main.qml` uses these context properties directly for:

- folder list model and folder operations through `folderController`
- note list model, note CRUD, tag, save, selection, pagination, and image operations through `noteController`
- templates through `templateController`
- current note and folder export through `currentExportController`
- folder import progress and execution through `folderImportController`
- library switching/list updates through `libraryService`
- app title/logo/branding through `appName`, `appLogoPath`

`Main.qml` also creates `Connections` blocks for controller signals.

## Component usage pattern

Most components receive data through explicit QML properties and emit signals upward.

Known direct component dependencies:

- `WebNoteEditor.qml` uses global `noteController.saveLocalImage(...)` for local image insertion.
- `FolderItem.qml` uses a `Connections` block targeting global `folderController` for `folderAddedForRename`.

## Names that should remain stable

The following names are runtime API for QML and should not be renamed casually:

- `libraryService`
- `folderController`
- `noteController`
- `templateController`
- `currentExportController`
- `folderImportController`
- `appName`
- `appLogoPath`

## Signal names that are coupled to QML

Examples include:

- `folderController.libraryChanged`, `foldersChanged`, `currentFolderChanged`, `folderDeleteFailed`, `folderAddedForRename`
- `noteController.libraryChanged`, `filteredNotesChanged`, `noteSelected`, `notesChanged`, `tagsChanged`, `noteUpdated`, `saveStatusChanged`
- `templateController.templatesChanged`
- `folderImportController.importProgress`, `importFinished`
- `currentExportController.exportProgress`, `exportFinished`

## Extension principles

- Add new context properties under stable, explicit names.
- Prefer passing data into reusable components via properties instead of adding more global dependencies.
- Plugin/app-specific context should be grouped behind an app shell or plugin registry rather than directly scattered through common components.
- Keep existing names until all QML references are migrated and tested.
