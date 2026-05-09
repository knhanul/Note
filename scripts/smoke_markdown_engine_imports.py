"""Smoke-check markdown engine boundary imports without transforming payloads."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import packages.markdown_engine
import packages.markdown_engine.normalizer


def main() -> None:
    assert packages.markdown_engine is not None
    assert packages.markdown_engine.normalizer is not None
    print("markdown_engine imports ok")


if __name__ == "__main__":
    main()
