# Architecture Overview

## Refactoring Purpose

The Note2 refactoring aims to:

- Preserve the stable pure markdown editor as the shared foundation
- Enable app-specific variants (work AI editor, special-purpose editor)
- Introduce modular package boundaries without breaking existing behavior
- Prepare for optional AI/SLLM features without coupling them to the core editor

## Structure Overview

```
Note2/
├── apps/                    # Application entrypoints
│   ├── markdown_editor/     # Pure markdown editor app
│   ├── work_ai_editor/      # Future Ollama/SLLM work assistant
│   └── special_editor/      # Future special-purpose editor
├── packages/                # Shared packages
│   ├── storage/             # Storage compatibility wrappers
│   ├── import_export/       # Import/export compatibility wrappers
│   ├── markdown_engine/     # Markdown engine boundary (doc + placeholder)
│   ├── editor_ui/           # QML/UI boundary (doc only)
│   ├── editor_core/         # Core coordination boundary (doc + placeholders)
│   ├── plugin_api/          # Plugin API registry (minimal)
│   └── ollama_plugin/       # Ollama plugin stub (network-free)
├── controllers/             # Existing QML controllers
├── services/                # Existing services
├── qml/                     # Existing QML files
├── editor-src/              # Existing React/Tiptap editor
└── assets/                  # Existing assets
```

## App Relationships

- **root main.py**: Compatibility entrypoint, reuses existing runtime
- **apps/markdown_editor**: Pure markdown editor app, reuses existing runtime
- **apps/work_ai_editor**: Future Ollama/SLLM work assistant, currently skeleton
- **apps/special_editor**: Future special-purpose editor, currently skeleton

All apps currently reuse the same `app_config.py`, `app_bootstrap.py`, `qml/Main.qml`, `controllers/`, and `services/`.

## Package Roles

- **packages/storage**: Compatibility wrappers for existing services-based storage
- **packages/import_export**: Compatibility wrappers for existing import/export services
- **packages/markdown_engine**: Documentation and placeholder for future markdown engine boundary
- **packages/editor_ui**: Documentation for QML/UI boundary
- **packages/editor_core**: Documentation and placeholders for core coordination
- **packages/plugin_api**: Minimal plugin API registry and extension point contracts
- **packages/ollama_plugin**: Network-free Ollama plugin stub

## Current Stage

This is the **first structural separation phase**:

- No actual logic moves from controllers/services to packages
- No QML changes
- No DB schema changes
- No runtime connection of adapters or plugins
- Focus on skeleton apps, wrapper packages, documentation, and test baseline

## Stability First

The refactoring prioritizes preserving existing stability:

- Autosave logic remains unchanged
- Image tokenization/hydration remains unchanged
- QML context property names remain unchanged
- DB paths and schemas remain unchanged
- All existing apps continue to run as before
