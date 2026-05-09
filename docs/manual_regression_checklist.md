# Manual Regression Checklist

## App Execution

- [ ] `python main.py` launches
- [ ] `python apps\markdown_editor\main.py` launches
- [ ] `python apps\work_ai_editor\main.py` launches
- [ ] `python apps\special_editor\main.py` launches
- [ ] `python -m apps.markdown_editor.main` launches
- [ ] `python -m apps.work_ai_editor.main` launches
- [ ] `python -m apps.special_editor.main` launches

## Library Loading

- [ ] Existing libraries load correctly
- [ ] Folder tree displays correctly
- [ ] Note list displays correctly
- [ ] Smart folders (All, Favorites) work

## Note Operations

- [ ] Open a note
- [ ] Edit note content
- [ ] Autosave indicator shows saved
- [ ] Switch to another note (save on switch)
- [ ] Create new note
- [ ] Delete note (soft delete)
- [ ] Pin/unpin note

## Folder Operations

- [ ] Create folder
- [ ] Rename folder
- [ ] Delete folder (prevented if children or notes exist)
- [ ] Move folder
- [ ] Reorder folder
- [ ] Collapse/expand folder
- [ ] Select folder

## Image Operations

- [ ] Paste image into note
- [ ] Image displays in editor
- [ ] Save note with image
- [ ] Reload note with image
- [ ] Image token `note-image://` handled correctly
- [ ] Export note with image

## Editor Modes

- [ ] Switch between WYSIWYG and Markdown mode
- [ ] Formatting buttons work (bold, italic, heading, code, list, table)
- [ ] Link insertion works
- [ ] Table insertion works

## Tag Operations

- [ ] Add tag to note
- [ ] Remove tag from note
- [ ] Filter by tag
- [ ] Tag chip click sets filter
- [ ] Clear tag filter

## Template Operations

- [ ] Create template
- [ ] Edit template
- [ ] Delete template
- [ ] Apply template to note
- [ ] Template fields render correctly

## Export/Import

- [ ] Export current note to Markdown
- [ ] Export current note to HTML
- [ ] Export folder to Markdown
- [ ] Import directory tree
- [ ] Imported notes appear correctly
- [ ] HWP/HWPX conversion stubs do not break app

## Brand-Specific Features

- [ ] `posid` CLI argument changes brand (nuni vs posid)
- [ ] App icon loads correctly
- [ ] App name displays correctly
- [ ] Logo path resolves correctly

## Three-App Verification

- [ ] `main.py` behaves as before
- [ ] `markdown_editor` behaves as before
- [ ] `work_ai_editor` launches (skeleton, no AI features)
- [ ] `special_editor` launches (skeleton, no special editor UI)

## Regression Tests

- [ ] `python scripts\run_regression_checks.py` passes (48 tests)
