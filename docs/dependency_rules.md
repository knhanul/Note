# Dependency Rules

## Core Principles

- **editor_core must not import ollama_plugin**
- **editor_core must not import app-specific code**
- **storage must not depend on QML/UI**
- **import_export must not depend on app brand or AI features**
- **plugin_api must not depend on specific plugin implementations**
- **ollama_plugin may use plugin_api, but must not be forced into markdown_editor**
- **apps compose packages; packages should not know about apps**
- **QML context property names must not be changed without migration plan**
- **DB paths and schemas must not be changed without migration plan**
- **NoteController autosave logic must not be modified without regression tests**

## Forbidden Dependencies

- `packages.editor_core` → `packages.ollama_plugin`
- `packages.editor_core` → `apps.*`
- `packages.storage` → `qml`, `PyQt6.QtQml`, UI-specific modules
- `packages.import_export` → app-specific brand logic
- `packages.plugin_api` → `packages.ollama_plugin` (plugin_api should stay generic)
- `packages.markdown_engine` → `editor-src/App.jsx` (future boundary)

## Allowed Dependencies

- `apps.*` → `packages.*`
- `packages.editor_core` → `packages.plugin_api` (optional, for extension points)
- `packages.ollama_plugin` → `packages.plugin_api` (plugin implements contract)
- `packages.storage` → `services.*` (current wrapper stage only)
- `packages.import_export` → `services.*` (current wrapper stage only)

## Runtime Modification Constraints

- Do not modify `NoteController` autosave internals without characterization tests
- Do not modify image tokenization/hydration without image regression tests
- Do not change QML context property names without updating all QML files and tests
- Do not change DB paths without data migration plan
- Do not replace `WebNoteEditor.qml` without adapter contract tests
- Do not remove `Main.qml` without app shell separation plan
- Do not remove `editor-src/App.jsx` without markdown engine replacement plan

## Migration Sequencing

Before moving logic from controllers to packages:

1. Add regression tests for the behavior
2. Add characterization tests for autosave/image tokenization
3. Document the contract
4. Implement the new package component
5. Wire it in a single app first
6. Verify regression tests pass
7. Roll out to other apps if applicable
