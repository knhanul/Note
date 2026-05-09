# Plugin API

`packages.plugin_api` defines the minimal extension API for future Note2 app variants and plugins.

## Purpose

The package provides an in-memory registry and small data structures for plugins to contribute commands, menu actions, document actions, and sidebar panels.

This step does not implement Ollama, SLLM, AI panels, QML integration, or plugin discovery. It only prepares a safe API boundary.

## Relationship with editor-core

`editor_core` should expose app-independent editor state and coordination contracts. `plugin_api` should consume stable contracts from app/core layers, but `editor_core` should not directly import specific plugins such as an `ollama_plugin`.

Future AI or special-purpose features should be registered by an app, not hardwired into core.

## Current stage

The current stage is a minimal registry stage:

- no QML connection
- no WebEngine connection
- no app bootstrap connection
- no database access
- no external dependency
- no plugin auto-discovery

The existing markdown editor app continues to run without plugins.

## Registration model

An app can create a `PluginRegistry`, build a `PluginContext`, register plugins, and activate them:

```python
registry = PluginRegistry()
context = PluginContext(app_name="work_ai_editor", registry=registry)
registry.register_plugin(plugin)
registry.activate_plugin(plugin.id, context)
```

## Extension points

Current minimal extension point data structures:

- `Command`
- `MenuAction`
- `DocumentAction`
- `SidebarPanel`

Future candidates:

- settings page
- export/import provider
- AI assistant provider
- editor command provider
- document analysis provider
- workspace/sidebar provider

## Future work_ai_editor direction

A future `apps/work_ai_editor` can register an `ollama_plugin` through this API. That plugin should remain optional, app-owned, and isolated from the pure markdown editor app.
