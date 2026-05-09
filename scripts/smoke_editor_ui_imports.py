"""Smoke-check editor UI boundary package imports without loading QML."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import packages.editor_ui


def main() -> None:
    assert packages.editor_ui is not None
    print("editor_ui imports ok")


if __name__ == "__main__":
    main()
