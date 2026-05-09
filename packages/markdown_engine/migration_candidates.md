# Markdown Engine Migration Candidates

This document lists future extraction candidates and risks. No runtime code was moved in the boundary-definition step.

## Too risky to move immediately

- `editor-src/src/App.jsx` save scheduling and `window.editorAPI` implementation.
- `qml/components/WebNoteEditor.qml` console-message bridge and QML autosave timer.
- `controllers/note_controller.py` `_perform_save()` async save/version tracking.
- `NoteController._store_data_urls_and_tokenize()` and `_hydrate_image_tokens()` without image regression tests.
- `Main.qml.flushSaveIfDirty()` because it coordinates draft creation, local cache, and controller save calls.
- Built assets under `assets/editor/` because they are runtime artifacts loaded by QML.

## Pure function candidates for later extraction

Candidates that appear separable after tests exist:

- title extraction logic from `App.jsx` `extractFirstLineTitle()`.
- markdown payload shape validation helpers.
- markdown-mode payload construction rules.
- data URL parsing helpers used by image tokenization.
- `note-image://` token parsing helpers.
- safe markdown image reference detection helpers.
- export markdown/table/html normalization helpers currently in `services/current_note_export_service.py`.

## Candidates that need tests before moving

- WYSIWYG markdown conversion expectations from `tiptap-markdown`.
- JSON-first restore behavior in `editorAPI.setContent()`.
- mode switching behavior between WYSIWYG and Markdown.
- focusout flush behavior.
- debounce save behavior and stale payload protection.
- image paste data URL persistence.
- tokenization of both markdown and JSON.
- hydration of both markdown and JSON when loading a note.
- export rewriting of data URL images into sidecar image files.

## Image tokenization/hydration plan

1. Add tests around current regex behavior for data URLs and `note-image://` tokens.
2. Extract token parsing and data URL parsing into pure helpers.
3. Keep DB access in storage/repository layer.
4. Introduce an adapter that receives image persistence functions instead of importing controllers.
5. Move `NoteController` to call the adapter only after output equivalence is proven.

## Markdown normalization plan

1. Document current Tiptap markdown output with sample notes.
2. Add golden tests for tables, images, links, task lists, headings, and raw HTML.
3. Extract export-only normalization helpers first because they are easier to test offline.
4. Avoid changing editor-side markdown generation until editor payload tests exist.

## Payload validation plan

1. Add a non-mutating validator for expected payload keys: `markdown`, `json`, `title`, `text`.
2. Validate types only; do not normalize or mutate payload initially.
3. Log validation failures in adapter layers once safe.
4. Introduce stricter validation only after compatibility coverage exists.

## Recommended sequence

1. Documentation boundary, placeholder package, import smoke test.
2. Golden tests for payload/image/export behavior.
3. Pure helper extraction with no controller/QML behavior changes.
4. Adapter introduction around QML/React/Python boundary.
5. Gradual migration of callers to `packages.markdown_engine`.
6. Remove legacy duplicates only after compatibility period.
