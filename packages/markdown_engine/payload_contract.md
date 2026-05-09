# Editor Payload Contract

This document describes the current payload contract between the React/Tiptap editor, QML WebEngine bridge, QML application shell, and Python `NoteController`.

## Producer

The primary payload producer is `editor-src/src/App.jsx`.

In WYSIWYG mode, `buildPayload(ed)` creates:

```js
{
  markdown: string,
  json: string,
  title: string,
  text: string
}
```

In Markdown mode, `buildMarkdownPayload(markdownText)` creates the same shape, but `json` is an empty string.

## Fields

- `markdown`: canonical markdown content for note storage and export. In WYSIWYG mode it comes from `ed.storage.markdown.getMarkdown()`, falling back to plain text if conversion fails.
- `json`: serialized Tiptap/ProseMirror JSON from `JSON.stringify(ed.getJSON())`. This is used for high-fidelity editor restoration. It is empty in raw Markdown mode.
- `title`: derived from the first meaningful text line. Markdown header/list/emphasis markers are stripped and the result is truncated to 100 characters.
- `text`: plain text representation. It is mainly used inside the editor payload, not directly saved by QML/Python.

No `html` field is currently part of `window.__editorLastPayload`. HTML is available through `editorAPI.getHTML()` and is used by PDF/export-related paths when requested separately.

## Publishing

`App.jsx` stores the latest payload in:

```js
window.__editorLastPayload
```

Important publishing functions:

- `publishPayload(ed)`: WYSIWYG payload.
- `publishMarkdownPayload()`: raw Markdown payload.
- `publishActivePayload(ed)`: mode-aware payload.

## QML bridge read path

`qml/components/WebNoteEditor.qml` reads the payload by running JavaScript:

```js
JSON.stringify(window.__editorLastPayload || {})
```

It then emits:

```qml
contentUpdated(payload.title || "", payload.markdown || "", payload.json || "")
```

## QML application shell handling

`qml/Main.qml` receives `onContentUpdated(newTitle, newMarkdown, newJson)` and updates the in-memory `window.currentNote` fields:

- `currentNote.title`
- `currentNote.content`
- `currentNote.content_json`

This update is intentionally local. Actual DB writes occur through `flushSaveIfDirty()`.

## Python save path

`flushSaveIfDirty()` calls:

```qml
noteController.updateNoteWithJson(noteId, title, liveMarkdown, liveJson)
noteController.saveCurrentNote()
```

`NoteController.updateNoteWithJson()` does not immediately write to DB. It:

- updates `_current_note_id`
- compares title/content/json against `_current_note_data`
- stores changed values in `_pending_title`, `_pending_content`, `_pending_json`
- bumps `_edit_version`
- marks save status dirty

`saveCurrentNote()` delegates to `_perform_save()`, which asynchronously persists the pending snapshot.

## Autosave flow

1. React editor updates payload during typing.
2. React schedules its internal debounce and emits `REQUEST_SAVE` through `console.log`.
3. `WebNoteEditor.qml` catches `REQUEST_SAVE` in `onJavaScriptConsoleMessage`.
4. QML reads `window.__editorLastPayload`.
5. QML emits `contentUpdated(...)`.
6. QML `autosaveTimer` restarts.
7. When the timer fires, `requestAutosave()` is emitted.
8. `Main.qml` handles `onRequestAutosave` with `flushSaveIfDirty()`.

## Flush save flow

1. QML-injected focusout hook emits `REQUEST_FLUSH` through `console.log`.
2. `WebNoteEditor.qml` reads the latest payload.
3. QML emits `contentUpdated(...)` if payload fields exist.
4. QML stops `autosaveTimer`.
5. QML emits `requestFlush()`.
6. `Main.qml` handles `onRequestFlush` with `flushSaveIfDirty()`.

## Document loading and switching

`WebNoteEditor.qml` calls:

```js
window.editorAPI.setContent(window.__loadMd, window.__loadJson, window.__loadNoteId)
```

`App.jsx` handles `setContent(markdown, jsonStr, noteId, isNewNote)`:

- if the same note id is loaded again, it avoids resetting content to preserve focus/cursor.
- for existing notes, JSON is preferred and markdown is fallback.
- for new notes, editor content is cleared and new-note flags are set.

## Fields and names that must not change casually

- `window.__editorLastPayload`
- `payload.markdown`
- `payload.json`
- `payload.title`
- `payload.text`
- `contentUpdated(title, markdown, json)`
- `currentNote.content`
- `currentNote.content_json`
- `noteController.updateNoteWithJson(noteId, title, content, content_json)`
- `noteController.saveCurrentNote()`
