# Image Token Service Plan

This document describes the current image flow. No image logic is moved in this step.

## Image insertion flow

Current entry points:

- `WebNoteEditor.qml` can request local image insertion through `noteController.saveLocalImage(...)`.
- `NoteController.saveBase64Image(...)` normalizes base64 payloads to data URLs.
- `NoteController.pasteImageFromClipboard(...)` reads a clipboard image, converts it to a data URL, inserts markdown, and reuses `updateNote(...)`.
- `ImageService` performs image-to-data-URL and markdown insertion helpers.

The editor receives data URLs for immediate rendering. Tokenization happens later during save.

## Data URL handling

Current patterns:

- `_DATA_URL_PATTERN` detects base64 image data URLs in markdown and JSON.
- `saveLocalImage(...)` returns a data URL loaded from a local file.
- `saveBase64Image(...)` returns a normalized data URL.
- `getImageDataUrl(...)` returns a data URL for preview/loading helpers.

Data URLs are editor-facing payloads before persistence normalization.

## note-image:// token handling

Current patterns:

- `_TOKEN_PATTERN` detects `note-image://<image_id>` references.
- `_store_data_urls_and_tokenize(...)` replaces data URLs with note-image tokens before note row persistence.
- `_hydrate_image_tokens(...)` replaces tokens with data URLs for editor rendering.

Tokens are persistence-facing references stored in note markdown/JSON.

## note_images table relationship

`NoteController` uses `NoteService` methods related to note images:

- `upsert_note_image(...)`
- `get_note_image(...)`
- `delete_unused_note_images(...)`

The note row stores tokenized markdown/JSON. The binary payload is represented as base64 data in `note_images` rows.

## Hydration flow

1. QML requests a note through `noteController.getNote(note_id)`.
2. `NoteController` loads the note via `NoteService.get_by_id(...)`.
3. Markdown and JSON fields are passed through `_hydrate_image_tokens(...)`.
4. Tokens are replaced with data URLs.
5. QML/WebNoteEditor receives editor-renderable payload.

## Tokenization flow

1. Editor changes arrive as markdown/json with possible data URLs.
2. Save is requested through `saveCurrentNote()`.
3. `_perform_save()` calls `_store_data_urls_and_tokenize(...)` before dispatching worker save.
4. Each data URL is hashed and upserted through `NoteService.upsert_note_image(...)`.
5. Content/JSON store `note-image://<image_id>` tokens.
6. Unreferenced images are removed through `delete_unused_note_images(...)`.

## Export relationship

Current-note export receives live editor payload from QML/WebNoteEditor and `CurrentExportController`. Folder/batch export reads notes from services.

Risk points:

- Export may need hydrated images depending on format and service expectations.
- Moving tokenization without export tests can break image rendering in exported files.
- Markdown and JSON must remain consistent.

## ImageTokenService extraction plan

1. Add tests for `NoteController` image hydration/tokenization behavior using a temporary database.
2. Extract regex constants and token extraction into pure helper functions.
3. Extract data URL replacement into `ImageTokenService` while still called from `NoteController`.
4. Keep `NoteService` note image methods as storage boundary.
5. Keep clipboard/local file functions in adapter layer or `ImageService`; do not put QApplication/QImage dependencies in pure core.
6. Update export paths only after tests document whether they expect hydrated data URLs or tokens.

## Required tests before extraction

- local image insert returns data URL to WebNoteEditor
- base64 image normalize returns data URL
- save converts data URLs to tokens
- opening a note hydrates tokens back to data URLs
- markdown and JSON tokenization both work
- unused image cleanup preserves referenced images only
- missing image token hydrates safely
- image-containing note export still works
- note copy/move/delete interactions keep image data valid
