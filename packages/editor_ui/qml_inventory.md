# QML Inventory

## Main.qml

`qml/Main.qml` is currently the application shell and orchestration center. It owns:

- top-level `Window`
- app-wide state such as `selectedNoteId`, `currentNote`, tabs, import/export status, template dialog state, batch note state, folder move state, editor zoom, draft-note state, and tag editing state
- global shortcut `Ctrl+S`
- save orchestration through `flushSaveIfDirty()`
- current-note export dialog state
- folder import/export workflows
- folder/note selection synchronization
- QML `Connections` to controllers
- folder panel, note list panel, editor panel, tag row, dialogs, overlays, and status feedback

`Main.qml` depends heavily on ids and mutable `window.*` properties. It should not be split until references are mapped and regression tests exist.

## Components

- `AppHeader.qml`: top application header. Uses `theme`. Emits app/header actions. Depends on app branding values passed from `Main.qml` or context-derived bindings.
- `EditorToolbar.qml`: formatting toolbar component. Uses `theme`. Emits formatting actions such as bold, italic, heading, code, link, image, table, lists, horizontal rule, quote.
- `FolderItem.qml`: folder tree/list item. Uses `theme`. Has folder properties and signals for click, rename, delete, move, expand/collapse. It has a direct `Connections` dependency on `folderController.folderAddedForRename`, making it less purely reusable than it appears.
- `GlassCard.qml`: visual container component. Uses `theme`. Mostly common UI.
- `NoteEditor.qml`: older/native note editor component. Uses `theme` and `components`. Has title/content/save/image-paste signals. Kept for compatibility.
- `NoteListItem.qml`: note list row component. Uses `theme`. Has note title/preview/date/tags/pin/selection state and emits click/selection/pin/delete signals. Good common candidate with adapter data.
- `SaveStatusChip.qml`: save status visual component. Uses `theme`. Common component.
- `TagChip.qml`: tag visual chip. Uses `theme`. Emits clicked/removed. Common component.
- `WebNoteEditor.qml`: WebEngine-based editor bridge. Uses `QtWebEngine`, `QtQuick.Dialogs`, `theme`, and `components`. Directly depends on global `noteController` for local image insertion and relies on the React editor bridge contract. High-risk component.

> Removed: `NotebookItem.qml` and `SidebarSection.qml` were deleted because they had no runtime usage.

## Theme files

- `Colors.qml`: singleton color tokens for primary/accent/background/surface/text/border/status/gradients.
- `Metrics.qml`: singleton spacing, radius, component sizing, shadow, animation duration tokens.
- `Typography.qml`: singleton font family, weight, size, line-height, letter-spacing tokens.

## Context property dependencies

Most global controller dependencies are in `Main.qml`. Notable component-level direct dependency:

- `WebNoteEditor.qml` uses `noteController.saveLocalImage(...)`.
- `FolderItem.qml` listens to `folderController.folderAddedForRename`.

Other components primarily receive data through properties and emit signals upward.

## Special risk markers

- `Main.qml`: very high risk because it mixes app shell, workflow orchestration, dialogs, note save flow, and many id references.
- `WebNoteEditor.qml`: very high risk because it bridges QML, WebEngine, React/Tiptap, autosave, image insertion, PDF export, and editor mode sync.
- `FolderItem.qml`: medium risk because of direct controller connection.
- `NoteListItem.qml`: medium risk because it participates in selection/batch/pin/delete flows but is property/signal oriented.
