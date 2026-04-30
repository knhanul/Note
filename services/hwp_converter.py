"""HWP to HWPX converter via Hancom COM automation.

This module is import-safe: failures return None instead of raising,
so callers can fallback to legacy parsing paths.
"""
from __future__ import annotations

import logging
from pathlib import Path
import tempfile


logger = logging.getLogger(__name__)

_COM_PROG_IDS = ["HWPFrame.HwpObject", "Hwp.HwpObject"]


def convert_hwp_to_hwpx_via_com(hwp_path: str, output_dir: str | None = None) -> str | None:
    """Convert .hwp to .hwpx using Hancom COM.

    Args:
        hwp_path: Source .hwp file path.
        output_dir: Optional directory for converted .hwpx.
            If not provided, a temporary directory is used.

    Returns:
        Converted .hwpx path on success, otherwise None.
    """
    source = Path(hwp_path)
    if source.suffix.lower() != ".hwp":
        logger.warning("convert_hwp_to_hwpx_via_com called with non-.hwp: %s", hwp_path)
        return None

    if not source.exists() or not source.is_file():
        logger.warning("HWP source not found: %s", hwp_path)
        return None

    target_dir = _resolve_output_dir(output_dir)
    if target_dir is None:
        return None

    target_path = target_dir / f"{source.stem}.hwpx"

    com_modules = _load_com_modules()
    if com_modules is None:
        return None
    pythoncom, win32_client = com_modules

    abs_hwp = str(source.resolve())
    abs_hwpx = str(target_path.resolve())

    pythoncom.CoInitialize()
    hwp = None

    try:
        hwp = _create_hwp_com_object(win32_client)
        if hwp is None:
            return None

        _configure_hwp_session(hwp)

        if not _open_hwp_document(hwp, abs_hwp):
            return None

        if not _save_as_hwpx(hwp, abs_hwpx, target_path):
            logger.warning("COM SaveAs to HWPX failed: %s", abs_hwpx)
            return None

        logger.info("HWP -> HWPX COM conversion success: %s", abs_hwpx)
        return str(target_path)
    except Exception:
        logger.exception("Unexpected HWP COM conversion failure")
        return None
    finally:
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception:
                logger.debug("Failed to quit HWP COM object", exc_info=True)
        try:
            pythoncom.CoUninitialize()
        except Exception:
            logger.debug("CoUninitialize failed", exc_info=True)


def _resolve_output_dir(output_dir: str | None) -> Path | None:
    if output_dir:
        target_dir = Path(output_dir)
    else:
        target_dir = Path(tempfile.mkdtemp(prefix="hwp_import_"))

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir
    except Exception:
        logger.exception("Failed to create output dir for HWP conversion: %s", target_dir)
        return None


def _load_com_modules():
    try:
        import pythoncom
        import win32com.client

        return pythoncom, win32com.client
    except Exception:
        logger.exception("pywin32 unavailable for HWP COM conversion")
        return None


def _create_hwp_com_object(win32_client) -> object | None:
    methods = [
        ("DispatchEx", win32_client.DispatchEx),
        ("Dispatch", win32_client.Dispatch),
    ]
    errors: list[str] = []

    for prog_id in _COM_PROG_IDS:
        for method_name, dispatch in methods:
            try:
                hwp = dispatch(prog_id)
                logger.info("HWP COM connected via %s('%s')", method_name, prog_id)
                return hwp
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{method_name}('{prog_id}'): {exc}")

    logger.warning(
        "HWP COM object creation failed. Tried %s. Errors: %s",
        _COM_PROG_IDS,
        "; ".join(errors),
    )
    return None


def _configure_hwp_session(hwp: object) -> None:
    try:
        hwp.XHwpWindows.Item(0).Visible = False
    except Exception:
        logger.debug("Unable to hide HWP window", exc_info=True)

    try:
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    except Exception:
        logger.debug("RegisterModule failed", exc_info=True)


def _open_hwp_document(hwp: object, abs_hwp: str) -> bool:
    open_errors: list[str] = []
    for open_args in [(), ("HWP", "")]:
        try:
            if open_args:
                opened = bool(hwp.Open(abs_hwp, *open_args))
            else:
                opened = bool(hwp.Open(abs_hwp))
            if opened:
                return True
        except Exception as exc:  # noqa: BLE001
            open_errors.append(str(exc))

    logger.warning("Failed to open HWP in COM: %s", "; ".join(open_errors))
    return False


def _save_as_hwpx(hwp: object, abs_hwpx: str, target_path: Path) -> bool:
    saved = bool(hwp.SaveAs(abs_hwpx, "HWPX", ""))
    return bool(saved and target_path.exists())
