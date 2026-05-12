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
from services.settings_service import SettingsService


def setup_fonts(app: QApplication, ui_scale: float = 1.0):
    """Load and configure application fonts."""
    # Get available font families
    families = QFontDatabase.families()
    
    # Scale base font size by ui_scale
    base_size = int(round(10 * ui_scale))
    
    # System font fallback
    font = QFont("Inter", base_size)
    if "Inter" not in families:
        # Fallback to system sans-serif fonts
        font = QFont("Segoe UI", base_size)
        if "Segoe UI" not in families:
            font = QFont("Helvetica Neue", base_size)
            if "Helvetica Neue" not in families:
                font = QFont("Arial", base_size)
    
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)


def main():
    """Application entry point."""
    # Load UI scale from settings
    settings_service = SettingsService()
    ui_scale = settings_service.get_ui_scale()
    
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
    os.environ["QT_SCALE_FACTOR"] = str(ui_scale)
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
    
    setup_fonts(app, ui_scale)
    
    engine = QQmlApplicationEngine()
    bootstrap_app(engine, config)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()