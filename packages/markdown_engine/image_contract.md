# Image Contract

This document describes the current image flow across the React editor, QML bridge, Python controller, storage, and export paths.

## Image paste in the editor

`editor-src/src/extensions/ImagePaste.js` handles clipboard image paste inside Tiptap:

1. It inspects `event.clipboardData.items`.
2. For the first `image/*` item, it prevents the default paste.
3. It reads the image with `FileReader.readAsDataURL(file)`.
4. It inserts an image node with `src` set to the generated data URL.

The pasted image therefore enters the payload as a base64 `data:image/...;base64,...` URL.

## Resizable image extension

`editor-src/src/extensions/ResizableImage.jsx` extends Tiptap image support with `width` and `height` attributes. The `src` attribute remains the image source and can be a data URL or a hydrated data URL from storage.

## Local image file insertion

`qml/components/WebNoteEditor.qml` opens a `FileDialog` for image selection. On accept it calls:

```qml
noteController.saveLocalImage(root.noteId, filePath)
```

`NoteController.saveLocalImage()` delegates to `ImageService.load_image_file_as_data_url()`, which returns a PNG data URL. QML then calls:

```js
window.editorAPI.insertImage(window.__imgDataUrl)
```

## Data URL meaning

A data URL is the editor-facing representation of image bytes. It allows WebEngine/Tiptap to render the image immediately without a separate file URL.

## `note-image://` token meaning

`note-image://<image_id>` is the persisted content representation used to avoid storing large base64 image payloads directly inside note markdown/json after save.

The token points to a row in the `note_images` table.

## `note_images` table relationship

`services.database.Database.init_schema()` creates `note_images` with:

- `id`
- `note_id`
- `mime_type`
- `data_base64`
- `checksum`
- `created_at`

`services.note_service.NoteService` provides:

- `upsert_note_image(note_id, mime_type, data_base64, checksum)`
- `get_note_image(image_id)`
- `delete_unused_note_images(note_id, keep_image_ids)`

## Tokenization before save

`NoteController._perform_save()` calls `_store_data_urls_and_tokenize()` before dispatching the async DB update.

`_store_data_urls_and_tokenize(note_id, content, content_json)`:

1. Finds `data:image/...;base64,...` URLs in markdown and JSON.
2. Computes a checksum from mime type and base64 data.
3. Inserts or reuses the image row with `upsert_note_image()`.
4. Replaces the full data URL with `note-image://<image_id>`.
5. Extracts all remaining image tokens.
6. Deletes unused images for the note.
7. Returns tokenized markdown and tokenized JSON.

## Hydration for editor rendering

`NoteController.getNote(note_id)` fetches note content from DB, then calls `_hydrate_image_tokens()` for both:

- `content`
- `content_json`

`_hydrate_image_tokens()` replaces `note-image://<image_id>` with a data URL rebuilt from `note_images.mime_type` and `note_images.data_base64`.

The editor therefore receives data URLs even though DB content may store compact tokens.

## Export behavior

`services/current_note_export_service.py` handles export-time image behavior. Markdown export rewrites embedded data URL markdown images into image files next to the exported markdown and changes the markdown reference to the exported file name.

Folder/current export behavior was not changed by this markdown-engine boundary step.

## High-risk areas

- Changing `note-image://` format can break hydration and old notes.
- Changing data URL regex behavior can duplicate, delete, or lose images.
- Moving tokenization without tests can break async save snapshots.
- Failing to tokenize both markdown and JSON can desynchronize editor restore.
- Deleting unused images too early can remove still-referenced images.
- Changing export image rewriting can alter exported markdown output.
