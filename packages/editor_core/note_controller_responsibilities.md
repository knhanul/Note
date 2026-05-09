# NoteController Responsibilities

`NoteController` is currently the densest controller. It combines QML adapter API, current document state, filtering, save coordination, image tokenization, and note commands.

## A. QML bridge responsibility

Current location:

- `pyqtSignal` declarations near class top
- `pyqtProperty` declarations for note list, tags, save status, filters, and current note
- `pyqtSlot` methods for all note actions

Risk: High.

Future candidate:

- `NoteControllerAdapter` or `QmlNoteController`

Required tests:

- QML can read all existing properties.
- QML can call all existing slots with current signatures.
- Existing signals still trigger UI refresh.

Do not change now because context property and signal/slot names are direct QML API.

## B. Current note selection state

Current location:

- `_current_note_id`
- `_current_note_data`
- `currentNoteId`
- `selectNote`
- `getNote`

Risk: High.

Future candidate:

- `NoteSelectionState`
- `DocumentSessionState`

Required tests:

- selecting a note updates editor content
- switching notes preserves pending save behavior
- empty draft deletion behavior remains identical

Do not change now because selection interacts with autosave and QML document switching.

## C. Note CRUD

Current location:

- `createNote`
- `deleteNote`
- `moveNoteToFolder`
- `moveNotesToFolder`
- `copyNotesToFolder`
- `deleteNotes`
- `togglePinned`
- `isNotePinned`

Risk: Medium to High.

Future candidate:

- `DocumentCommandService`
- `NoteCommandService`

Required tests:

- create/delete/move/copy/pin operations update list, tags, and selection correctly
- smart-folder fallback behavior is preserved

Do not change now because these methods emit multiple QML refresh signals and encode folder policy.

## D. Autosave orchestration

Current location:

- `updateNoteWithJson`
- `saveCurrentNote`
- `_perform_save`
- `selectNote` when dirty

Risk: Very high.

Future candidate:

- `SaveCoordinator`

Required tests:

- content edits mark dirty without list re-render
- debounce-triggered save persists latest payload
- focusout/flush save persists latest payload
- note switch saves pending changes
- title-only edits refresh the list row only

Do not change now because autosave is central to data safety.

## E. Save worker/thread management

Current location:

- `_NoteSaveWorker`
- `_start_async_note_update`
- `_on_async_save_finished`
- `_save_thread`
- `_save_worker`

Risk: Very high.

Future candidate:

- `SaveWorkerRunner`
- PyQt-specific adapter around pure `SaveCoordinator`

Required tests:

- worker success path
- worker failure path
- edits arriving while save is in-flight
- thread cleanup after multiple saves

Do not change now because thread lifetime and signal ordering are fragile.

## F. Dirty/pending/in-flight state management

Current location:

- `_is_dirty`
- `_is_saving`
- `_save_pending`
- `_save_queued`
- `_save_status`
- `_pending_title`
- `_pending_content`
- `_pending_json`
- `_edit_version`
- `_last_saved_version`
- `_inflight_version`

Risk: Very high.

Future candidate:

- `DirtyStateTracker`
- `SaveState`

Required tests:

- every state transition during edit/save/finish/failure
- stale save snapshot detection
- no lost update when typing during save

Do not change now because these fields prevent data loss.

## G. Markdown/json payload handling

Current location:

- `updateNoteWithJson`
- `createNote`
- `_perform_save`
- `getNote`
- `_get_hydrated_note_dict`

Risk: High.

Future candidate:

- `EditorPayloadService`
- `DocumentPayloadNormalizer`

Required tests:

- markdown and TipTap JSON are saved together
- missing JSON remains backward-compatible
- title/content/json pending snapshots behave correctly

Do not change now because this is tied to `markdown_engine` and WebNoteEditor bridge contracts.

## H. Image tokenization/hydration

Current location:

- `_DATA_URL_PATTERN`
- `_TOKEN_PATTERN`
- `_store_data_urls_and_tokenize`
- `_hydrate_image_tokens`
- `saveBase64Image`
- `saveLocalImage`
- `pasteImageFromClipboard`
- `getImageDataUrl`

Risk: Very high.

Future candidate:

- `ImageTokenService`

Required tests:

- data URL to `note-image://` token conversion
- hydration back to data URL
- unused image cleanup
- copy note with images
- WebNoteEditor local image insertion

Do not change now because image persistence affects DB content and export behavior.

## I. Tag handling

Current location:

- `allTags`
- `selectedTag`
- `selectTag`
- `clearTagFilter`
- `updateNoteTags`
- tags-related refresh signals

Risk: Medium.

Future candidate:

- `TagCoordinator`
- part of `NoteFilterService`

Required tests:

- tag filter toggling
- hierarchical tag prefix filtering
- tag counts after note edits/deletes/imports

Do not change now because filtering, list refresh, and tag UI are coupled.

## J. Search/filter/pagination

Current location:

- `_loaded_notes`
- `_pagination_offset`
- `_pagination_limit`
- `_sort_field`
- `_sort_order`
- `_search_keyword`
- `_filter_from_date`
- `_filter_to_date`
- `_include_subfolders`
- `_load_first_page`
- `loadMoreNotes`
- `_apply_sort_and_filter`

Risk: Medium.

Future candidate:

- `NoteFilterService`
- `PaginationState`

Required tests:

- smart all/favorites filters
- folder and subfolder filtering
- tag + search + date + sort combinations
- infinite-scroll pagination

Do not change now because list behavior is visible in QML and easy to regress.

## K. Import/export linkage

Current location:

- note refresh signals consumed after import
- current note export data provided through QML/WebNoteEditor and `currentExportController`
- batch operations that affect export scopes

Risk: Medium.

Future candidate:

- `DocumentCommandService`
- import/export adapters remain outside core

Required tests:

- import refresh updates notes/tags/folders
- export current note gets latest editor payload
- folder/favorites/all scopes remain correct

Do not change now because import/export currently depends on controller signals and QML dialogs.

## L. App/UI policy

Current location:

- default note title behavior
- empty draft deletion policy
- smart-folder fallback when creating/moving notes
- formatted date display
- `showCalendarDialog`
- preview text formatting
- folder path display text

Risk: Medium.

Future candidate:

- `AppStatePolicy`
- `DocumentDisplayPolicy`
- app shell/config layer

Required tests:

- default titles
- empty draft cleanup
- calendar/date filter behavior
- display strings used in UI

Do not change now because these policies are mixed with QML-visible behavior.
