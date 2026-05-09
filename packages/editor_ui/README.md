# Editor UI Boundary

`packages.editor_ui` is the planned boundary for reusable QML UI structure in Note2.

## Purpose

The goal is to let `apps/markdown_editor`, `apps/work_ai_editor`, and future specialized editor apps reuse common UI components, theme tokens, and shell patterns without copying QML files.

## Current phase

This is a documentation/boundary phase. The actual QML implementation still lives in the existing `qml/` directory.

No QML file has been moved. No QML import path has been changed. No context property, signal, id, property, or visual design has been changed.

## Current implementation locations

- Main shell and orchestration: `qml/Main.qml`
- Reusable components: `qml/components/*.qml`
- Theme singletons: `qml/theme/Colors.qml`, `Metrics.qml`, `Typography.qml`
- QML import path setup: `app_bootstrap.py`, via `engine.addImportPath(str(config.qml_import_path))`
- QML path config: `app_config.py`

## Stability principles

- Keep `import theme` and `import components` working.
- Keep context property names stable, including `noteController`, `folderController`, `templateController`, `currentExportController`, `folderImportController`, and `libraryService`.
- Do not split `Main.qml` until signal flow and id/property references are tested.
- Keep `WebNoteEditor.qml` bridge behavior unchanged unless markdown-engine bridge tests exist.

## Future direction

The likely direction is to move simple theme/components first, then introduce an app shell abstraction. App-specific panels such as AI assistant panels or special workflow panels should be composed around the shared shell rather than copied from the markdown editor.
