# Special Editor Skeleton

`apps/special_editor` is a skeleton entrypoint for a future app that can use a specialized editor or business-specific editing workflow.

## Current status

This app currently reuses the existing markdown editor runtime:

- existing `app_config.py`
- existing `app_bootstrap.py`
- existing `qml/Main.qml`
- existing `controllers/`
- existing `services/`
- existing `editor-src/`
- existing `assets/`

No special-purpose editor UI is implemented in this step.

## EditorAdapter status

`packages.editor_core.adapters` defines adapter contracts and stubs, but they are not connected to runtime yet.

The current app still uses the existing QML and WebNoteEditor path through `app_bootstrap.py`.

## Execution methods

From the project root:

```powershell
python apps\special_editor\main.py
python -m apps.special_editor.main
```

Existing entrypoints remain available:

```powershell
python main.py
python apps\markdown_editor\main.py
python apps\work_ai_editor\main.py
```

## Paths and runtime boundaries

This skeleton does not move or modify:

- `qml/`
- `controllers/`
- `services/`
- `editor-src/`
- `assets/`
- database files
- library folders
- settings files

Future steps can connect app-specific editor adapters after adapter contract tests and EditorPanel separation are in place.
