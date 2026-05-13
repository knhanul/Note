"""Model manager for Ollama models."""

import logging
from typing import Optional

from .client import OllamaClient, OllamaModel

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()
        self._models: list[OllamaModel] = []
        self._chat_model: str = ""
        self._embedding_model: str = ""

    @property
    def models(self) -> list[OllamaModel]:
        return self._models

    @property
    def chat_model(self) -> str:
        return self._chat_model

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    def refresh_models(self) -> list[OllamaModel]:
        """Refresh the model list from Ollama server."""
        result = self.client.list_models()
        if result.success:
            self._models = result.models
            logger.info(f"Loaded {len(self._models)} models from Ollama")
        else:
            self._models = []
            logger.warning(f"Failed to load models: {result.error}")
        return self._models

    def set_chat_model(self, model_name: str) -> None:
        """Set the chat model."""
        self._chat_model = model_name
        logger.info(f"Chat model set to: {model_name}")

    def set_embedding_model(self, model_name: str) -> None:
        """Set the embedding model."""
        self._embedding_model = model_name
        logger.info(f"Embedding model set to: {model_name}")

    def get_model_names(self) -> list[str]:
        """Get list of model names."""
        return [m.name for m in self._models]

    def find_default_chat_model(self) -> Optional[str]:
        """Find a suitable default chat model."""
        for model in self._models:
            name = model.name.lower()
            if "gemma" in name and "2b" in name:
                return model.name
            if "llama" in name and "3" in name:
                return model.name
            if "phi" in name:
                return model.name
        if self._models:
            return self._models[0].name
        return None

    def find_default_embedding_model(self) -> Optional[str]:
        """Find a suitable default embedding model."""
        for model in self._models:
            name = model.name.lower()
            if "nomic" in name:
                return model.name
            if "embed" in name:
                return model.name
            if "bge" in name:
                return model.name
        return None
