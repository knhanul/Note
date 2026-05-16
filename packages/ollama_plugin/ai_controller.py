"""AI Assistant controller for QML integration."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot

from .ai_settings import AISettingsManager
from .client import OllamaClient, OllamaModel
from .model_manager import ModelManager

logger = logging.getLogger(__name__)


class AIAssistantController(QObject):
    """Controller for AI Assistant panel in QML."""

    connectionStatusChanged = pyqtSignal(str)
    isConnectedChanged = pyqtSignal(bool)
    modelsChanged = pyqtSignal('QVariantList')
    chatModelChanged = pyqtSignal(str)
    embeddingModelChanged = pyqtSignal(str)
    performanceModeChanged = pyqtSignal(str)

    def __init__(self, app_data_dir: Path | None = None, parent=None):
        super().__init__(parent)
        self._client = OllamaClient()
        self._model_manager = ModelManager(self._client)
        self._settings_manager = AISettingsManager(app_data_dir)

        self._connection_status = "연결 안 됨"
        self._is_connected = False
        self._models: list[str] = []
        self._chat_model = ""
        self._embedding_model = ""
        self._performance_mode = "low"

    @pyqtProperty(str, notify=connectionStatusChanged)
    def connectionStatus(self) -> str:
        return self._connection_status

    @pyqtProperty(bool, notify=isConnectedChanged)
    def isConnected(self) -> bool:
        return self._is_connected

    @pyqtProperty('QVariantList', notify=modelsChanged)
    def modelList(self) -> list:
        return self._models

    @pyqtProperty(str, notify=chatModelChanged)
    def chatModel(self) -> str:
        return self._chat_model

    @pyqtProperty(str, notify=embeddingModelChanged)
    def embeddingModel(self) -> str:
        return self._embedding_model

    @pyqtProperty(str, notify=performanceModeChanged)
    def performanceMode(self) -> str:
        return self._performance_mode

    @pyqtSlot()
    def check_connection(self) -> None:
        """Check Ollama connection and update status."""
        logger.info("[AIAssistant] Checking connection...")
        result = self._client.check_connection()

        self._connection_status = result.message
        self._is_connected = result.success
        self.connectionStatusChanged.emit(self._connection_status)
        self.isConnectedChanged.emit(self._is_connected)

        if result.success:
            self.refresh_models()
        else:
            self._models = []
            self.modelsChanged.emit(self._models)

        logger.info(f"[AIAssistant] Connection status: {self._connection_status}")

    @pyqtSlot()
    def refresh_models(self) -> None:
        """Refresh model list from Ollama."""
        logger.info("[AIAssistant] Refreshing models...")
        models = self._model_manager.refresh_models()
        self._models = [m.name for m in models]
        self.modelsChanged.emit(self._models)
        logger.info(f"[AIAssistant] Found {len(self._models)} models")

    @pyqtSlot(str, result=bool)
    def setChatModel(self, model: str) -> bool:
        """Set chat model and save to settings."""
        logger.info(f"[AIAssistant] Setting chat model: {model}")
        self._chat_model = model
        self._model_manager.set_chat_model(model)
        self._settings_manager.update_chat_model(model)
        self.chatModelChanged.emit(self._chat_model)
        return True

    @pyqtSlot(str, result=bool)
    def setEmbeddingModel(self, model: str) -> bool:
        """Set embedding model and save to settings."""
        logger.info(f"[AIAssistant] Setting embedding model: {model}")
        self._embedding_model = model
        self._model_manager.set_embedding_model(model)
        self._settings_manager.update_embedding_model(model)
        self.embeddingModelChanged.emit(self._embedding_model)
        return True

    @pyqtSlot(str, result=bool)
    def setPerformanceMode(self, mode: str) -> bool:
        """Set performance mode and save to settings."""
        logger.info(f"[AIAssistant] Setting performance mode: {mode}")
        self._performance_mode = mode
        self._settings_manager.update_performance_mode(mode)
        self.performanceModeChanged.emit(self._performance_mode)
        return True

    @pyqtSlot()
    def initialize(self) -> None:
        """Initialize settings from file."""
        settings = self._settings_manager.settings
        self._chat_model = settings.chat_model
        self._embedding_model = settings.embedding_model
        self._performance_mode = settings.performance_mode

        self.chatModelChanged.emit(self._chat_model)
        self.embeddingModelChanged.emit(self._embedding_model)
        self.performanceModeChanged.emit(self._performance_mode)

        logger.info(f"[AIAssistant] Initialized with chat_model={self._chat_model}, embedding_model={self._embedding_model}, mode={self._performance_mode}")

        # Auto-check connection with saved model
        if self._chat_model:
            logger.info(f"[AIAssistant] Auto-checking connection with model: {self._chat_model}")
            self.check_connection()

            # Verify saved model exists in available models
            if self._chat_model not in self._models:
                logger.warning(f"[AIAssistant] Saved model '{self._chat_model}' not found in available models, resetting")
                self._chat_model = ""
                self._settings_manager.update_chat_model("")
                self.chatModelChanged.emit(self._chat_model)
        else:
            logger.info("[AIAssistant] No chat model saved, skipping connection check")
