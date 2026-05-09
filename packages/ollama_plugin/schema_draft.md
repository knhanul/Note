# AI Schema Draft

This document is a draft only. No migration is created or executed in this step.

## Goals

Future AI features may need to preserve sessions, messages, generated outputs, references, tasks, chunks, and embeddings while keeping the pure markdown editor database behavior stable.

## Candidate tables

### llm_sessions

Potential fields:

- `id`
- `note_id`
- `title`
- `provider`
- `model_name`
- `created_at`
- `updated_at`

### llm_messages

Potential fields:

- `id`
- `session_id`
- `role`
- `content`
- `created_at`

### llm_outputs

Potential fields:

- `id`
- `session_id`
- `note_id`
- `output_type`
- `content`
- `created_at`

### llm_references

Potential fields:

- `id`
- `output_id`
- `note_id`
- `source_type`
- `source_id`
- `quote`

### llm_tasks

Potential fields:

- `id`
- `task_type`
- `status`
- `input_payload`
- `output_id`
- `created_at`
- `updated_at`

### rag_chunks

Potential fields:

- `id`
- `note_id`
- `chunk_text`
- `chunk_index`
- `content_hash`
- `created_at`

### embeddings

Potential fields:

- `id`
- `chunk_id`
- `provider`
- `model_name`
- `vector_blob`
- `created_at`

## Non-goals for this step

- no DB migration
- no schema change
- no index creation
- no vector storage implementation
- no writes to existing databases
