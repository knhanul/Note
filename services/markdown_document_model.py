from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarkdownMetadata:
    title: str | None = None
    tags: list[str] = field(default_factory=list)
    folder: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MarkdownAsset:
    asset_id: str
    original_ref: str
    resolved_path: str | None = None
    db_image_id: str | None = None
    mime_type: str | None = None
    status: str = "ok"


@dataclass
class MarkdownDocument:
    metadata: MarkdownMetadata = field(default_factory=MarkdownMetadata)
    body_markdown: str = ""
    assets: list[MarkdownAsset] = field(default_factory=list)
    source_path: str | None = None
    warnings: list[str] = field(default_factory=list)
