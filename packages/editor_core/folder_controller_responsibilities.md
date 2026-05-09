# FolderController Responsibilities

`FolderController` currently combines folder persistence orchestration, tree presentation shaping, current folder selection, smart-folder policy, and QML adapter API.

## Folder tree loading

Current location:

- `_on_library_changed`
- `_load_folders`
- `folders` property
- `_get_folder_depth`

Behavior:

- Recreates `FolderService` for the current library database.
- Loads regular folders from `FolderService.get_all()`.
- Enriches folder dicts with `note_count`, `depth`, and `has_children`.
- Builds parent-child ordering and hides descendants of collapsed folders.
- Prepends built-in smart folders.

Risk: High.

Reason:

- The `folders` property is both a data API and a QML presentation model.
- It mutates/enriches service data for UI rendering.

Future candidate:

- `FolderTreePresenter`
- `FolderTreeState`

## Folder creation/update/delete/move

Current location:

- `createFolder`
- `deleteFolder`
- `renameFolder`
- `moveFolder`
- `reorderFolder`
- `setFolderDefaultTemplate`

Behavior:

- Generates folder ids.
- Enforces max depth policy.
- Prevents deleting folders with children or notes.
- Prevents moving smart folders or moving folders under descendants.
- Emits QML refresh and operation signals.

Risk: Medium to High.

Future candidate:

- `FolderCommandService`
- `FolderPolicy`

Move only after tests cover hierarchy, depth limits, delete failure messages, and QML refresh signals.

## Current folder selection state

Current location:

- `_current_folder_id`
- `currentFolderId`
- `currentFolderName`
- `selectFolder`
- last folder restore via `SettingsService`

Behavior:

- Maintains selected folder id.
- Persists selected folder id in settings.
- Handles smart-folder display names.
- Emits `currentFolderChanged`.

Risk: High.

Future candidate:

- `FolderSelectionState`

Move only after tests cover library switching, settings restoration, smart-folder selection, and note list refresh.

## Smart folder policy

Current location:

- `SMART_FOLDER_PREFIX`
- `SMART_FOLDERS`
- `_is_smart_folder_id`
- `isSmartFolder`
- smart-folder branches in `folders`, `currentFolderName`, `selectFolder`, and hierarchy commands

Behavior:

- Provides built-in `smart:all` and `smart:favorites` rows.
- Prevents smart folders from being moved, used as real parents, or queried as real DB folders.

Risk: Medium.

Future candidate:

- `SmartFolderPolicy`
- app config or app shell policy

This is partly app policy and may belong outside pure persistence/service code.

## QML-exposed methods and properties

Properties:

- `folders`
- `currentFolderId`
- `currentFolderName`

Slots/methods:

- `createFolder`
- `deleteFolder`
- `renameFolder`
- `moveFolder`
- `reorderFolder`
- `getFolder`
- `getFolderPath`
- `getFolderDefaultTemplateId`
- `setFolderDefaultTemplate`
- `selectFolder`
- `isSmartFolder`
- `getFirstRegularFolderId`
- `getFolderCount`
- `getNoteCount`
- `isFolderCollapsed`
- `toggleFolderExpanded`
- `getDescendantIds`

Signals:

- `foldersChanged`
- `currentFolderChanged`
- `folderAdded`
- `folderAddedForRename`
- `folderRemoved`
- `folderRenamed`
- `folderDeleteFailed`
- `libraryChanged`

## FolderService relationship

`FolderController` delegates persistence to `FolderService` but owns several policies around it:

- tree shaping
- note count enrichment
- depth calculation
- smart folder injection
- delete preconditions
- default folder creation
- selected folder persistence

`FolderService` should remain persistence-focused. Core/app policy should eventually move out of the QML adapter.

## App-policy mixed areas

- smart folder names and colors
- default folder name `내 노트`
- max folder depth policy
- delete failure Korean messages
- auto-select newly created folders
- immediate rename mode via `folderAddedForRename`
- expanded/collapsed visual state
- restoring last folder through settings

## Possible app_config/app shell candidates

- smart folder definitions
- maximum hierarchy depth
- default folder name/color
- initial folder selection policy
- UI rename-after-create policy

## Migration risk

Overall risk: High.

Safer order:

1. Add tests around `FolderService` persistence behavior.
2. Add tests around smart-folder and selection behavior through `FolderController`.
3. Extract pure hierarchy helpers for depth/tree shaping.
4. Extract smart-folder configuration/policy.
5. Extract selection state.
6. Keep QML adapter names unchanged until `editor_ui` shell is stable.
