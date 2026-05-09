# Editor Core Migration Candidates

## Dangerous to move immediately

- `NoteController._perform_save`
- `NoteController._start_async_note_update`
- `NoteController._on_async_save_finished`
- `NoteController.updateNoteWithJson`
- `NoteController.saveCurrentNote`
- all save state fields: `_edit_version`, `_last_saved_version`, `_save_pending`, `_pending_title`, `_pending_content`, `_pending_json`
- image tokenization/hydration methods
- `NoteController.selectNote` because of save-on-switch and empty-draft cleanup
- QML-facing signal/slot/property names in every controller
- import/export worker thread ownership

## Move only after tests

- note filtering/search/sort/pagination
- tag filtering and tag counts
- folder tree shaping and collapsed state
- smart folder policy
- note batch move/delete/copy commands
- template rendering/default template application
- import completion refresh behavior
- export scope mapping and progress relay behavior

## Relatively early pure candidates

- folder depth/tree helper functions after fixture tests
- dirty state transition model after characterization tests
- note filter criteria data object
- pagination state data object
- smart folder definitions moved to config/policy while preserving IDs
- template variable rendering if kept independent of QML

## Safe NoteController slimming order

1. Add characterization tests for save, selection, filters, tags, images, and batch commands.
2. Extract `DirtyStateTracker` as a pure state object.
3. Extract `NoteFilterService` for filtering/sorting/pagination without changing QML API.
4. Extract `ImageTokenService` behind existing private methods.
5. Extract `SaveCoordinator` while keeping `NoteController` as PyQt adapter.
6. Extract `NoteSelectionState` after save-on-switch tests pass.
7. Move document commands into `DocumentCommandService` after batch operation tests pass.

## Safe FolderController slimming order

1. Add tests for folder tree ordering, depth, smart folders, and delete/move rules.
2. Extract pure hierarchy helpers.
3. Extract `SmartFolderPolicy` from inline constants.
4. Extract `FolderSelectionState` while preserving `currentFolderId` and `currentFolderName` properties.
5. Move app policy such as default folder name/color and max depth into config/policy.
6. Keep `FolderController` as QML adapter until `editor_ui` shell is split.

## App config candidates

- smart folder names/colors and IDs, if compatibility remains stable
- default folder name and color
- folder max depth
- default sort field/order
- pagination limit
- include-subfolders default
- app-specific display strings

## Plugin API prerequisites

- stable document command interface
- stable selection state API
- stable save coordinator contract
- stable image token contract
- clear separation between QML adapter and editor core
- event/signal mapping that does not expose PyQt-only internals to plugin code

## apps/markdown_editor split prerequisites

- editor UI shell documented and gradually extracted
- controller context property names kept compatible or wrapped
- app state flow documented and tested
- save coordinator tests in place
- image token service tests in place
- folder/note selection tests in place
- import/export wrappers remain compatible
- storage paths and database schema unchanged
