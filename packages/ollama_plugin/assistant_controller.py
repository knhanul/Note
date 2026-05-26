"""Assistant controller for AI operations."""

import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty

from .action_registry import ActionRegistry
from .ai_settings import AISettingsManager
from .ai_worker import AIWorkerManager, AIWorker
from .ai_prompt_service import PromptService
from .prompt_renderer import PromptRenderer
from .simple_chunker import SimpleChunker
from .simple_retriever import SimpleRetriever

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000
MAX_OUTPUT_LENGTH = 500
RESPONSE_LENGTH_TO_NUM_PREDICT = {
    "short": 256,
    "medium": 512,
    "long": 1024,
}


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
        self._prompt_service = PromptService(app_data_dir)
        self._prompt_renderer = PromptRenderer()
        self._chunker = SimpleChunker()
        initial_settings = self._settings_manager.settings
        self._retriever = SimpleRetriever(top_k=initial_settings.top_k or SimpleRetriever.DEFAULT_TOP_K)
        self._current_worker: AIWorker | None = None
        self._response_text = ""
        self._retrieved_context = ""
        self._last_query = ""
        self._note_controller = None
        self._folder_controller = None
        self._app_data_dir = app_data_dir

    def set_note_controller(self, controller):
        """Set note controller for creating notes."""
        self._note_controller = controller

    def set_folder_controller(self, controller):
        """Set folder controller for folder operations."""
        self._folder_controller = controller

    @pyqtProperty(bool, notify=runningChanged)
    def isRunning(self) -> bool:
        return self._worker_manager.is_running()

    @pyqtProperty(str)
    def status(self) -> str:
        return self._settings_manager.settings.chat_model or "모델 미선택"

    def _load_settings(self, refresh: bool = False):
        settings = self._settings_manager.refresh() if refresh else self._settings_manager.settings
        top_k = settings.top_k or SimpleRetriever.DEFAULT_TOP_K
        self._retriever.top_k = top_k
        return settings

    def _on_worker_finished(self):
        """Handle worker finished."""
        self.runningChanged.emit(False)
        self._current_worker = None
        self._worker_manager.clear_worker()
        
        # Check for empty response - this happens when worker emitted error for empty response
        if not self._response_text or len(self._response_text) == 0:
            logger.warning(f"[AssistantController] Empty response detected, emitting error instead of resultReady")
            self.errorOccurred.emit("AI 응답이 비어 있습니다. 모델 또는 응답 파싱을 확인해 주세요.")
            return
            
        logger.info(f"[AssistantController] Worker finished, emitting resultReady: response_text_len={len(self._response_text)}")
        self.resultReady.emit(self._response_text)
        logger.info("[AssistantController] Task finished")

    def _on_token_received(self, token: str):
        """Handle token received."""
        logger.info(f"[AssistantController] Token received from worker: len={len(token)}, response_text_len={len(self._response_text)}")
        if len(self._response_text) < MAX_OUTPUT_LENGTH:
            self._response_text += token
            self.tokenReceived.emit(token)
        else:
            logger.warning(f"[AssistantController] Token dropped due to MAX_OUTPUT_LENGTH limit: {MAX_OUTPUT_LENGTH}")

    def _on_error(self, error: str):
        """Handle error."""
        self.errorOccurred.emit(error)
        self.runningChanged.emit(False)
        self._current_worker = None
        logger.error(f"[AssistantController] Error: {error}")

    def _on_status_changed(self, status: str):
        """Handle status changed."""
        self.statusChanged.emit(status)

    def _resolve_response_length(self, action: dict | None) -> str:
        value = (action or {}).get("response_length", "medium")
        if value not in RESPONSE_LENGTH_TO_NUM_PREDICT:
            return "medium"
        return value

    def _build_generation_options(self, settings, action: dict | None = None) -> dict:
        response_length = self._resolve_response_length(action)
        return {
            "num_predict": RESPONSE_LENGTH_TO_NUM_PREDICT[response_length],
            "num_ctx": settings.num_ctx,
            "temperature": settings.temperature,
        }

    def _run_ai_task(self, prompt: str, action_id: str = "", action: dict | None = None):
        """Run an AI task with the given prompt."""
        if self._worker_manager.is_running():
            logger.warning("[AssistantController] Task already running")
            self.errorOccurred.emit("이미 실행 중인 작업이 있습니다")
            return

        settings = self._load_settings(refresh=True)
        if not settings.chat_model:
            self.errorOccurred.emit("모델이 선택되지 않았습니다")
            return

        options = self._build_generation_options(settings, action)

        logger.info(
            f"[AssistantController] Running AI task: action_id={action_id}, "
            f"model={settings.chat_model}, prompt_len={len(prompt)}, "
            f"timeout={settings.timeout}, stream={settings.streaming}, "
            f"options={options}, keep_alive={settings.keep_alive}, "
            f"response_length={self._resolve_response_length(action)}"
        )
        self._response_text = ""
        self.runningChanged.emit(True)
        self.statusChanged.emit("실행 중...")

        self._current_worker = self._worker_manager.run_task(
            prompt=prompt,
            model=settings.chat_model,
            base_url=settings.base_url,
            timeout=settings.timeout,
            stream=settings.streaming,
            options=options,
            keep_alive=settings.keep_alive,
            first_token_timeout=settings.first_token_timeout,
            idle_timeout=settings.idle_timeout,
            action_id=action_id,
        )

        self._current_worker.signals.finished.connect(self._on_worker_finished)
        self._current_worker.signals.tokenReceived.connect(self._on_token_received)
        self._current_worker.signals.errorOccurred.connect(self._on_error)
        self._current_worker.signals.statusChanged.connect(self._on_status_changed)

    @pyqtSlot(str, str)
    def runTask(self, action_id: str, content: str):
        """Run an AI task based on action ID."""
        if not content or not content.strip():
            self.errorOccurred.emit("현재 노트를 선택한 뒤 실행해주세요.")
            return

        action = self._action_registry.get_action(action_id)
        if not action:
            logger.warning(f"[AssistantController] Action not found: {action_id}")
            self.errorOccurred.emit(f"알 수 없는 작업: {action_id}")
            return

        truncated_content = content[:MAX_CONTENT_LENGTH]

        # Get prompt summary with fallback info for logging
        summary = self._prompt_service._repo.get_prompt_summary_for_action(action.id)
        if summary:
            prompt_doc_id = summary.get("prompt_doc_id", action.id)
            prompt = summary.get("prompt")
            fallback_used = summary.get("fallback_used", False)
            fallback_reason = summary.get("fallback_reason", "")
        else:
            prompt_doc_id = action.id
            prompt = None
            fallback_used = True
            fallback_reason = "summary_not_found"

        # Log runtime prompt resolution
        if prompt:
            logger.info(
                f"[AssistantController] AI task: action_id={action.id}, "
                f"prompt_doc_id={prompt_doc_id}, "
                f"title={prompt.get('title', '')[:50]}, "
                f"source_type={prompt.get('source_type', '')}, "
                f"fallback_used={fallback_used}, "
                f"fallback_reason={fallback_reason if fallback_reason else 'none'}"
            )
        else:
            logger.warning(
                f"[AssistantController] AI task fallback: action_id={action.id}, "
                f"prompt_doc_id={prompt_doc_id}, "
                f"fallback_used={fallback_used}, "
                f"fallback_reason={fallback_reason}"
            )

        prompt_template = self._prompt_service.get_effective_prompt(action.id)
        if not prompt_template:
            logger.warning(f"[AssistantController] Prompt template not found: {action.id}")
            self.errorOccurred.emit(f"프롬프트를 찾을 수 없습니다: {action.id}")
            return

        context = {
            "current_note": truncated_content,
            "content": truncated_content,
            "CONTENT": truncated_content,
            "SELECTION": truncated_content,
            "TITLE": "",
            "TAGS": "",
            "CONTEXT": "",
            "QUESTION": "",
        }

        if action.rag and action_id == "current_note_qa":
            chunks = self._chunker.chunk_text(truncated_content)
            retrieved_chunks = self._retriever.retrieve(chunks, self._last_query or "")
            self._retrieved_context = self._retriever.format_context(retrieved_chunks)
            context["retrieved_context"] = self._retrieved_context
            context["question"] = self._last_query or ""
            context["CONTEXT"] = self._retrieved_context
            context["QUESTION"] = self._last_query or ""

        prompt = self._prompt_service.render_prompt(action.id, context)
        logger.info(
            f"[AssistantController] Task prepared: action_id={action.id}, "
            f"content_len={len(truncated_content)}, prompt_len={len(prompt)}"
        )
        action_dict = {
            "response_length": getattr(action, "response_length", "medium"),
        }
        self._run_ai_task(prompt, action_id=action.id, action=action_dict)

    @pyqtSlot(str, str, str, str, str)
    def runCustomAction(
        self,
        action_id: str,
        user_input: str,
        current_note_json: str,
        selection: str,
        chat_history_json: str,
    ):
        """Run a custom AI action with full context."""
        import json

        if self._worker_manager.is_running():
            self.errorOccurred.emit("이미 실행 중인 작업이 있습니다")
            return

        current_note = None
        chat_history = []

        try:
            if current_note_json:
                current_note = json.loads(current_note_json)
        except json.JSONDecodeError:
            logger.warning("[AssistantController] Failed to parse current_note_json")

        try:
            if chat_history_json:
                chat_history = json.loads(chat_history_json)
        except json.JSONDecodeError:
            logger.warning("[AssistantController] Failed to parse chat_history_json")

        action = self._prompt_service.get_action(action_id)

        if not action:
            logger.warning(f"[AssistantController] runCustomAction: Action not found: {action_id}")
            self.errorOccurred.emit(f"알 수 없는 작업: {action_id}")
            return

        if not action.get("enabled", True):
            self.errorOccurred.emit("이 AI 기능은 비활성화되어 있습니다.")
            return

        if action.get("archived", False):
            self.errorOccurred.emit("이 AI 기능은 삭제되었습니다.")
            return

        from .prompt_variable_analyzer import PromptVariableAnalyzer
        from .action_execution_context_builder import ActionExecutionContextBuilder

        binding = self._prompt_service.repository.get_binding(action_id)
        prompt_doc_id = binding.get("prompt_doc_id") if binding else None
        prompt_doc = None

        if prompt_doc_id:
            prompt_doc = self._prompt_service.get_prompt_document(prompt_doc_id)

        if not prompt_doc:
            prompt_doc = self._prompt_service.get_prompt_document(action_id)

        if not prompt_doc:
            logger.warning(f"[AssistantController] runCustomAction: Prompt not found for action: {action_id}")
            self.errorOccurred.emit("연결된 프롬프트를 찾을 수 없습니다.")
            return

        if prompt_doc.get("archived", False):
            self.errorOccurred.emit("연결된 프롬프트가 삭제되었습니다.")
            return

        content_md = prompt_doc.get("content_md", "")
        explicit_input_mode = action.get("input_mode", "auto")

        validation = PromptVariableAnalyzer.build_validation_result(
            action_id, prompt_doc_id or prompt_doc.get("prompt_doc_id"), content_md, explicit_input_mode
        )

        inferred_input_mode = validation.get("inferred_input_mode", explicit_input_mode)
        if explicit_input_mode and explicit_input_mode != "auto":
            inferred_input_mode = explicit_input_mode

        if action_id == "current_note_qa" and inferred_input_mode == "chat_only":
            logger.info("[AssistantController] current_note_qa: forcing input_mode to note_and_chat")
            inferred_input_mode = "note_and_chat"

        preconditions = ActionExecutionContextBuilder.validate_execution_preconditions(
            action, inferred_input_mode, current_note, user_input, selection
        )

        if not preconditions["valid"]:
            for error in preconditions["errors"]:
                self.errorOccurred.emit(error)
            return

        if preconditions["warnings"]:
            for warning in preconditions["warnings"]:
                logger.warning(f"[AssistantController] runCustomAction warning: {warning}")

        use_rag = action.get("use_rag", False)
        retriever = self._retriever if use_rag else None

        context = ActionExecutionContextBuilder.build_context_for_action(
            action, prompt_doc, user_input, current_note, selection, chat_history, retriever
        )

        rendered_prompt = self._prompt_service.render_prompt(action_id, context)
        if not rendered_prompt:
            logger.warning(f"[AssistantController] runCustomAction: Failed to render prompt: {action_id}")
            self.errorOccurred.emit("프롬프트 렌더링에 실패했습니다.")
            return

        logger.info(
            f"[AssistantController] runCustomAction: action_id={action_id}, "
            f"prompt_doc_id={prompt_doc.get('prompt_doc_id')}, "
            f"input_mode={inferred_input_mode}, "
            f"use_rag={use_rag}, "
            f"variables={validation.get('variables', [])}, "
            f"content_len={len(context.get('CONTENT', ''))}, "
            f"user_input_len={len(context.get('USER_INPUT', ''))}, "
            f"question_len={len(context.get('QUESTION', ''))}, "
            f"context_len={len(context.get('CONTEXT', ''))}, "
            f"selection_len={len(context.get('SELECTION', ''))}, "
            f"prompt_len={len(rendered_prompt)}"
        )

        self._run_ai_task(rendered_prompt, action_id=action_id, action=action)

    @pyqtSlot(str, str)
    def askQuestion(self, content: str, question: str):
        """Ask a question about the current note."""
        if self._worker_manager.is_running():
            self.errorOccurred.emit("이미 실행 중인 작업이 있습니다")
            return

        if not content or not content.strip():
            self.errorOccurred.emit("현재 노트를 선택한 뒤 실행해주세요.")
            return

        if not question or not question.strip():
            self.errorOccurred.emit("이 기능은 입력창에 질문이 필요합니다.")
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
        self._run_ai_task(prompt, action_id="test_prompt")

    @pyqtSlot()
    def cancel(self):
        """Cancel the current operation."""
        if self._worker_manager.is_running():
            self._worker_manager.cancel_current()
        self.statusChanged.emit("중지됨")
        self.runningChanged.emit(False)
        logger.info("[AssistantController] Task cancelled")

    @pyqtSlot()
    def reloadSettings(self):
        """Reload AI settings from disk and apply to helper components."""
        settings = self._load_settings(refresh=True)
        logger.info(
            "[AssistantController] Reloaded AI settings (chat_model=%s, performance_mode=%s)",
            settings.chat_model,
            settings.performance_mode,
        )
        self.statusChanged.emit(self.status)

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

    @pyqtSlot(result=str)
    def getOrCreateAIResultFolder(self) -> str:
        """Find or create 'AI결과' folder in root and return its ID."""
        if not self._folder_controller:
            logger.warning("[AssistantController] Folder controller not set")
            return ""

        try:
            all_folders = self._folder_controller.getAllFoldersJson()
            import json
            folders = json.loads(all_folders) if all_folders else []

            for folder in folders:
                if folder.get("name") == "AI결과" and not folder.get("parent_id"):
                    return folder.get("id", "")

            folder_id = self._folder_controller.createFolder("AI결과", "#3B82F6", "")
            logger.info(f"[AssistantController] Created AI결과 folder: {folder_id}")
            return folder_id
        except Exception as e:
            logger.error(f"[AssistantController] Failed to get/create AI결과 folder: {e}")
            return ""
