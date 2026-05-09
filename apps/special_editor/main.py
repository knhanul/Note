#!/usr/bin/env python3
"""Entrypoint for the special editor skeleton app."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

from app_bootstrap import bootstrap_app
from app_config import create_app_config


def setup_fonts(app: QApplication):
    families = QFontDatabase.families()

    font = QFont("Inter", 10)
    if "Inter" not in families:
        font = QFont("Segoe UI", 10)
        if "Segoe UI" not in families:
            font = QFont("Helvetica Neue", 10)
            if "Helvetica Neue" not in families:
                font = QFont("Arial", 10)

    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)


def main():
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

    config = create_app_config(PROJECT_ROOT, sys.argv)

    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    app.setOrganizationName(config.organization_name)
    app.setApplicationVersion(config.app_version)

    if config.icon_path.exists():
        app.setWindowIcon(QIcon(str(config.icon_path)))

    setup_fonts(app)

    engine = QQmlApplicationEngine()
    bootstrap_app(engine, config)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
