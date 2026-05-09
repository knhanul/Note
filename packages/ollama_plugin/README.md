# Ollama Plugin Stub

`packages.ollama_plugin` is a disabled-by-default stub for future Ollama/SLLM features.

## Current status

This package does not call an Ollama server, does not create AI UI, does not write settings, and does not change the database schema.

The package only provides:

- `OllamaSettings` dataclass defaults
- `OllamaClient` network-free stub
- `OllamaAssistantPlugin` plugin-api compatible stub
- mock command handlers that return fixed strings
- schema and workflow planning documents

## Runtime integration

The current `markdown_editor` app does not load this plugin.

The `work_ai_editor` skeleton has helper functions for registering this plugin into a `PluginRegistry`, but the app bootstrap is not strongly coupled to the plugin system yet.

## Not implemented

- HTTP calls to Ollama
- model discovery through Ollama
- chat/generate execution
- embeddings
- RAG
- AI panel UI
- DB migration
- settings file persistence

## Future integration direction

A future step can activate this plugin from `apps/work_ai_editor` after UI extension points and plugin lifecycle rules are finalized.
