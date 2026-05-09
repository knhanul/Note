# State Model Plan

## Current library state

Owner:

- `LibraryService`

Flow:

- `LibraryService.currentLibraryChanged` triggers controller reloads.
- `FolderController`, `NoteController`, and `TemplateController` recreate or refresh service objects for the current database.
- QML receives `libraryService` directly and controller signals indirectly.

Future candidate:

- `LibrarySelectionState` can remain in storage/app layer, while editor core consumes a current-library context.

## Current folder state

Owner:

- `FolderController._current_folder_id`
- persisted through `SettingsService`

Flow:

- QML calls `folderController.selectFolder(...)` or sets/reads properties.
- Folder selection emits `currentFolderChanged`.
- `NoteController` listens/collaborates with `FolderController` to reload filtered notes.

Future candidate:

- `FolderSelectionState`
- `SmartFolderPolicy`

## Current note state

Owner:

- `NoteController._current_note_id`
- `NoteController._current_note_data`

Flow:

- QML selects a note through `noteController.selectNote(...)`.
- `getNote(...)` returns hydrated content for editor display.
- `noteSelected` and list-refresh signals update QML.

Future candidate:

- `NoteSelectionState`
- `DocumentSessionState`

## Dirty state

Owner:

- `NoteController._is_dirty`
- `NoteController._save_status`

Flow:

- `WebNoteEditor.qml` and `Main.qml` call `updateNoteWithJson(...)` on content changes.
- `updateNoteWithJson(...)` marks dirty and emits `saveStatusChanged`.
- QML reads `saveStatus`, `isDirty`, and `isSaving`.

Future candidate:

- `DirtyStateTracker`

## Pending save state

Owner:

- `_pending_title`
- `_pending_content`
- `_pending_json`
- `_save_pending`
- `_save_queued`
- `_is_saving`
- `_edit_version`
- `_last_saved_version`
- `_inflight_version`

Flow:

- User edits update pending fields.
- Save creates an in-flight snapshot.
- Save completion checks whether newer edits arrived.

Future candidate:

- `SaveCoordinator`
- `SaveState`

## Note list state

Owner:

- `NoteController._loaded_notes`
- `NoteController._pagination_offset`
- `NoteController._pagination_limit`

Flow:

- Folder/tag/search/date/sort changes reset the loaded list.
- QML reads `filteredNotes` and triggers `loadMoreNotes()`.

Future candidate:

- `PaginationState`
- `NoteListState`

## Filter/search state

Owner:

- `_sort_field`
- `_sort_order`
- `_search_keyword`
- `_filter_from_date`
- `_filter_to_date`
- `_include_subfolders`

Flow:

- QML calls setter slots.
- Controller reloads notes and emits `filteredNotesChanged`.

Future candidate:

- `NoteFilterState`
- `NoteFilterService`

## Tag state

Owner:

- `NoteController._selected_tag`
- tag aggregation in `NoteService.get_all_tags()`

Flow:

- QML reads `allTags` and `selectedTag`.
- QML calls `selectTag`, `clearTagFilter`, or `updateNoteTags`.
- Controller emits `tagsChanged` and `filteredNotesChanged`.

Future candidate:

- `TagCoordinator`

## Template state

Owner:

- `TemplateController._template_service`
- QML dialog state in `Main.qml`

Flow:

- QML reads `templateController.templates`.
- QML calls template CRUD/render methods.
- Template changes emit `templatesChanged`.

Future candidate:

- `TemplateApplyService`
- app shell owns dialog state

## QML/Python state flow

Current pattern:

1. Python controllers expose Qt properties, slots, and signals.
2. `app_bootstrap.py` injects controllers as QML context properties.
3. `Main.qml` owns many UI-local states and calls controller slots.
4. Controllers mutate internal state and emit signals.
5. QML bindings/list models refresh from controller properties.

Risk:

- State is split between `Main.qml` and controllers.
- Save state crosses QML, WebEngine, React, and Python.
- Selection state and list state are coupled.

## Future AppState possibility

A future `AppState` should not be introduced as a giant global object immediately. Safer staged extraction:

1. Extract pure state data classes for selection and dirty state.
2. Keep PyQt controllers as adapters.
3. Add tests for state transitions independent of QML.
4. Gradually move orchestration from controllers into core services.
5. Only later introduce an app shell state object if it reduces coupling.
