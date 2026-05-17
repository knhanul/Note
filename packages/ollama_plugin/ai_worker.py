"""AI Worker for asynchronous Ollama operations."""

import logging
import time
import urllib.request
import urllib.error
import json
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool

logger = logging.getLogger(__name__)


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
            url = f"{self.base_url}/api/generate"
            data = {
                "model": self.model,
                "prompt": self.prompt,
                "stream": self.stream,
            }

            if self.options:
                data["options"] = self.options

            if self.keep_alive:
                data["keep_alive"] = self.keep_alive

            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                method="POST"
            )
            request.add_header("Content-Type", "application/json")

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
                    return

                if self.stream:
                    buffer = ""
                    for line in response:
                        if self._is_cancelled:
                            self.signals.statusChanged.emit("중지됨")
                            self.signals.finished.emit()
                            return

                        if line:
                            buffer += line.decode("utf-8")
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                try:
                                    data = json.loads(line)
                                    if first_token_time is None:
                                        first_token_time = time.time() - start_time
                                        logger.info(
                                            f"[AIWorker] First token received: {first_token_time:.2f}s, "
                                            f"action_id={self.action_id}"
                                        )
                                    if "response" in data:
                                        token = data["response"]
                                        logger.info(f"[AIWorker] Emitting token: len={len(token)}, action_id={self.action_id}")
                                        self.signals.tokenReceived.emit(token)
                                    if data.get("done", False):
                                        total_time = time.time() - start_time
                                        load_duration_ms = data.get("load_duration", 0)
                                        total_duration_ms = data.get("total_duration", 0)
                                        load_duration_s = load_duration_ms / 1000 if load_duration_ms else 0
                                        total_duration_s = total_duration_ms / 1000 if total_duration_ms else 0
                                        logger.info(
                                            f"[AIWorker] Stream complete: total={total_time:.2f}s, "
                                            f"first_token={first_token_time:.2f}s, "
                                            f"load_duration={load_duration_s:.2f}s, "
                                            f"total_duration={total_duration_s:.2f}s, "
                                            f"action_id={self.action_id}"
                                        )
                                except json.JSONDecodeError:
                                    continue

                    self.signals.statusChanged.emit("완료")
                    self.signals.resultReady.emit("응답 완료")
                else:
                    body = response.read().decode("utf-8")
                    data = json.loads(body)
                    first_token_time = time.time() - start_time
                    load_duration_ms = data.get("load_duration", 0)
                    total_duration_ms = data.get("total_duration", 0)
                    load_duration_s = load_duration_ms / 1000 if load_duration_ms else 0
                    total_duration_s = total_duration_ms / 1000 if total_duration_ms else 0
                    logger.info(
                        f"[AIWorker] Non-stream response: first_token={first_token_time:.2f}s, "
                        f"load_duration={load_duration_s:.2f}s, "
                        f"total_duration={total_duration_s:.2f}s, "
                        f"action_id={self.action_id}"
                    )
                    if "response" in data:
                        token = data["response"]
                        logger.info(f"[AIWorker] Emitting non-stream token: len={len(token)}, action_id={self.action_id}")
                        self.signals.tokenReceived.emit(token)
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
        logger.info(
            f"[AIWorker] Task finished: total={total_time:.2f}s, "
            f"first_token={first_token_time if first_token_time else 'N/A'}s, "
            f"action_id={self.action_id}"
        )
        self.signals.finished.emit()


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
