# Save Coordinator Plan

This document describes the current save flow. No save logic is moved in this step.

## Current save flow

Primary entry points:

- `updateNoteWithJson(note_id, title, content, content_json)`
- `saveCurrentNote()`
- `_perform_save()`
- `_start_async_note_update(...)`
- `_on_async_save_finished(ok)`

The editor sends the latest title, markdown, and JSON payload to `updateNoteWithJson`. This updates an in-memory mirror and marks the note dirty without immediately writing to the database.

`saveCurrentNote()` delegates to `_perform_save()`. `_perform_save()` builds a snapshot from pending data, tokenizes images, and starts async persistence.

## Autosave flow

1. QML/WebNoteEditor reports content changes.
2. `Main.qml` or editor bridge calls `noteController.updateNoteWithJson(...)`.
3. `NoteController` updates `_pending_title`, `_pending_content`, `_pending_json`.
4. `_edit_version` increments when content changed.
5. `_is_dirty` becomes true and `_save_status` becomes `dirty`.
6. QML receives `saveStatusChanged`.
7. Debounced autosave calls `saveCurrentNote()`.
8. `_perform_save()` creates a save snapshot and starts async worker.

## Flush save flow

Flush save is triggered by explicit save, focusout, or document switching logic in QML.

Important behavior:

- It must save the latest editor payload, not a stale controller snapshot.
- It must not cause editor re-render/cursor reset.
- It must preserve pending JSON and markdown together.

## Document transition save flow

`selectNote(...)` checks the current note before switching:

- If current note is effectively empty, it can hard-delete the draft.
- If current note is dirty, it calls `saveCurrentNote()` before selecting the next note.
- Then it loads the selected note and resets current state.

This is high risk because note switching and data safety interact directly.

## Save worker flow

- `_NoteSaveWorker` receives database path, note id, title, content, and content JSON.
- `_start_async_note_update(...)` starts a `QThread` and worker.
- Worker writes through `NoteService.update(...)` in a background thread.
- Worker emits `finished(bool)`.
- `_on_async_save_finished(...)` clears worker/thread references and updates save state.

## Version tracking flow

Important fields:

- `_edit_version`: incremented when a new edit arrives.
- `_last_saved_version`: last version confirmed as saved.
- `_inflight_version`: version represented by the currently running save snapshot.

When a save finishes, the controller checks whether new pending data or version drift exists. If so, it immediately schedules/continues another save.

## Dirty/pending/in-flight state meanings

- `_is_dirty`: current editor data differs from persisted state or needs saving.
- `_is_saving`: async save is currently running.
- `_save_pending`: a save was requested while another save is in progress.
- `_save_queued`: another save should run after the current one.
- `_pending_title`: pending title snapshot, if changed.
- `_pending_content`: pending markdown snapshot, if changed.
- `_pending_json`: pending editor JSON snapshot, if changed.
- `_save_status`: QML-visible status such as dirty/saving/saved/error.

## Dangerous variables and methods

Do not modify casually:

- `_perform_save`
- `_start_async_note_update`
- `_on_async_save_finished`
- `_edit_version`
- `_last_saved_version`
- `_inflight_version`
- `_save_pending`
- `_save_queued`
- `_pending_title`
- `_pending_content`
- `_pending_json`
- `updateNoteWithJson`
- `saveCurrentNote`

## SaveCoordinator extraction plan

1. Write characterization tests for existing `NoteController` save behavior.
2. Extract a pure `DirtyStateTracker` with no DB/thread dependency.
3. Extract snapshot-building logic while keeping `_perform_save` as caller.
4. Extract tokenization behind an `ImageTokenService` interface.
5. Extract save sequencing into `SaveCoordinator` while `NoteController` still owns PyQt signals.
6. Move PyQt worker/thread orchestration behind an adapter if needed.
7. Keep QML slots and signals unchanged until compatibility is proven.

## Required tests before extraction

- edit marks dirty and emits save status
- autosave persists title/content/json
- flush save persists latest editor payload
- note switching saves dirty note
- edits during in-flight save are not lost
- save failure leaves recoverable dirty/pending state
- title-only edit updates note list row without full editor rebind
- content-only edit does not trigger disruptive list/editor refresh
