import logging
import subprocess
import sys
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal

logger = logging.getLogger(__name__)


class ToolController(QObject):
    """Controller for launching external tools."""

    toolExecutionFailed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Determine tools directory based on execution environment
        if getattr(sys, 'frozen', False):
            # Running as executable
            prog_dir = Path(sys.executable).parent
            self._tools_dir = prog_dir / "tools"
        else:
            # Running as script
            self._tools_dir = Path(__file__).parent.parent / "tools"

    @pyqtSlot()
    def launchHwpConversionTool(self):
        """Launch the HWP to HWPX conversion tool."""
        tool_path = self._tools_dir / "HWP2HWPX_Converter.exe"
        
        if not tool_path.exists():
            error_msg = f"도구를 찾을 수 없습니다: {tool_path}"
            logger.error(f"[ToolController] {error_msg}")
            self.toolExecutionFailed.emit(error_msg)
            return

        try:
            logger.info(f"[ToolController] Launching HWP conversion tool: {tool_path}")
            subprocess.Popen(
                [str(tool_path)],
                cwd=str(self._tools_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
        except Exception as e:
            error_msg = f"도구 실행 실패: {e}"
            logger.error(f"[ToolController] {error_msg}")
            self.toolExecutionFailed.emit(error_msg)

    @pyqtSlot()
    def launchOllamaModelTool(self):
        """Launch the Ollama model registration tool."""
        tool_path = self._tools_dir / "simple_ollama_model_register.exe"
        
        if not tool_path.exists():
            error_msg = f"도구를 찾을 수 없습니다: {tool_path}"
            logger.error(f"[ToolController] {error_msg}")
            self.toolExecutionFailed.emit(error_msg)
            return

        try:
            logger.info(f"[ToolController] Launching Ollama model tool: {tool_path}")
            subprocess.Popen(
                [str(tool_path)],
                cwd=str(self._tools_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
        except Exception as e:
            error_msg = f"도구 실행 실패: {e}"
            logger.error(f"[ToolController] {error_msg}")
            self.toolExecutionFailed.emit(error_msg)
