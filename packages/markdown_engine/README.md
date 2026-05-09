# Markdown Engine Boundary

`packages.markdown_engine` is the planned boundary for markdown/editor payload logic in Note2.

## Purpose

This package will eventually collect reusable markdown/editor behavior shared by the pure markdown editor, AI work editor, and future specialized editors.

## Current implementation locations

The real implementation is currently distributed across several areas:

- `editor-src/src/App.jsx`: React/Tiptap editor, markdown/json payload creation, editor mode switching, `window.editorAPI`.
- `editor-src/src/extensions/ImagePaste.js`: clipboard image paste handling with data URLs.
- `editor-src/src/extensions/ResizableImage.jsx`: Tiptap image node extension and resize attributes.
- `qml/components/WebNoteEditor.qml`: Qt WebEngine bridge, JavaScript console message handling, QML autosave timer, `runJavaScript` calls.
- `qml/Main.qml`: editor signal handling, local note cache updates, save flush orchestration.
- `controllers/note_controller.py`: deferred save state, save version tracking, data URL tokenization, `note-image://` hydration.
- `services/image_service.py`: local image file to data URL conversion.
- `services/current_note_export_service.py`: markdown export normalization and embedded image handling.
- `assets/editor/index.html`: built WebEngine editor asset loaded by QML.

## Current phase

This is a documentation/compatibility boundary phase. No conversion logic, payload shaping logic, image token logic, editor bridge logic, or autosave logic has been moved.

## Future separation candidates

- markdown/html/json payload normalization
- editor payload validation
- image data URL tokenization and `note-image://` hydration helpers
- markdown export normalization
- table/image/link handling helpers
- bridge contract validation between React, QML, and Python

## Stability rule

Existing behavior must not change while this package is introduced. In particular, do not change `REQUEST_SAVE`, `REQUEST_FLUSH`, `window.__editorLastPayload`, `window.editorAPI`, `note-image://`, Tiptap markdown output, QML signal names, or `NoteController` save semantics without dedicated migration tests.
