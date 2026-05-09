# Editor Adapters

`packages.editor_core.adapters` defines the future adapter boundary for editor implementations.

## Purpose

The `EditorAdapter` contract describes operations that app-specific editor surfaces may eventually provide:

- read content
- set content
- save
- focus
- insert image
- insert table
- export markdown
- subscribe to content changes

## Why WebNoteEditor is not replaced now

The existing `WebNoteEditor.qml`, React/Tiptap bridge, and `NoteController` autosave flow are tightly coupled and high-risk. Replacing them before characterization tests and EditorPanel separation could break autosave, image tokenization, focus handling, or QML signal flows.

## MarkdownEditorAdapter

`MarkdownEditorAdapter` represents the existing markdown editor surface for future integration. It is currently a stub and does not access QML, WebEngine, or `NoteController`.

## CustomEditorAdapter

`CustomEditorAdapter` represents future special-purpose editors such as business form editors, workflow editors, or domain-specific document tools. It is currently a stub and is not used by runtime.

## Future editor directions

Possible future adapters:

- existing WYSIWYG markdown editor adapter
- Milkdown editor adapter
- business form editor adapter
- AI conversational editor adapter
- read-only preview/editor hybrid adapter

## Autosave caution

Do not directly couple new adapters to `NoteController` autosave internals until the save coordinator boundary is tested. The current save flow depends on pending fields, version counters, async workers, and image tokenization state.

## Required tests before runtime connection

- adapter contract tests
- WebNoteEditorAdapter characterization tests
- autosave flush tests
- image insertion/tokenization tests
- focus and content changed event tests
- export markdown consistency tests

## Future steps

1. adapter contract tests
2. WebNoteEditorAdapter implementation
3. EditorPanel separation
4. app-specific adapter selection
5. special_editor-specific UI connection
