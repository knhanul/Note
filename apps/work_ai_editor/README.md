# Work AI Editor Skeleton

`apps/work_ai_editor` is a skeleton entrypoint for a future work-oriented editor app with optional AI plugin support.

## Current status

This app currently reuses the existing pure markdown editor runtime:

- existing `app_config.py`
- existing `app_bootstrap.py`
- existing `qml/Main.qml`
- existing `controllers/`
- existing `services/`
- existing `editor-src/`
- existing `assets/`

The app does not add an AI panel, does not call Ollama, and does not change database or settings paths.

## Ollama status

Ollama support currently exists only as a stub package under `packages/ollama_plugin`.

The stub can register mock commands through `packages.plugin_api`, but it does not perform HTTP calls, model discovery, embeddings, RAG, or database writes.

## Execution methods

From the project root:

```powershell
python apps\work_ai_editor\main.py
python -m apps.work_ai_editor.main
```

Existing entrypoints remain available:

```powershell
python main.py
python apps\markdown_editor\main.py
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

Future AI UI and real Ollama integration should be added in later steps after plugin lifecycle and UI extension contracts are finalized.
