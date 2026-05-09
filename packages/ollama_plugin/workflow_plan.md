# Work AI Editor Workflow Plan

This document outlines future workflows only. No AI runtime is implemented in this step.

## Candidate workflows

### Current document summary

The user can request a summary of the current note. The future plugin should read the current document through stable editor-core/plugin-api contracts, not by directly coupling to QML internals.

### Selection-based question answering

The user can ask a question about selected text. The selection provider should be app-owned or exposed through a stable document context.

### Work result accumulation

AI outputs can be accumulated as task outputs and optionally linked to notes or sessions.

### Conversation history storage

Future `llm_sessions` and `llm_messages` tables may preserve multi-turn context after an explicit migration step.

### Document-linked AI outputs

Generated outputs can be associated with a note so users can revisit summaries, decisions, and extracted tasks.

### RAG candidates

RAG can use note chunks and embeddings after a separate indexing pipeline is designed and tested.

### Ollama server connection check

The plugin should gracefully detect whether an Ollama server is reachable before enabling real commands.

### Model selection

Model choice should be configurable per app or workspace without changing the pure markdown editor defaults.

### Graceful degradation

If Ollama is unavailable, commands should fail safely and the editor should remain usable.

## Separation principle

The pure `markdown_editor` app must remain independent from AI-specific plugins. `work_ai_editor` should own the optional registration of Ollama/SLLM plugins.
