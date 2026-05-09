# Package Structure

## packages/storage

**Current state**: Compatibility wrappers.

**Runtime connection**: Re-exports existing `services/database`, `note_service`, `folder_service`, `library_service`, `settings_service` without changing behavior.

**Future migration target**: Actual repository layer.

**Note**: No DB path or schema changes.

## packages/import_export

**Current state**: Compatibility wrappers.

**Runtime connection**: Re-exports existing `services/current_note_export_service`, `folder_export_service`, `folder_import_service`, HWP/HWPX conversion functions.

**Future migration target**: Actual provider layer.

**Note**: No file path or export format changes.

## packages/markdown_engine

**Current state**: Documentation + placeholder.

**Runtime connection**: No runtime logic. `normalizer.py` is a placeholder.

**Future migration target**: Markdown normalization, payload validation, image contract enforcement.

**Note**: Existing React/Tiptap editor and QML bridge remain in `editor-src/` and `qml/`.

## packages/editor_ui

**Current state**: Documentation only.

**Runtime connection**: No runtime logic. QML files remain in `qml/`.

**Future migration target**: Common UI components, theme contracts, QML module structure.

**Note**: QML import paths and context property names remain unchanged.

## packages/editor_core

**Current state**: Documentation + inactive placeholders.

**Runtime connection**: No runtime logic. Placeholders for `SaveCoordinator`, `ImageTokenService`, `NoteFilterService`, `SelectionState` are not instantiated.

**Future migration target**: Core coordination logic (save coordination, image tokenization, selection state, filtering).

**Note**: Autosave logic and image tokenization/hydration remain in `NoteController`.

## packages/plugin_api

**Current state**: Minimal registry and extension point contracts.

**Runtime connection**: Independent registry only. Not connected to `app_bootstrap.py` or QML.

**Future migration target**: Plugin lifecycle, command/action registration, sidebar panel contracts.

**Note**: No actual plugins are activated by the existing apps.

## packages/ollama_plugin

**Current state**: Network-free stub.

**Runtime connection**: Stub plugin that can be registered but does not call Ollama.

**Future migration target**: Real Ollama client, model discovery, embeddings, RAG.

**Note**: No HTTP calls, no settings file writes, no DB schema changes.

## packages/editor_core/adapters

**Current state**: Contract + stubs.

**Runtime connection**: `EditorAdapter` Protocol exists. `MarkdownEditorAdapter` and `CustomEditorAdapter` are stubs not connected to QML/WebEngine/NoteController.

**Future migration target**: Actual editor adapters for WebNoteEditor, Milkdown, business forms, AI conversational editors.

**Note**: No QML component replacement, no autosave connection changes.
