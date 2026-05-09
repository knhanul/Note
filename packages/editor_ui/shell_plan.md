# Future App Shell Plan

This is a planning document only. No QML shell files are created in this step.

## Proposed future structure

```text
editor_ui/qml/shell/
  AppShell.qml
  FolderPanel.qml
  NoteListPanel.qml
  EditorPanel.qml
  CommandDialogs.qml
  AppHeaderArea.qml
```

## AppShell.qml

Top-level layout container that composes header, sidebar/folder panel, note list, editor panel, and command dialogs.

Likely needs:

- app branding values
- selected note/folder state
- panel visibility state
- controller references or adapter objects
- shell-level signals for save, selection, import/export, and app commands

## FolderPanel.qml

Owns folder tree/list presentation.

Likely needs:

- `folderController.folders`
- `folderController.currentFolderId/currentFolderName`
- folder selection/create/rename/delete/move/toggle actions
- folder import/export entry actions
- smart-folder display policy

Signals to expose upward:

- folder selected
- create folder requested
- rename/delete/move requested
- import/export requested

## NoteListPanel.qml

Owns note list presentation, sorting/filtering/search controls, batch selection, and note actions.

Likely needs:

- `noteController.filteredNotes`
- selected note id
- batch selection state
- create/select/delete/pin/move note actions
- note count and pagination/load-more state

Signals to expose upward:

- note selected
- new note requested
- delete requested
- pin toggled
- batch action requested

## EditorPanel.qml

Owns current editor display, `WebNoteEditor`, tag row, tabs, save status, and editor zoom/mode state.

Likely needs:

- `selectedNoteId`
- `currentNote`
- `noteController.saveStatus`
- `isDraftNewNote`
- editor mode/zoom
- tag update actions
- export current note action

High-risk signals:

- `contentUpdated`
- `requestAutosave`
- `requestFlush`
- `requestExportCurrentNote`
- `pdfExportFinished`

## CommandDialogs.qml

Owns modal/dialog state for import/export/template/folder settings/delete failures and command overlays.

Likely needs:

- `folderImportController`
- `currentExportController`
- `templateController`
- status message/progress values
- output directory/path values

Signals to expose upward:

- import directory selected
- export requested
- template selected/updated
- dialog dismissed

## AppHeaderArea.qml

Owns branded header area and top-level command buttons.

Likely needs:

- `appName`
- `appLogoPath`
- sync/import/export/note-management signals
- active library information if shown

## Cross-area signal flow

- Header command signals route to `AppShell`, then to panels/dialogs.
- Folder selection triggers note list refresh and editor selection reset.
- Note selection updates `EditorPanel` current note.
- Editor autosave signals route to shell-level save helper or controller adapter.
- Import/export progress signals update `CommandDialogs` and may refresh folder/note panels.

## Fragile references to map before splitting

- `window.currentNote`
- `window.selectedNoteId`
- `window.openTabs`
- `window.isDraftNewNote`
- `window.flushSaveIfDirty()`
- `notesListView`, `foldersListView`, `libraryRepeater`
- export/import status properties
- template dialog properties
- batch note/folder move properties
- tag row and editor id `noteEditor`

These references should be replaced by explicit properties/signals only after regression tests exist.
