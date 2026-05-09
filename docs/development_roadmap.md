# Development Roadmap

## Recommended Next Steps (Post Phase 1)

### 1. Ollama Connection Preparation
- Design settings screen for Ollama base URL and model name
- Add connection health-check stub tests
- Do not implement actual HTTP calls yet

### 2. AI Schema Migration Branch
- Create a separate branch for AI-related DB schema
- Design `llm_sessions`, `llm_messages`, `llm_outputs` tables
- Design migration scripts
- Do not merge until app-level AI integration is ready

### 3. AI Panel UI Contract
- Design plugin-api to QML connection for sidebar panels
- Document QML signal/slot contracts for AI responses
- Do not add actual AI panel to `Main.qml` yet

### 4. NoteController Slimming
- Add comprehensive autosave characterization tests
- Add image tokenization/hydration characterization tests
- Extract pure state objects (dirty state, selection state)
- Extract `SaveCoordinator` after tests pass

### 5. SaveCoordinator Separation (Last Priority)
- This is the highest-risk component
- Requires autosave flush, document transition, version tracking tests
- Do not attempt until NoteController is well-characterized

### 6. ImageTokenService Separation
- Add image insertion/reloading regression tests
- Add image export consistency tests
- Extract image tokenization/hydration after tests pass
- Verify note-image:// token handling in export

### 7. Main.qml Splitting
- Add QML snapshot tests for current layout
- Create manual regression checklist for panel behavior
- Design AppShell, FolderPanel, NoteListPanel, EditorPanel separation
- Do not modify `Main.qml` until shell plan is reviewed

### 8. Storage Wrapper to Repository Migration
- Add repository contract tests
- Migrate one repository at a time
- Verify existing service behavior unchanged
- Update controller imports gradually

### 9. Import/Export Wrapper to Provider Migration
- Add provider contract tests
- Migrate one provider at a time
- Verify export/import behavior unchanged
- Update controller imports gradually

### 10. EditorAdapter Runtime Connection
- Add WebNoteEditorAdapter characterization tests
- Design EditorPanel QML component
- Connect adapter in a single app first
- Verify autosave, image, focus, content change events

## Sequencing Principles

- **Tests first**: Add regression/characterization tests before moving logic
- **Single app first**: Test new components in one app before rolling out
- **Separate branches**: Use separate branches for high-risk changes (DB, autosave)
- **Document contracts**: Document interfaces before implementing
- **Preserve compatibility**: Keep wrappers until migration is complete
