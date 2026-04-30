"""Utility functions for HWP/HWPX processing."""
from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Optional
import zipfile


def sanitize_hwp_text(text: str) -> str:
    """Sanitize HWP text by removing control characters.
    
    HWP files may contain control characters in the 0x01-0x1F range
    that should be removed or converted for Markdown output.
    """
    if not text:
        return ""

    # Remove common HWP control characters
    control_chars = {
        '\x0c': '',  # Form feed
        '\x1e': '',  # Record separator
        '\x1f': '',  # Unit separator
        '\x0b': '\n',  # Vertical tab -> newline
        '\x0a': '\n',  # Line feed
        '\x0d': '',  # Carriage return
    }

    for char, replacement in control_chars.items():
        text = text.replace(char, replacement)

    # Remove other non-printable characters except common whitespace
    text = re.sub(r'[\x00-\x08\x0e-\x1f\x7f-\x9f]', '', text)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_image_from_hwpx(zip_file: zipfile.ZipFile, image_path: str) -> Optional[str]:
    """Extract image from HWPX ZIP archive and convert to base64 data URL.
    
    Args:
        zip_file: Opened HWPX ZIP file object
        image_path: Path to image within the ZIP archive
        
    Returns:
        Base64 data URL string or None if extraction fails
    """
    try:
        img_data = zip_file.read(image_path)
        b64_data = base64.b64encode(img_data).decode("ascii")

        # Determine MIME type from file extension
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime_type = _ext_to_mime(ext)

        return f"data:image/{mime_type};base64,{b64_data}"
    except Exception as exc:
        print(f"[hwp_utils] Failed to extract image {image_path}: {exc}")
        return None


def _ext_to_mime(ext: str) -> str:
    """Convert file extension to MIME type."""
    mime_map = {
        "png": "png",
        "jpg": "jpeg",
        "jpeg": "jpeg",
        "gif": "gif",
        "webp": "webp",
        "bmp": "bmp",
        "svg": "svg+xml",
    }
    return mime_map.get(ext.lower(), "png")


def is_hwpx_file(path: Path) -> bool:
    """Check if file is a valid HWPX file.
    
    HWPX files are ZIP archives with specific structure.
    """
    if path.suffix.lower() != ".hwpx":
        return False

    try:
        with zipfile.ZipFile(path, "r") as zf:
            # Check for required HWPX structure
            namelist = zf.namelist()
            return any("Contents/section.xml" in name for name in namelist)
    except Exception:
        return False


def fallback_to_gethwp(fpath: Path) -> str:
    """Fallback to gethwp library for HWP/HWPX text extraction.
    
    This is used when XML parsing fails or is not available.
    """
    try:
        import gethwp
    except Exception as exc:
        print(f"[hwp_utils] gethwp library not available: {exc}")
        return ""

    try:
        ext = fpath.suffix.lower()
        if ext == ".hwp":
            text = gethwp.read_hwp(str(fpath))
        elif ext == ".hwpx":
            text = gethwp.read_hwpx(str(fpath))
        else:
            return ""

        if not text:
            return ""

        # Sanitize text
        text = sanitize_hwp_text(text)
        
        # Convert to simple markdown (preserve paragraphs)
        lines = text.split('\n')
        blocks = [line.strip() for line in lines if line.strip()]
        return "\n\n".join(blocks)
    except Exception as exc:
        print(f"[hwp_utils] gethwp extraction failed: {exc}")
        return ""
