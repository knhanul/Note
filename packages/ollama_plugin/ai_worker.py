"""AI Worker for asynchronous Ollama operations."""

import logging
import time
import urllib.request
import urllib.error
import json
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool

logger = logging.getLogger(__name__)

DEBUG_MODE = False  # Set to True for debug logging


def extract_response_text(chunk: dict) -> str:
    """Extract actual text from Ollama streaming chunk.
    
    Supports both /api/generate (chunk["response"]) and /api/chat (chunk["message"]["content"]) formats.
    Returns empty string if no valid text found.
    """
    # /api/generate format: {"response": "text", ...}
    if "response" in chunk:
        text = chunk["response"]
        if isinstance(text, str):
            return text
    
    # /api/chat format: {"message": {"content": "text", ...}, ...}
    if "message" in chunk and isinstance(chunk["message"], dict):
        content = chunk["message"].get("content")
        if isinstance(content, str):
            return content
    
    return ""


class AIWorkerSignals(QObject):
    """Signals for AI worker."""
    statusChanged = pyqtSignal(str)
    tokenReceived = pyqtSignal(str)
    resultReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    finished = pyqtSignal()


class AIWorker(QRunnable):
    """Runnable worker for AI operations."""

    _warned_q8_models: set[str] = set()

    def __init__(
        self,
        prompt: str,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
        stream: bool = True,
        options: dict | None = None,
        keep_alive: str = "10m",
        first_token_timeout: int = 180,
        idle_timeout: int = 60,
        action_id: str = "",
    ):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.stream = stream
        self.options = options or {}
        self.keep_alive = keep_alive
        self.first_token_timeout = first_token_timeout
        self.idle_timeout = idle_timeout
        self.action_id = action_id
        self.signals = AIWorkerSignals()
        self._is_cancelled = False

    def cancel(self):
        """Cancel the current operation."""
        self._is_cancelled = True
        logger.info("[AIWorker] Operation cancelled")

    def run(self):
        """Run the AI operation."""
        start_time = time.time()
        first_token_time = None
        accumulated_response = ""
        chunk_count = 0
        fallback_attempted = False

        if not self.model:
            self.signals.errorOccurred.emit("모델이 선택되지 않았습니다")
            self.signals.finished.emit()
            return

        if not self.prompt:
            self.signals.errorOccurred.emit("프롬프트가 없습니다")
            self.signals.finished.emit()
            return

        self.signals.statusChanged.emit("실행 중...")

        logger.info(
            f"[AIWorker] Starting task: action_id={self.action_id}, model={self.model}, "
            f"prompt_len={len(self.prompt)}, stream={self.stream}, timeout={self.timeout}, "
            f"first_token_timeout={self.first_token_timeout}, idle_timeout={self.idle_timeout}, "
            f"options={self.options}, keep_alive={self.keep_alive}"
        )

        # Model recommendation based on model name
        model_lower = self.model.lower()
        if "q8" in model_lower and model_lower not in self._warned_q8_models:
            self._warned_q8_models.add(model_lower)
            logger.warning(
                f"[AIWorker] Q8 model detected: {self.model}. "
                f"Q8 models prioritize quality but are very slow on CPU office PCs. "
                f"Consider using Q4 or smaller models (1.5B-2B) for better performance."
            )

        try:
            # Try stream=True first, fallback to stream=False if empty response
            response_text = self._execute_request(start_time, first_token_time, accumulated_response, chunk_count, fallback_attempted)
            
            # Check if response is empty and fallback not yet attempted
            if not response_text and not fallback_attempted and self.stream:
                logger.info("[AIWorker] Empty response with stream=True, retrying with stream=False")
                fallback_attempted = True
                response_text = self._execute_request(start_time, first_token_time, accumulated_response, chunk_count, fallback_attempted)
            
            # Handle empty response after all attempts
            if not response_text:
                logger.warning(f"[AIWorker] Empty response after all attempts, action_id={self.action_id}")
                self.signals.errorOccurred.emit("AI 응답이 비어 있습니다. 모델 또는 응답 파싱을 확인해 주세요.")
                self.signals.finished.emit()
                return
            
            self.signals.statusChanged.emit("완료")
            self.signals.resultReady.emit("응답 완료")

        except urllib.error.URLError as e:
            logger.error(f"[AIWorker] Connection error: {e}")
            error_msg = "연결 실패: Ollama가 실행 중인지 확인하세요"
            raw_reason = str(getattr(e, "reason", "") or "")
            if "timed out" in raw_reason.lower() or "timeout" in raw_reason.lower():
                error_msg = "AI 응답 시간이 초과되었습니다. 더 가벼운 모델을 선택하거나 입력 길이를 줄여 다시 시도해보세요."
            if hasattr(e, 'read'):
                try:
                    error_data = e.read().decode("utf-8")
                    if error_data:
                        error_msg = f"오류: {error_data}"
                except:
                    pass
            self.signals.errorOccurred.emit(error_msg)
        except Exception as e:
            logger.error(f"[AIWorker] Error: {e}")
            self.signals.errorOccurred.emit(f"오류: {str(e)}")

        total_time = time.time() - start_time
        first_token_str = f"{first_token_time:.2f}s" if first_token_time else "N/A"
        logger.info(
            f"[AIWorker] Task finished: total={total_time:.2f}s, "
            f"first_token={first_token_str}, "
            f"action_id={self.action_id}"
        )
        self.signals.finished.emit()

    def _execute_request(self, start_time, first_token_time, accumulated_response, chunk_count, fallback_attempted):
        """Execute the Ollama API request and return accumulated response."""
        use_stream = self.stream and not fallback_attempted
        
        # FIXED: Use /api/generate only (disable /api/chat auto-switch for this issue)
        # TODO: Re-enable /api/chat path after verifying fix
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": self.prompt,
            "stream": use_stream,
            "think": False,  # Disable thinking to prevent token exhaustion
        }

        if self.options:
            data["options"] = self.options

        if self.keep_alive:
            data["keep_alive"] = self.keep_alive

        # Log payload options for debugging
        logger.info(
            f"[AIWorker] Request payload: model={self.model}, stream={use_stream}, "
            f"think={data.get('think')}, num_predict={self.options.get('num_predict', 'default')}, "
            f"num_ctx={self.options.get('num_ctx', 'default')}, temperature={self.options.get('temperature', 'default')}, "
            f"action_id={self.action_id}"
        )

        request = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            method="POST"
        )
        request.add_header("Content-Type", "application/json")

        accumulated_response = ""
        chunk_count = 0
        first_token_time = None

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    error_msg = f"오류: {response.status}"
                    try:
                        error_data = response.read().decode("utf-8")
                        error_msg += f" - {error_data}"
                    except:
                        pass
                    self.signals.errorOccurred.emit(error_msg)
                    self.signals.finished.emit()
                    return ""

                if use_stream:
                    buffer = ""
                    accumulated_thinking = ""  # Track thinking separately
                    for line in response:
                        if self._is_cancelled:
                            self.signals.statusChanged.emit("중지됨")
                            self.signals.finished.emit()
                            return ""

                        if line:
                            buffer += line.decode("utf-8")
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                try:
                                    chunk = json.loads(line)
                                    chunk_count += 1
                                    
                                    # Debug log first 3 chunks
                                    if DEBUG_MODE and chunk_count <= 3:
                                        logger.debug(f"[AIWorker] Raw chunk {chunk_count}: {chunk}")
                                    
                                    # Extract thinking (if present) - don't emit to UI
                                    thinking = chunk.get("thinking", "")
                                    if thinking:
                                        accumulated_thinking += thinking
                                        if DEBUG_MODE:
                                            logger.debug(f"[AIWorker] Thinking chunk: {len(thinking)} chars")
                                    
                                    # Extract text using helper function (response field)
                                    token = extract_response_text(chunk)
                                    
                                    # Log if eval_count is present but token is empty
                                    if not token and chunk.get("eval_count", 0) > 0:
                                        logger.warning(f"[AIWorker] Chunk has eval_count={chunk.get('eval_count')} but empty token text. Chunk keys: {list(chunk.keys())}")
                                    
                                    # Skip empty tokens for first token detection
                                    if first_token_time is None and token:
                                        first_token_time = time.time() - start_time
                                        logger.info(
                                            f"[AIWorker] First token received: {first_token_time:.2f}s, "
                                            f"action_id={self.action_id}"
                                        )
                                    
                                    # Only emit non-empty response tokens
                                    if token:
                                        logger.info(f"[AIWorker] Emitting token: len={len(token)}, action_id={self.action_id}")
                                        self.signals.tokenReceived.emit(token)
                                        accumulated_response += token
                                    
                                    if chunk.get("done", False):
                                        total_time = time.time() - start_time
                                        # Handle both ms and ns duration values
                                        load_duration_raw = chunk.get("load_duration", 0)
                                        total_duration_raw = chunk.get("total_duration", 0)
                                        
                                        # Convert to seconds (Ollama returns ns, so values like 129552398300000000 need /1e9)
                                        # If value > 1e11 (100+ seconds in ns), it's likely in ns
                                        if load_duration_raw > 1e11:
                                            load_duration_s = load_duration_raw / 1e9  # ns to seconds
                                        else:
                                            load_duration_s = load_duration_raw / 1000 if load_duration_raw else 0
                                            
                                        if total_duration_raw > 1e11:
                                            total_duration_s = total_duration_raw / 1e9  # ns to seconds
                                        else:
                                            total_duration_s = total_duration_raw / 1000 if total_duration_raw else 0
                                        
                                        done_reason = chunk.get("done_reason", "")
                                        eval_count = chunk.get("eval_count", 0)
                                        prompt_eval_count = chunk.get("prompt_eval_count", 0)
                                        response_chars = len(accumulated_response)
                                        thinking_chars = len(accumulated_thinking)
                                        
                                        first_token_str = f"{first_token_time:.2f}s" if first_token_time else "N/A"
                                        logger.info(
                                            f"[AIWorker] Stream complete: total={total_time:.2f}s, "
                                            f"first_token={first_token_str}, "
                                            f"load_duration={load_duration_s:.2f}s, "
                                            f"total_duration={total_duration_s:.2f}s, "
                                            f"done_reason={done_reason}, "
                                            f"eval_count={eval_count}, "
                                            f"prompt_eval_count={prompt_eval_count}, "
                                            f"response_chars={response_chars}, "
                                            f"thinking_chars={thinking_chars}, "
                                            f"action_id={self.action_id}"
                                        )
                                        
                                        # Check for thinking-only termination
                                        if response_chars == 0 and thinking_chars > 0:
                                            logger.warning(
                                                f"[AIWorker] Thinking-only termination detected: "
                                                f"thinking_chars={thinking_chars}, done_reason={done_reason}. "
                                                f"Consider increasing num_predict or disabling think."
                                            )
                                except json.JSONDecodeError:
                                    continue

                    return accumulated_response
                else:
                    body = response.read().decode("utf-8")
                    data = json.loads(body)
                    first_token_time = time.time() - start_time
                    
                    # Handle both ms and ns duration values
                    load_duration_raw = data.get("load_duration", 0)
                    total_duration_raw = data.get("total_duration", 0)
                    
                    # If value > 1e11 (100+ seconds in ns), it's likely in ns
                    if load_duration_raw > 1e11:
                        load_duration_s = load_duration_raw / 1e9
                    else:
                        load_duration_s = load_duration_raw / 1000 if load_duration_raw else 0
                        
                    if total_duration_raw > 1e11:
                        total_duration_s = total_duration_raw / 1e9
                    else:
                        total_duration_s = total_duration_raw / 1000 if total_duration_raw else 0
                    
                    # Extract thinking (if present) - don't emit to UI
                    thinking = data.get("thinking", "")
                    thinking_chars = len(thinking) if thinking else 0
                    
                    logger.info(
                        f"[AIWorker] Non-stream response: first_token={first_token_time:.2f}s, "
                        f"load_duration={load_duration_s:.2f}s, "
                        f"total_duration={total_duration_s:.2f}s, "
                        f"thinking_chars={thinking_chars}, "
                        f"action_id={self.action_id}"
                    )
                    
                    # Use helper function to extract text
                    token = extract_response_text(data)
                    if token:
                        logger.info(f"[AIWorker] Emitting non-stream token: len={len(token)}, action_id={self.action_id}")
                        self.signals.tokenReceived.emit(token)
                        accumulated_response = token
                    else:
                        # Check for thinking-only response
                        if thinking_chars > 0:
                            logger.warning(
                                f"[AIWorker] Non-stream response has thinking only (no response). "
                                f"thinking_chars={thinking_chars}. Consider increasing num_predict or disabling think."
                            )
                        else:
                            logger.warning(f"[AIWorker] Non-stream response has empty token. Data keys: {list(data.keys())}")
                    
                    return accumulated_response

        except urllib.error.URLError as e:
            logger.error(f"[AIWorker] Connection error in _execute_request: {e}")
            raise
        except Exception as e:
            logger.error(f"[AIWorker] Error in _execute_request: {e}")
            raise

        return accumulated_response


