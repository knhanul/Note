#!/usr/bin/env python3
"""Entrypoint for the work AI editor skeleton app."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication

import logging

from app_bootstrap import bootstrap_app
from app_config import create_app_config
from packages.ollama_plugin import AIAssistantController, AssistantController, OllamaAssistantPlugin, PromptController, AIPromptDocumentController, AIActionController
from packages.plugin_api import PluginRegistry, PluginContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def plugin_setup(engine, services, config):
    """Setup AI plugins for work_ai_editor."""
    logger.info("[work_ai_editor] Setting up AI plugins...")

    # Setup AI Assistant Controller for QML
    ai_controller = AIAssistantController(config.app_data_dir)
    ai_controller.initialize()
    engine.rootContext().setContextProperty("aiAssistantController", ai_controller)
    engine._ai_controller = ai_controller  # Prevent GC

    # Setup Assistant Controller for AI operations
    assistant_controller = AssistantController(config.app_data_dir)
    assistant_controller.set_note_controller(services.note_controller)
    engine.rootContext().setContextProperty("assistantController", assistant_controller)
    engine._assistant_controller = assistant_controller  # Prevent GC

    prompt_controller = PromptController(config.app_data_dir)
    engine.rootContext().setContextProperty("promptController", prompt_controller)
    engine._prompt_controller = prompt_controller  # Prevent GC

    # Setup AI Prompt Document Controller for workspace mode
    prompt_document_controller = AIPromptDocumentController(config.app_data_dir, prompt_service=prompt_controller._service)
    prompt_document_controller._initialize()
    engine.rootContext().setContextProperty("promptDocumentController", prompt_document_controller)
    engine._prompt_document_controller = prompt_document_controller  # Prevent GC

    # Setup AIActionController for action management (Phase 1)
    ai_action_controller = AIActionController(config.app_data_dir)
    engine.rootContext().setContextProperty("aiActionController", ai_action_controller)
    engine._ai_action_controller = ai_action_controller  # Prevent GC

    logger.info("[work_ai_editor] AI Assistant Controller initialized")

    registry = PluginRegistry()
    plugin = OllamaAssistantPlugin()

    registry.register_plugin(plugin)

    context = PluginContext(
        app_name="work_ai_editor",
        app_config=config,
        services=services,
        registry=registry
    )

    success = registry.activate_plugin("ollama.assistant", context)

    if success:
        logger.info("[work_ai_editor] OllamaAssistantPlugin activated successfully")
        logger.info(f"[work_ai_editor] Registered commands: {[c.id for c in registry.get_commands()]}")
    else:
        error = registry.get_activation_error("ollama.assistant")
        logger.error(f"[work_ai_editor] Failed to activate OllamaAssistantPlugin: {error}")

    logger.info("[work_ai_editor] Plugin setup complete")


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
    bootstrap_app(engine, config, plugin_setup=plugin_setup, app_variant="work_ai_editor")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
