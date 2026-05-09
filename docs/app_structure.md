# App Structure

## Root main.py

**Role**: Compatibility entrypoint for existing users.

**Current behavior**: Reuses existing `app_config.py`, `app_bootstrap.py`, `qml/Main.qml`, `controllers/`, `services/`.

**Execution**:
```powershell
python main.py
```

## apps/markdown_editor

**Role**: Pure markdown editor app entrypoint.

**Current behavior**: Reuses existing runtime. Future refactoring may move app-specific configuration here.

**Execution**:
```powershell
python apps\markdown_editor\main.py
python -m apps.markdown_editor.main
```

## apps/work_ai_editor

**Role**: Future Ollama/SLLM work assistant app.

**Current status**: Skeleton. Reuses existing markdown editor runtime. Plugin helpers exist but are not connected to bootstrap.

**Execution**:
```powershell
python apps\work_ai_editor\main.py
python -m apps.work_ai_editor.main
```

**Future**: May register `OllamaAssistantPlugin` and add AI-specific UI.

## apps/special_editor

**Role**: Future special-purpose editor app (business forms, workflow editors, etc.).

**Current status**: Skeleton. Reuses existing markdown editor runtime. Editor adapter helpers exist but are not connected to runtime.

**Execution**:
```powershell
python apps\special_editor\main.py
python -m apps.special_editor.main
```

**Future**: May use `CustomEditorAdapter` and app-specific editor UI.

## App Execution Summary

All entrypoints currently launch the same markdown editor UI through the existing QML and controller stack. Future steps will differentiate apps through:
- App-specific config
- Optional plugin registration
- Optional editor adapter selection
- App-specific QML panels or overlays
