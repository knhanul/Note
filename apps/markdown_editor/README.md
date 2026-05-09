# Markdown Editor App

`apps/markdown_editor` is the application entrypoint package for the current pure markdown editor app.

## Current role

This package only adds an app-specific launch entrypoint. It reuses the existing root application configuration and bootstrap modules:

- `app_config.py`
- `app_bootstrap.py`

The app still loads the existing `qml/Main.qml` and uses the existing controllers, services, editor frontend, assets, database paths, and QML context property names.

## Execution methods

From the project root:

```powershell
python main.py
python apps\markdown_editor\main.py
python -m apps.markdown_editor.main
```

All three commands should launch the same current markdown editor app.

## Not moved in this step

The following runtime assets remain in their existing locations:

- `qml/`
- `controllers/`
- `services/`
- `editor-src/`
- `assets/`
- database files and library folders

## Migration direction

Common functionality is being prepared under `packages/` boundaries. This app entrypoint is the first step toward future app separation, while preserving the current root entrypoint and runtime behavior.
