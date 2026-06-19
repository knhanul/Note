#!/usr/bin/env python3
"""Entrypoint for work AI editor with posid branding."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add 'posid' to argv for brand detection
sys.argv.append("posid")

# Import and run the original main
from apps.work_ai_editor.main import main

if __name__ == "__main__":
    main()
