"""HWP import service for Note2.

This module provides HWP file import capabilities by reusing existing
hwp_converter.py and hwpx_importer.
"""

from pathlib import Path
from typing import Optional, Tuple

from services.hwp_converter import convert_hwp_to_hwpx_via_com
from services.hwpx_importer import hwpx_to_markdown


def convert_hwp_to_markdown_text(hwp_path: str) -> Tuple[str, list[str]]:
    """Convert HWP file to Markdown text.

    This function attempts to convert HWP to HWPX via COM, then to Markdown.
    If COM is not available, it falls back to gethwp (if available).

    Args:
        hwp_path: Path to the HWP file.

    Returns:
        Tuple of (markdown_text, warnings).
        Returns ("", [warning]) on failure.
    """
    warnings: list[str] = []
    path = Path(hwp_path)

    if not path.exists():
        warnings.append(f"HWP file not found: {hwp_path}")
        return "", warnings

    if path.suffix.lower() != ".hwp":
        warnings.append(f"Expected .hwp file, got: {path.suffix}")
        return "", warnings

    hwpx_path = _try_convert_hwp_to_hwpx(hwp_path)
    if hwpx_path:
        try:
            markdown = hwpx_to_markdown(hwpx_path)
            if markdown:
                return markdown, warnings
            warnings.append("HWPX to Markdown conversion returned empty result")
        except Exception as exc:
            warnings.append(f"HWPX to Markdown conversion failed: {exc}")
        finally:
            _cleanup_temp_hwpx(hwpx_path)

    fallback_markdown = _try_fallback_import(hwp_path)
    if fallback_markdown:
        warnings.append("Used fallback import (gethwp)")
        return fallback_markdown, warnings

    warnings.append("All HWP import methods failed")
    return "", warnings


def _try_convert_hwp_to_hwpx(hwp_path: str) -> Optional[str]:
    """Try to convert HWP to HWPX via COM."""
    try:
        return convert_hwp_to_hwpx_via_com(hwp_path)
    except Exception:
        return None


def _try_fallback_import(hwp_path: str) -> str:
    """Try fallback import via gethwp."""
    try:
        import gethwp
        return gethwp.read_hwp(hwp_path) or ""
    except ImportError:
        return ""
    except Exception:
        return ""


def _cleanup_temp_hwpx(hwpx_path: Optional[str]) -> None:
    """Clean up temporary HWPX file."""
    if hwpx_path is None:
        return
    try:
        path = Path(hwpx_path)
        if path.exists():
            path.unlink()
        parent = path.parent
        if parent.exists() and parent.name.startswith("hwp_import_"):
            parent.rmdir()
    except Exception:
        pass


def import_hwpx_as_markdown_text(hwpx_path: str) -> Tuple[str, list[str]]:
    """Convert HWPX file directly to Markdown text.

    Args:
        hwpx_path: Path to the HWPX file.

    Returns:
        Tuple of (markdown_text, warnings).
        Returns ("", [warning]) on failure.
    """
    warnings: list[str] = []
    path = Path(hwpx_path)

    if not path.exists():
        warnings.append(f"HWPX file not found: {hwpx_path}")
        return "", warnings

    if path.suffix.lower() != ".hwpx":
        warnings.append(f"Expected .hwpx file, got: {path.suffix}")
        return "", warnings

    try:
        markdown = hwpx_to_markdown(hwpx_path)
        if markdown:
            return markdown, warnings
        warnings.append("HWPX to Markdown conversion returned empty result")
    except Exception as exc:
        warnings.append(f"HWPX to Markdown conversion failed: {exc}")

    fallback_markdown = _try_hwpx_fallback_import(hwpx_path)
    if fallback_markdown:
        warnings.append("Used fallback import (gethwp)")
        return fallback_markdown, warnings

    warnings.append("HWPX import failed")
    return "", warnings


def _try_hwpx_fallback_import(hwpx_path: str) -> str:
    """Try fallback import via gethwp for HWPX."""
    try:
        import gethwp
        return gethwp.read_hwpx(hwpx_path) or ""
    except ImportError:
        return ""
    except Exception:
        return ""


__all__ = [
    "convert_hwp_to_markdown_text",
    "import_hwpx_as_markdown_text",
]
