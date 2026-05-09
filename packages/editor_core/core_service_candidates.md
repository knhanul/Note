# Core Service Candidates

## SaveCoordinator

- Purpose: coordinate dirty state, pending editor payloads, in-flight save snapshots, version tracking, and save retries.
- Current location: `NoteController._perform_save`, `_start_async_note_update`, `_on_async_save_finished`, `updateNoteWithJson`, `saveCurrentNote`.
- Depends on: `NoteService`, database path, image tokenization step, worker/thread adapter.
- QML dependency: should not depend on QML after extraction.
- DB dependency: indirect; final persistence uses `NoteService`.
- Priority: High.
- Difficulty: High.
- Tests needed first: autosave, flush save, note switch save, edit-during-save, save failure.

## ImageTokenService

- Purpose: convert data URLs to `note-image://` tokens, hydrate tokens back to data URLs, and cleanup unused images.
- Current location: `NoteController._store_data_urls_and_tokenize`, `_hydrate_image_tokens`, `_extract_tokens`, image-related slots.
- Depends on: `NoteService` note image methods, `ImageService` for local/clipboard conversion.
- QML dependency: no for tokenization/hydration; local image slot remains adapter-facing.
- DB dependency: yes, through `note_images` methods.
- Priority: High.
- Difficulty: High.
- Tests needed first: tokenization, hydration, cleanup, missing image rows, copy/export interactions.

## NoteFilterService

- Purpose: apply search, sort, tag, date, smart-folder, and subfolder filters to note lists.
- Current location: `NoteController._load_first_page`, `loadMoreNotes`, `_apply_sort_and_filter`, tag filtering branches.
- Depends on: `NoteService`, `FolderController.getDescendantIds` or folder tree service.
- QML dependency: none after extraction.
- DB dependency: yes through `NoteService`, but some filtering is client-side.
- Priority: Medium.
- Difficulty: Medium.
- Tests needed first: filter combinations, pagination, smart all/favorites, include subfolders.

## NoteSelectionState

- Purpose: hold current note id/data and selection transitions separate from controller signals.
- Current location: `_current_note_id`, `_current_note_data`, `selectNote`, `currentNoteId`, `getNote`.
- Depends on: selected note payload from `NoteService`.
- QML dependency: no after extraction.
- DB dependency: indirect.
- Priority: High.
- Difficulty: High because save-on-switch coupling is strong.
- Tests needed first: note switching, pending save preservation, empty draft cleanup.

## FolderSelectionState

- Purpose: hold current folder id, smart-folder selection, and last-selected folder restore.
- Current location: `FolderController._current_folder_id`, `currentFolderId`, `selectFolder`, `_on_library_changed`.
- Depends on: `SettingsService`, folder existence checks.
- QML dependency: no after extraction.
- DB dependency: indirect through `FolderService.exists`.
- Priority: Medium.
- Difficulty: Medium.
- Tests needed first: library switch restore, deleted folder fallback, smart-folder selection.

## DirtyStateTracker

- Purpose: represent dirty/saving/pending/queued/version status as explicit state transitions.
- Current location: `NoteController` save fields.
- Depends on: none if pure.
- QML dependency: no.
- DB dependency: no.
- Priority: High.
- Difficulty: Medium to High.
- Tests needed first: state transition table for edits, save start, save finish, save failure.

## PaginationState

- Purpose: track offset, limit, loaded notes, and load-more behavior.
- Current location: `_pagination_offset`, `_pagination_limit`, `_loaded_notes`, `_load_first_page`, `loadMoreNotes`.
- Depends on: note query provider.
- QML dependency: no.
- DB dependency: indirect.
- Priority: Medium.
- Difficulty: Medium.
- Tests needed first: first page, load more, reset on filter/folder changes.

## TagCoordinator

- Purpose: manage selected tag, tag counts, hierarchical tag matching, and tag updates.
- Current location: `selectedTag`, `allTags`, `selectTag`, `clearTagFilter`, `updateNoteTags`.
- Depends on: `NoteService`.
- QML dependency: no after extraction.
- DB dependency: yes.
- Priority: Medium.
- Difficulty: Medium.
- Tests needed first: tag filtering, update note tags, tag tree counts.

## TemplateApplyService

- Purpose: render templates and apply default folder template policy when creating notes.
- Current location: `TemplateController.renderTemplate`, `TemplateService.render_template_fields`, `FolderController.getFolderDefaultTemplateId`, note creation flow in QML/controller.
- Depends on: `TemplateService`, `FolderService`.
- QML dependency: no after extraction.
- DB dependency: yes.
- Priority: Low to Medium.
- Difficulty: Medium.
- Tests needed first: default template lookup, variable rendering, template deletion clearing folder defaults.

## DocumentCommandService

- Purpose: app-independent note commands such as create, duplicate/copy, move, delete, pin, and maybe export handoff.
- Current location: `NoteController` CRUD/batch methods and `CurrentExportController` scope mapping.
- Depends on: `NoteService`, `FolderService`, `ImageTokenService` for copies with images.
- QML dependency: no after extraction.
- DB dependency: yes.
- Priority: Medium.
- Difficulty: High.
- Tests needed first: batch operations, folder moves, copy with image payloads, signals expected by QML adapter.
