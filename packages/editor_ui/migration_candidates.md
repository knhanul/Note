# Editor UI Migration Candidates

## Too risky to move immediately

- `qml/Main.qml`: owns app state, controller connections, save orchestration, dialogs, panels, and many ids.
- `qml/components/WebNoteEditor.qml`: bridges QML, QtWebEngine, React/Tiptap, autosave, PDF export, image insertion, and editor mode sync.
- editor content area inside `Main.qml`: tightly coupled to `currentNote`, `selectedNoteId`, `isDraftNewNote`, tab updates, tags, and save flushing.
- import/export dialog areas: coupled to controller progress signals and window-level status properties.
- folder/note management overlays: coupled to batch selection, move targets, and controller slot semantics.

## First theme candidates

Theme files are good early candidates once QML module import compatibility is designed:

- `qml/theme/Colors.qml`
- `qml/theme/Metrics.qml`
- `qml/theme/Typography.qml`
- `qml/theme/qmldir`

They should move only if `import theme` remains valid or a compatibility import path is retained.

## First simple component candidates

Likely safer after theme path compatibility:

- `GlassCard.qml`
- `TagChip.qml`
- `SaveStatusChip.qml`
- `NotebookItem.qml`
- `SidebarSection.qml`
- `EditorToolbar.qml`
- `NoteListItem.qml` after confirming its signals cover all app behavior

`FolderItem.qml` should wait until its direct `folderController` dependency is removed or adapted.

## Main.qml split order

A safer future split sequence:

1. Extract read-only visual/status dialogs that do not own save state.
2. Extract `CommandDialogs.qml` for import/export/template/folder dialogs while keeping properties passed from `Main.qml`.
3. Extract `AppHeaderArea.qml` as a thin wrapper around `AppHeader`.
4. Extract `FolderPanel.qml` with explicit controller/model/action properties.
5. Extract `NoteListPanel.qml` with explicit note model, selection, batch, and action signals.
6. Extract `EditorPanel.qml` only after WebNoteEditor and save flow tests exist.
7. Introduce `AppShell.qml` last, after panels are stable.

## Required tests before moving QML

- app starts and loads `Main.qml`
- `import theme` works
- `import components` works
- folder list renders and selection works
- note list renders and selection works
- editor loads WebEngine and keeps autosave behavior
- note switching does not lose content
- image notes hydrate correctly
- import/export dialogs open and controller progress signals update UI
- Ctrl+S still flushes save
- tag add/remove behavior remains stable

## QML import path strategy

Do not change `engine.addImportPath(str(config.qml_import_path))` until a compatibility plan exists.

A future migration can add an additional import path for `packages/editor_ui/qml`, but should keep the original `qml/` path during the transition.

## Compatibility strategy

- Keep old `qml/components` and `qml/theme` paths while new packages are introduced.
- Move one simple component at a time, then leave wrapper/qmldir compatibility if needed.
- Avoid renaming modules from `theme` and `components` during the first migration.
- Use explicit property/signal adapters instead of direct global controller dependencies in shared components.
