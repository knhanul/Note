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
from controllers.ai_rag_controller import AiRagController
from controllers.tool_controller import ToolController
from services.ai_rag_application_service import AiRagApplicationService

# Setup logging to file for executable builds
def setup_logging():
    """Setup logging to console and file."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # File handler for executable builds
    if getattr(sys, 'frozen', False):
        # Running as executable
        prog_dir = Path(sys.executable).parent
        logs_dir = prog_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / "posid_note.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[console_handler, file_handler],
            format=log_format,
            datefmt=date_format
        )
        local_logger = logging.getLogger(__name__)
        local_logger.info(f"[Logging] Log file: {log_file}")
    else:
        # Running as script
        logging.basicConfig(
            level=logging.INFO,
            handlers=[console_handler],
            format=log_format,
            datefmt=date_format
        )

setup_logging()
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
    assistant_controller.set_folder_controller(services.folder_controller)
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
    try:
        logger.info("[work_ai_editor] Initializing AIActionController...")
        ai_action_controller = AIActionController(config.app_data_dir)
        engine.rootContext().setContextProperty("aiActionController", ai_action_controller)
        engine._ai_action_controller = ai_action_controller  # Prevent GC
        logger.info("[work_ai_editor] AIActionController initialized successfully")
    except Exception as e:
        import traceback
        logger.error(f"[work_ai_editor] Failed to initialize AIActionController: {e}")
        logger.error(f"[work_ai_editor] Traceback: {traceback.format_exc()}")
        engine.rootContext().setContextProperty("aiActionController", None)
        engine._ai_action_controller = None

    logger.info("[work_ai_editor] AI Assistant Controller initialized")

    # Setup AiRagController for multi-document RAG
    try:
        logger.info("[work_ai_editor] Initializing AiRagController...")
        ai_db_path = config.app_data_dir / "ai" / "ai_index.db"
        ai_db_path.parent.mkdir(parents=True, exist_ok=True)
        app_service = AiRagApplicationService(db_path=str(ai_db_path), app_data_dir=config.app_data_dir)
        ai_rag_controller = AiRagController(app_service=app_service)
        engine.rootContext().setContextProperty("aiRagController", ai_rag_controller)
        engine._ai_rag_controller = ai_rag_controller
        logger.info("[work_ai_editor] AiRagController initialized successfully")
    except Exception as e:
        import traceback
        logger.error(f"[work_ai_editor] Failed to initialize AiRagController: {e}")
        logger.error(f"[work_ai_editor] Traceback: {traceback.format_exc()}")
        engine.rootContext().setContextProperty("aiRagController", None)
        engine._ai_rag_controller = None

    # Setup ToolController for external tools
    try:
        logger.info("[work_ai_editor] Initializing ToolController...")
        tool_controller = ToolController()
        engine.rootContext().setContextProperty("toolController", tool_controller)
        engine._tool_controller = tool_controller
        logger.info("[work_ai_editor] ToolController initialized successfully")
    except Exception as e:
        import traceback
        logger.error(f"[work_ai_editor] Failed to initialize ToolController: {e}")
        logger.error(f"[work_ai_editor] Traceback: {traceback.format_exc()}")
        engine.rootContext().setContextProperty("toolController", None)
        engine._tool_controller = None

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
