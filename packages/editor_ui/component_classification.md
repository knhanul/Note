# Component Classification

## A. Fully common UI candidates

These are mostly property/signal driven and can likely move first after import path compatibility is planned:

- `GlassCard.qml`: visual container.
- `TagChip.qml`: generic tag/chip component with clicked/removed signals.
- `SaveStatusChip.qml`: generic save status display.
- `NotebookItem.qml`: simple notebook/folder-like item.
- `SidebarSection.qml`: reusable sidebar section/list pattern.
- `EditorToolbar.qml`: common formatting toolbar, if actions remain signal-based.
- `qml/theme/Colors.qml`, `Metrics.qml`, `Typography.qml`: shared design tokens.

## B. Common UI candidates requiring adapters

These can be shared but need explicit data/action adapters instead of direct controller coupling:

- `WebNoteEditor.qml`: common editor panel, but depends on WebEngine, React/Tiptap bridge, `noteController.saveLocalImage`, PDF export, editor mode sync, and autosave signals.
- `NoteListItem.qml`: common row component, but app-specific actions may vary.
- `FolderItem.qml`: common folder row, but currently has direct `folderController` connection for rename mode.
- Future NoteList/FolderTree panels extracted from `Main.qml`: should accept models/actions as properties.
- Export/import dialog areas currently embedded in `Main.qml`: should be extracted behind controller/service adapters.

## C. App-specific UI candidates

These should stay in an app shell or app-specific layer:

- app brand header composition and logo choices
- app-specific side panels
- AI assistant panels for `work_ai_editor`
- domain-specific editor panels for `special_editor`
- app-specific menu and command composition
- workflow-specific import/export messages or specialized dialogs
- smart-folder presentation policy if app-specific

## D. Dangerous to move now

- `Main.qml`: too many global ids, window properties, dialogs, controller calls, and cross-panel references.
- `WebNoteEditor.qml`: tightly coupled to WebEngine/React bridge and autosave flow.
- editor panel section inside `Main.qml`: coupled to `flushSaveIfDirty`, draft creation, tab title updates, and `currentNote` mutation.
- import/export dialog sections inside `Main.qml`: coupled to progress state, controller signals, and output paths.
- note/folder batch management overlays: coupled to selection state and controller slots.

## Recommended near-term stance

Keep QML in place. Treat `packages.editor_ui` as documentation until simple components and theme files have import-path compatibility tests.
