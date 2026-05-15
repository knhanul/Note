"""Assistant controller for AI operations."""

import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty

from .action_registry import ActionRegistry
from .ai_settings import AISettingsManager
from .ai_worker import AIWorkerManager, AIWorker
from .prompt_manager import PromptManager
from .prompt_renderer import PromptRenderer
from .simple_chunker import SimpleChunker
from .simple_retriever import SimpleRetriever

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000
MAX_OUTPUT_LENGTH = 500


class AssistantController(QObject):
    """Controller for AI assistant operations."""

    statusChanged = pyqtSignal(str)
    tokenReceived = pyqtSignal(str)
    resultReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    runningChanged = pyqtSignal(bool)
    noteCreated = pyqtSignal(str)

    def __init__(self, app_data_dir=None, parent=None):
        super().__init__(parent)
        self._worker_manager = AIWorkerManager()
        self._settings_manager = AISettingsManager(app_data_dir)
        self._action_registry = ActionRegistry()
        self._prompt_manager = PromptManager(app_data_dir=app_data_dir)
        self._prompt_renderer = PromptRenderer()
        self._chunker = SimpleChunker()
        self._retriever = SimpleRetriever(top_k=3)
        self._current_worker: AIWorker | None = None
        self._response_text = ""
        self._retrieved_context = ""
        self._last_query = ""
        self._note_controller = None
        self._app_data_dir = app_data_dir

    def set_note_controller(self, controller):
        """Set note controller for creating notes."""
        self._note_controller = controller

    @pyqtProperty(bool, notify=runningChanged)
    def isRunning(self) -> bool:
        return self._worker_manager.is_running()

    @pyqtProperty(str)
    def status(self) -> str:
        return self._settings_manager.settings.chat_model or "모델 미선택"

    def _on_worker_finished(self):
        """Handle worker finished."""
        self.runningChanged.emit(False)
        self._current_worker = None
        self._worker_manager.clear_worker()
        self.resultReady.emit(self._response_text)
        logger.info("[AssistantController] Task finished")

    def _on_token_received(self, token: str):
        """Handle token received."""
        if len(self._response_text) < MAX_OUTPUT_LENGTH:
            self._response_text += token
            self.tokenReceived.emit(token)

    def _on_error(self, error: str):
        """Handle error."""
        self.errorOccurred.emit(error)
        self.runningChanged.emit(False)
        self._current_worker = None
        logger.error(f"[AssistantController] Error: {error}")

    def _on_status_changed(self, status: str):
        """Handle status changed."""
        self.statusChanged.emit(status)

    def _run_ai_task(self, prompt: str):
        """Run an AI task with the given prompt."""
        if self._worker_manager.is_running():
            logger.warning("[AssistantController] Task already running")
            self.errorOccurred.emit("이미 실행 중인 작업이 있습니다")
            return

        settings = self._settings_manager.settings
        if not settings.chat_model:
            self.errorOccurred.emit("모델이 선택되지 않았습니다")
            return

        logger.info(f"[AssistantController] Running AI task with model: {settings.chat_model}")
        self._response_text = ""
        self.runningChanged.emit(True)
        self.statusChanged.emit("실행 중...")

        self._current_worker = self._worker_manager.run_task(
            prompt=prompt,
            model=settings.chat_model,
            base_url=settings.base_url,
            timeout=120
        )

        self._current_worker.signals.finished.connect(self._on_worker_finished)
        self._current_worker.signals.tokenReceived.connect(self._on_token_received)
        self._current_worker.signals.errorOccurred.connect(self._on_error)
        self._current_worker.signals.statusChanged.connect(self._on_status_changed)

    @pyqtSlot(str, str)
    def runTask(self, action_id: str, content: str):
        """Run an AI task based on action ID."""
        if not content or not content.strip():
            self.errorOccurred.emit("문서 내용이 없습니다")
            return

        action = self._action_registry.get_action(action_id)
        if not action:
            logger.warning(f"[AssistantController] Action not found: {action_id}")
            self.errorOccurred.emit(f"알 수 없는 작업: {action_id}")
            return

        truncated_content = content[:MAX_CONTENT_LENGTH]

        prompt_template = self._prompt_manager.get_prompt(action.prompt_template)
        if not prompt_template:
            logger.warning(f"[AssistantController] Prompt template not found: {action.prompt_template}")
            self.errorOccurred.emit(f"프롬프트를 찾을 수 없습니다: {action.prompt_template}")
            return

        context = {
            "current_note": truncated_content,
            "content": truncated_content,
        }

        if action.rag and action_id == "current_note_qa":
            chunks = self._chunker.chunk_text(truncated_content)
            retrieved_chunks = self._retriever.retrieve(chunks, self._last_query or "")
            self._retrieved_context = self._retriever.format_context(retrieved_chunks)
            context["retrieved_context"] = self._retrieved_context
            context["question"] = self._last_query or ""

        prompt = self._prompt_renderer.render(prompt_template, context)
        self._run_ai_task(prompt)

    @pyqtSlot(str, str)
    def askQuestion(self, content: str, question: str):
        """Ask a question about the current note."""
        if self._worker_manager.is_running():
            self.errorOccurred.emit("이미 실행 중인 작업이 있습니다")
            return

        if not content or not content.strip():
            self.errorOccurred.emit("문서 내용이 없습니다")
            return

        if not question or not question.strip():
            self.errorOccurred.emit("질문이 없습니다")
            return

        self._last_query = question
        self.runTask("current_note_qa", content)

    @pyqtProperty(str)
    def retrievedContext(self) -> str:
        """Get the last retrieved context."""
        return self._retrieved_context

    @pyqtSlot(str, result=list)
    def listActions(self) -> list:
        """List all available actions."""
        return self._action_registry.list_actions()

    @pyqtSlot(str)
    def testPrompt(self, prompt: str):
        """Run a test prompt."""
        self._run_ai_task(prompt)

    @pyqtSlot()
    def cancel(self):
        """Cancel the current operation."""
        if self._worker_manager.is_running():
            self._worker_manager.cancel_current()
            self.statusChanged.emit("중지됨")
            self.runningChanged.emit(False)
            logger.info("[AssistantController] Task cancelled")

    @pyqtSlot()
    def clearResponse(self):
        """Clear the response text."""
        self._response_text = ""
        self.resultReady.emit("")

    @pyqtSlot(str, str, str, result=str)
    def createNewNote(self, title: str, content: str, folder_id: str = "") -> str:
        """Create a new note with the given content."""
        if not self._note_controller:
            logger.error("[AssistantController] Note controller not set")
            self.errorOccurred.emit("노트 컨트롤러가 없습니다")
            return ""

        try:
            note_id = self._note_controller.createNote(title, content, "", folder_id)
            logger.info(f"[AssistantController] Created new note: {note_id}")
            self.noteCreated.emit(note_id)
            return note_id
        except Exception as e:
            logger.error(f"[AssistantController] Failed to create note: {e}")
            self.errorOccurred.emit(f"노트 생성 실패: {e}")
            return ""

    def getResponseText(self) -> str:
        """Get the accumulated response text."""
        return self._response_text
