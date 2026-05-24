import re
import uuid
from pathlib import Path
from typing import Any

from services.markdown_document_model import MarkdownAsset


_MD_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_DATA_URL_PATTERN = re.compile(r"^data:image/([a-zA-Z0-9.+-]+);base64,", re.IGNORECASE)
_NOTE_IMAGE_PATTERN = re.compile(r"^note-image://")
_HTTP_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


def extract_markdown_assets(body_markdown: str, base_path: str | None = None) -> tuple[list[MarkdownAsset], list[str]]:
    """Extract image assets from markdown body.

    Detects:
    - Relative path images
    - Absolute path images
    - note-image:// tokens
    - data:image/... base64
    - http/https external images

    For missing relative path files, sets status="missing" and adds warning.
    Does NOT rewrite body paths or perform file copy/DB storage.

    Returns:
        (list of MarkdownAsset, list of warnings)
    """
    assets: list[MarkdownAsset] = []
    warnings: list[str] = []

    if not body_markdown:
        return assets, warnings

    seen_refs: set[str] = set()

    for match in _MD_IMG_PATTERN.finditer(body_markdown):
        alt_text = match.group(1)
        src = match.group(2).strip()

        if not src or src in seen_refs:
            continue
        seen_refs.add(src)

        asset = _create_asset(src, alt_text, base_path)
        if asset.status == "missing":
            warnings.append(f"Image not found: {src}")

        assets.append(asset)

    return assets, warnings


def _create_asset(original_ref: str, alt_text: str, base_path: str | None) -> MarkdownAsset:
    """Create a MarkdownAsset based on the reference type."""
    asset_id = str(uuid.uuid4())[:16]

    if _NOTE_IMAGE_PATTERN.match(original_ref):
        return MarkdownAsset(
            asset_id=asset_id,
            original_ref=original_ref,
            resolved_path=None,
            db_image_id=original_ref.replace("note-image://", ""),
            mime_type=None,
            status="embedded"
        )

    data_match = _DATA_URL_PATTERN.match(original_ref)
    if data_match:
        mime_type = data_match.group(1)
        return MarkdownAsset(
            asset_id=asset_id,
            original_ref=original_ref,
            resolved_path=None,
            db_image_id=None,
            mime_type=mime_type,
            status="embedded"
        )

    if _HTTP_URL_PATTERN.match(original_ref):
        return MarkdownAsset(
            asset_id=asset_id,
            original_ref=original_ref,
            resolved_path=original_ref,
            db_image_id=None,
            mime_type=None,
            status="external"
        )

    if Path(original_ref).is_absolute():
        resolved = Path(original_ref)
        if resolved.exists() and resolved.is_file():
            return MarkdownAsset(
                asset_id=asset_id,
                original_ref=original_ref,
                resolved_path=str(resolved),
                db_image_id=None,
                mime_type=_guess_mime_type(resolved),
                status="ok"
            )
        else:
            return MarkdownAsset(
                asset_id=asset_id,
                original_ref=original_ref,
                resolved_path=str(resolved),
                db_image_id=None,
                mime_type=None,
                status="missing"
            )

    if base_path:
        base = Path(base_path)
        resolved = (base.parent / original_ref).resolve()
        if resolved.exists() and resolved.is_file():
            return MarkdownAsset(
                asset_id=asset_id,
                original_ref=original_ref,
                resolved_path=str(resolved),
                db_image_id=None,
                mime_type=_guess_mime_type(resolved),
                status="ok"
            )
        else:
            return MarkdownAsset(
                asset_id=asset_id,
                original_ref=original_ref,
                resolved_path=str(resolved),
                db_image_id=None,
                mime_type=None,
                status="missing"
            )

    return MarkdownAsset(
        asset_id=asset_id,
        original_ref=original_ref,
        resolved_path=original_ref,
        db_image_id=None,
        mime_type=None,
        status="missing"
    )


def _guess_mime_type(path: Path) -> str | None:
    """Guess MIME type from file extension."""
    ext = path.suffix.lower().lstrip(".")
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
    }
    return mime_map.get(ext)
