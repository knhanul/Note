# Regression Baseline Tests

These tests protect contracts that should not break during the upcoming controller/service refactoring.

## Purpose

The baseline checks verify:

- boundary package imports
- storage compatibility wrapper re-exports
- import/export compatibility wrapper imports
- markdown-engine placeholder status
- editor-ui documentation presence
- editor-core placeholder and documentation presence
- `app_bootstrap.py` QML context property names through static source inspection
- critical controller method/field names through static source inspection

## What these tests do not run

These tests intentionally do not start:

- QApplication
- QQmlApplicationEngine
- QML UI
- Qt WebEngine
- real application bootstrap
- real database migrations or writes
- import/export execution

Manual app verification is still required for UI behavior, autosave behavior, note editing, image display, and import/export dialogs.

## How to run

From Windows PowerShell in the project root:

```powershell
python scripts\run_regression_checks.py
```

Equivalent unittest command:

```powershell
python -m unittest discover -s tests
```

## Refactoring rule

Before moving controller/service logic, these tests should pass. If a test fails during refactoring, either restore the protected contract or update the test only after the compatibility impact is intentionally reviewed.
