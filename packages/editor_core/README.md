# Editor Core Boundary

`packages.editor_core` is the planned boundary for editor-domain coordination that should eventually sit between UI adapters and persistence/import/export services.

## Purpose

The goal is to separate pure editor state and coordination logic from PyQt/QML-facing controllers. Future core modules may coordinate note selection, dirty state, save sequencing, image token handling, filtering, pagination, templates, and document commands.

## Current phase

This is a documentation/boundary phase.

The actual implementation still lives in:

- `controllers/note_controller.py`
- `controllers/folder_controller.py`
- `controllers/template_controller.py`
- `controllers/current_export_controller.py`
- `controllers/folder_import_controller.py`
- `services/*.py`

No controller logic has been moved. No service logic has been moved. No runtime code imports these placeholders.

## Future direction

A later refactor can split responsibilities into:

- QML adapter/controller layer: PyQt signals, slots, properties, and context property names.
- Editor core layer: save coordination, selection state, filtering, payload/image coordination, and app-independent editor policies.
- Storage/import/export/markdown layers: existing package boundaries and services.

## Non-goals

`editor_core` should not contain:

- Ollama/SLLM integration
- app branding
- special business-workflow panels
- QML visual components
- app-specific UI policy

`editor_core` should avoid strong dependency on `editor_ui` or QML. PyQt-specific adapters should remain outside the pure core when possible.
