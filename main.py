#!/usr/bin/env python3
"""
Nuni Note - Premium Desktop Note Taking Application
====================================================

A premium-quality desktop note-taking app built with PyQt6/QML.
Designed with iOS-level aesthetics and financial app trustworthiness.

Author: Windsurf AI
Version: 1.0.0
"""

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtGui import QFontDatabase, QFont, QIcon

from app_bootstrap import bootstrap_app
from app_config import create_app_config


def setup_fonts(app: QApplication):
    """Load and configure application fonts."""
    # Get available font families
    families = QFontDatabase.families()
    
    # System font fallback
    font = QFont("Inter", 10)
    if "Inter" not in families:
        # Fallback to system sans-serif fonts
        font = QFont("Segoe UI", 10)
        if "Segoe UI" not in families:
            font = QFont("Helvetica Neue", 10)
            if "Helvetica Neue" not in families:
                font = QFont("Arial", 10)
    
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)


def main():
    """Application entry point."""
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
    # Use Basic style for customizable ScrollBar
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

    base_dir = Path(__file__).parent.resolve()
    config = create_app_config(base_dir, sys.argv)

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