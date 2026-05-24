"""Conversion environment diagnostics for Note2.

This module provides diagnostic capabilities to check if required dependencies
(e.g., HWP COM automation) are available on the current system.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

_HWP_PROG_IDS = ["HWPFrame.HwpObject", "Hwp.HwpObject"]


@dataclass
class ConversionDiagnosticResult:
    """Result of a conversion environment diagnostic check."""

    ok: bool
    feature: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def check_pywin32_available() -> ConversionDiagnosticResult:
    """Check if pywin32 (pythoncom, win32com.client) is available.

    Returns:
        ConversionDiagnosticResult with availability status.
    """
    result = ConversionDiagnosticResult(
        ok=False,
        feature="pywin32",
        message="pywin32 not available",
        details={},
        warnings=[],
    )

    try:
        import pythoncom
        result.details["pythoncom"] = "available"
    except ImportError as exc:
        result.details["pythoncom"] = f"import failed: {exc}"
        result.message = f"pythoncom import failed: {exc}"
        return result

    try:
        import win32com.client
        result.details["win32com.client"] = "available"
    except ImportError as exc:
        result.details["win32com.client"] = f"import failed: {exc}"
        result.message = f"win32com.client import failed: {exc}"
        return result

    result.ok = True
    result.message = "pywin32 is available"
    return result


def check_hwp_com_available() -> ConversionDiagnosticResult:
    """Check if HWP COM automation is available.

    This attempts to create an HWP COM object to verify if Hancom
    is installed and COM automation is functional.

    Returns:
        ConversionDiagnosticResult with HWP COM availability status.
    """
    result = ConversionDiagnosticResult(
        ok=False,
        feature="hwp_com",
        message="HWP COM not available",
        details={"prog_ids_tested": [], "errors": []},
        warnings=[],
    )

    pywin32_result = check_pywin32_available()
    if not pywin32_result.ok:
        result.message = f"HWP COM requires pywin32: {pywin32_result.message}"
        result.details["pywin32_check"] = pywin32_result.message
        return result

    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    hwp = None

    try:
        for prog_id in _HWP_PROG_IDS:
            result.details["prog_ids_tested"].append(prog_id)
            for method_name, dispatch in [
                ("DispatchEx", win32com.client.DispatchEx),
                ("Dispatch", win32com.client.Dispatch),
            ]:
                try:
                    hwp = dispatch(prog_id)
                    result.details["connected_via"] = f"{method_name}('{prog_id}')"
                    result.ok = True
                    result.message = "HWP COM is available"
                    return
                except Exception as exc:
                    result.details["errors"].append(f"{method_name}('{prog_id}'): {exc}")

        result.message = "Could not connect to HWP COM. Hancom may not be installed."
    except Exception as exc:
        result.details["errors"].append(f"Unexpected error: {exc}")
        result.message = f"HWP COM check failed: {exc}"
    finally:
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

    return result


def check_hwp_import_environment() -> ConversionDiagnosticResult:
    """Check the overall HWP import environment.

    This performs a comprehensive check including pywin32 and HWP COM.

    Returns:
        ConversionDiagnosticResult with overall environment status.
    """
    result = ConversionDiagnosticResult(
        ok=False,
        feature="hwp_import",
        message="HWP import environment not ready",
        details={},
        warnings=[],
    )

    pywin32 = check_pywin32_available()
    result.details["pywin32"] = {
        "ok": pywin32.ok,
        "message": pywin32.message,
    }

    if pywin32.ok:
        hwp_com = check_hwp_com_available()
        result.details["hwp_com"] = {
            "ok": hwp_com.ok,
            "message": hwp_com.message,
        }
        if hwp_com.ok:
            result.ok = True
            result.message = "HWP import environment is ready"
        else:
            result.warnings.append("HWP COM not available - HWP import will use fallback")
            result.message = "HWP import environment is partially ready (fallback mode)"
    else:
        result.warnings.append("pywin32 not available - HWP import will use fallback")
        result.message = "HWP import environment uses fallback mode"

    return result


__all__ = [
    "ConversionDiagnosticResult",
    "check_pywin32_available",
    "check_hwp_com_available",
    "check_hwp_import_environment",
]
