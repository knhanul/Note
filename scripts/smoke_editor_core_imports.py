"""Smoke-check editor core boundary imports without touching app state or DB."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import packages.editor_core
import packages.editor_core.placeholders.save_coordinator
import packages.editor_core.placeholders.image_token_service
import packages.editor_core.placeholders.note_filter_service
import packages.editor_core.placeholders.selection_state


def main() -> None:
    assert packages.editor_core is not None
    print("editor_core imports ok")


if __name__ == "__main__":
    main()
