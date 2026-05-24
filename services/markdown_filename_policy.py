import re


_INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, default_name: str = "untitled") -> str:
    """Create a safe filename for Windows.

    - Removes invalid filesystem characters
    - Handles empty, whitespace-only, or dot-only names
    - Preserves Korean characters
    - Trims leading/trailing spaces and dots
    - Limits length to 120 characters
    """
    if not name:
        cleaned = default_name
    else:
        cleaned = name.strip()

    cleaned = _INVALID_FS_CHARS.sub("_", cleaned)

    cleaned = cleaned.strip(" .")

    if not cleaned:
        cleaned = default_name

    if len(cleaned) > 120:
        cleaned = cleaned[:120]

    return cleaned


def dedupe_filename(filename: str, existing_names: set[str]) -> str:
    """Generate a unique filename by adding suffix if name exists.

    Args:
        filename: Base filename (with or without extension)
        existing_names: Set of existing filenames (lowercase for comparison)

    Returns:
        Unique filename that doesn't conflict with existing_names
    """
    base = filename.lower()
    if base not in existing_names:
        return filename

    if "." in filename:
        parts = filename.rsplit(".", 1)
        base_name = parts[0]
        ext = "." + parts[1]
    else:
        base_name = filename
        ext = ""

    n = 2
    candidate = f"{base_name}_{n}{ext}"
    while candidate.lower() in existing_names:
        n += 1
        candidate = f"{base_name}_{n}{ext}"

    return candidate
