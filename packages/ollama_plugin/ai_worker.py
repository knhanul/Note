"""AI Worker for asynchronous Ollama operations."""

import logging
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

    def __init__(self, prompt: str, model: str, base_url: str = "http://localhost:11434", timeout: int = 120):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.signals = AIWorkerSignals()
        self._is_cancelled = False

    def cancel(self):
        """Cancel the current operation."""
        self._is_cancelled = True
        logger.info("[AIWorker] Operation cancelled")

    def run(self):
        """Run the AI operation."""
        if not self.model:
            self.signals.errorOccurred.emit("모델이 선택되지 않았습니다")
            self.signals.finished.emit()
            return

        if not self.prompt:
            self.signals.errorOccurred.emit("프롬프트가 없습니다")
            self.signals.finished.emit()
            return

        self.signals.statusChanged.emit("실행 중...")

        try:
            url = f"{self.base_url}/api/generate"
            data = {
                "model": self.model,
                "prompt": self.prompt,
                "stream": True
            }

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
                                if "response" in data:
                                    token = data["response"]
                                    self.signals.tokenReceived.emit(token)
                            except json.JSONDecodeError:
                                continue

                self.signals.statusChanged.emit("완료")
                self.signals.resultReady.emit("응답 완료")

        except urllib.error.URLError as e:
            logger.error(f"[AIWorker] Connection error: {e}")
            error_msg = "연결 실패: Ollama가 실행 중인지 확인하세요"
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

        self.signals.finished.emit()


class AIWorkerManager:
    """Manager for AI workers."""

    def __init__(self):
        self._pool = QThreadPool.globalInstance()
        self._current_worker: AIWorker | None = None
        logger.info(f"[AIWorkerManager] Thread pool max threads: {self._pool.maxThreadCount()}")

    def run_task(self, prompt: str, model: str, base_url: str = "http://localhost:11434", timeout: int = 120) -> AIWorker:
        """Run an AI task."""
        if self._current_worker and self._current_worker.signals:
            logger.warning("[AIWorkerManager] Task already running")
            return self._current_worker

        worker = AIWorker(prompt, model, base_url, timeout)
        self._current_worker = worker
        self._pool.start(worker)
        logger.info("[AIWorkerManager] Task started")
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