class AIWorkerManager:
    """Manager for AI workers."""

    def __init__(self):
        self._pool = QThreadPool.globalInstance()
        self._current_worker: AIWorker | None = None
        logger.info(f"[AIWorkerManager] Thread pool max threads: {self._pool.maxThreadCount()}")

    def run_task(
        self,
        prompt: str,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
        stream: bool = True,
        options: dict | None = None,
        keep_alive: str = "10m",
        first_token_timeout: int = 180,
        idle_timeout: int = 60,
        action_id: str = "",
    ) -> AIWorker:
        """Run an AI task."""
        if self._current_worker and self._current_worker.signals:
            logger.warning("[AIWorkerManager] Task already running")
            return self._current_worker

        worker = AIWorker(
            prompt=prompt,
            model=model,
            base_url=base_url,
            timeout=timeout,
            stream=stream,
            options=options,
            keep_alive=keep_alive,
            first_token_timeout=first_token_timeout,
            idle_timeout=idle_timeout,
            action_id=action_id,
        )
        self._current_worker = worker
        self._pool.start(worker)
        logger.info(f"[AIWorkerManager] Task started: action_id={action_id}")
        return worker

    def cancel_current(self):
        """Cancel the current task."""
        if self._current_worker:
            self._current_worker.cancel()
            logger.info("[AIWorkerManager] Current task cancelled")

    def is_running(self) -> bool:
        """Check if a task is running."""
        return self._current_worker is not None

    def clear_worker(self):
        """Clear the current worker reference."""
        self._current_worker = None
