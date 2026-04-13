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
from PyQt6.QtGui import QFontDatabase, QFont

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


def main():
    """Application entry point."""
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "RoundPreferFloor"
    
    # WebEngine is initialized automatically when QWebEngineView is created
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Nuni Note")
    app.setOrganizationName("nuninote")
    app.setApplicationVersion("1.0.0")
    
    # Setup fonts
    setup_fonts(app)
    
    # Create QML engine first
    engine = QQmlApplicationEngine()
    
    # Create controllers with engine as parent so they stay alive
    folder_controller = FolderController(engine)
    note_controller = NoteController(folder_controller, engine)
    
    # Get the directory containing this script
    current_dir = Path(__file__).parent.resolve()
    qml_dir = current_dir / "qml"
    
    # Add import paths for QML modules
    engine.addImportPath(str(qml_dir))
    
    # Set context properties for controllers BEFORE loading QML
    engine.rootContext().setContextProperty("folderController", folder_controller)
    engine.rootContext().setContextProperty("noteController", note_controller)
    
    # Force context property update
    engine.rootContext().setContextProperty("folderControllerReady", True)
    
    # Load the main QML file
    main_qml = qml_dir / "Main.qml"
    
    if not main_qml.exists():
        print(f"Error: Main.qml not found at {main_qml}")
        sys.exit(1)
    
    engine.load(QUrl.fromLocalFile(str(main_qml)))
    
    # Check if loading succeeded
    if not engine.rootObjects():
        print("Error: Failed to load QML")
        sys.exit(1)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
