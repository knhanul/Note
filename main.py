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
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
from PyQt6.QtCore import QUrl, QObject, pyqtSignal, pyqtProperty, QTimer
from PyQt6.QtGui import QFontDatabase, QFont, QIcon

from services.library_service import LibraryService
from controllers.folder_controller import FolderController
from controllers.note_controller import NoteController


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


def resolve_brand(base_dir: Path) -> dict:
    """Detect brand from CLI args and return branding config."""
    args = sys.argv[1:]
    if "posid" in args:
        return {
            "brand":     "posid",
            "app_name":  "포시드노트",
            "icon_path": base_dir / "assets" / "images" / "posid" / "posid_logo.ico",
            "logo_path": str(base_dir / "assets" / "images" / "posid" / "posid_ename.png"),
        }
    return {
        "brand":     "nuni",
        "app_name":  "누니노트",
        "icon_path": base_dir / "assets" / "images" / "nuni" / "nuni_ico.ico",
        "logo_path": str(base_dir / "assets" / "images" / "nuni" / "nuni_logo.png"),
    }


def main():
    """Application entry point."""
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
    # Use Basic style for customizable ScrollBar
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

    # Determine base directory
    base_dir = Path(__file__).parent.resolve()

    # Resolve branding
    branding = resolve_brand(base_dir)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(branding["app_name"])
    app.setOrganizationName("nuninote")
    app.setApplicationVersion("1.0.0")

    # Set window icon
    icon_path = branding["icon_path"]
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Setup fonts
    setup_fonts(app)
    
    # Create QML engine first
    engine = QQmlApplicationEngine()
    
    # Create library service first (manages multiple databases)
    library_service = LibraryService(engine)
    
    # Create controllers with library service and engine as parent
    folder_controller = FolderController(library_service, engine)
    note_controller = NoteController(library_service, folder_controller, engine)
    
    # Get the directory containing this script
    current_dir = base_dir
    qml_dir = current_dir / "qml"
    
    # Add import paths for QML modules
    engine.addImportPath(str(qml_dir))
    
    # Set context properties for controllers BEFORE loading QML
    engine.rootContext().setContextProperty("libraryService", library_service)
    engine.rootContext().setContextProperty("folderController", folder_controller)
    engine.rootContext().setContextProperty("noteController", note_controller)

    # Branding context
    engine.rootContext().setContextProperty("appBrand",    branding["brand"])
    engine.rootContext().setContextProperty("appName",     branding["app_name"])
    engine.rootContext().setContextProperty("appLogoPath", branding["logo_path"])
    
    # Force context property update
    engine.rootContext().setContextProperty("folderControllerReady", True)
    
    # Load the main QML file
    main_qml = qml_dir / "Main.qml"
    
    if not main_qml.exists():
        sys.exit(1)

    engine.load(QUrl.fromLocalFile(str(main_qml)))

    # Check if loading succeeded
    if not engine.rootObjects():
        sys.exit(1)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
