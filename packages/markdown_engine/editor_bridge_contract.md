# Editor Bridge Contract

This document describes the current bridge between `qml/components/WebNoteEditor.qml`, the React/Tiptap editor, `qml/Main.qml`, and Python `NoteController`.

## Bridge mechanism

The bridge currently uses Qt WebEngine JavaScript execution and JavaScript console messages.

- QML loads `assets/editor/index.html` in `WebEngineView`.
- QML calls editor methods with `webView.runJavaScript(...)`.
- React/Tiptap exposes methods through `window.editorAPI`.
- React/Tiptap emits events to QML by calling `console.log(...)` with specific message strings.
- `WebNoteEditor.qml` handles those strings in `onJavaScriptConsoleMessage`.

No dedicated QWebChannel object API is the primary payload transport in the current flow.

## `REQUEST_SAVE`

`REQUEST_SAVE` means the editor has updated content and QML should read the latest payload and schedule a debounced autosave.

Flow:

1. React calls `publishActivePayload()` or `publishPayload()`.
2. React stores the result in `window.__editorLastPayload`.
3. React logs `REQUEST_SAVE`.
4. QML catches the message.
5. QML runs `JSON.stringify(window.__editorLastPayload || {})`.
6. QML emits `contentUpdated(title, markdown, json)`.
7. QML restarts `autosaveTimer`.
8. Timer emits `requestAutosave()`.
9. `Main.qml` calls `flushSaveIfDirty()`.

## `REQUEST_FLUSH`

`REQUEST_FLUSH` means focus left the editor and QML should save immediately instead of waiting for debounce.

Flow:

1. QML injects a focusout hook into the editor document after load.
2. If focus leaves the editor, injected JS logs `REQUEST_FLUSH`.
3. QML asks `window.editorAPI.onContentChanged()` if present, then reads `window.__editorLastPayload`.
4. QML emits `contentUpdated(...)` if payload fields exist.
5. QML stops `autosaveTimer`.
6. QML emits `requestFlush()`.
7. `Main.qml` calls `flushSaveIfDirty()`.

Note: the current React `editorAPI` does not define `onContentChanged`; QML calls it defensively.

## `window.__editorLastPayload`

This global stores the most recent editor payload. It avoids passing large markdown/json payloads through console logs.

Current expected shape:

```js
{
  markdown: string,
  json: string,
  title: string,
  text: string
}
```

## `window.editorAPI` methods observed in `App.jsx`

Core content/payload methods:

- `setContent(markdown, jsonStr, noteId, isNewNote)`
- `promoteToSaved(noteId)`
- `setMarkdown(markdown)`
- `getMarkdown()`
- `getJSON()`
- `getHTML()`
- `getTitle()`
- `getPayload()`
- `flushNow()`
- `requestExport()`

Insertion/focus methods:

- `insertImage(src)`
- `insertMarkdownAtCursor(markdown)`
- `focus()`

Formatting/mode methods:

- `formatBold()`
- `formatItalic()`
- `formatHeading()`
- `formatCode()`
- `insertTable(rows, cols)`
- `insertBulletList()`
- `insertNumberedList()`
- `insertHorizontalRule()`
- `insertQuote()`
- `insertLink()`
- `setMode(mode)`
- `getMode()`

## QML wrapper methods

`WebNoteEditor.qml` provides QML-facing helper methods:

- `setEditorContent(md, json)`
- `setMarkdownContent(md)`
- `getMarkdown(callback)`
- `getCurrentHtml(callback)`
- `exportCurrentPdf(outputPath)`
- `prepareForPdf()`
- `restoreAfterPdf()`
- editor mode sync helpers

## QML timer relation

There are two debounce layers:

- React has `SAVE_DEBOUNCE_MS = 1500` for editor-side save event scheduling.
- QML `autosaveTimer` has `interval: 1200` and fires `requestAutosave()` after QML receives a save request/payload.

The two layers must be treated carefully because changing either timing can affect stale payload/race behavior.

## Python save handoff

`Main.qml` receives editor signals and calls:

```qml
noteController.updateNoteWithJson(noteId, title, markdown, json)
noteController.saveCurrentNote()
```

`NoteController` handles deferred save state and async persistence.

## Names that must not change without migration tests

- Console messages: `REQUEST_SAVE`, `REQUEST_FLUSH`, `REQUEST_CREATE_NOTE`, `REQUEST_EXPORT_CURRENT_NOTE`, `EDITOR_CONTENT_CHANGED:__PAYLOAD_READY__`
- Globals: `window.__editorLastPayload`, `window.editorAPI`, `window.__loadMd`, `window.__loadJson`, `window.__loadNoteId`
- Signals: `contentUpdated`, `requestAutosave`, `requestFlush`, `requestExportCurrentNote`, `pdfExportFinished`
- Python slots: `updateNoteWithJson`, `saveCurrentNote`, `saveLocalImage`, `getNote`
- Editor API methods listed above
