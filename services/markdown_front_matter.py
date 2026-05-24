import re
import uuid
from typing import Any

from services.markdown_document_model import MarkdownDocument, MarkdownMetadata


def split_front_matter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """Split markdown text into front matter and body.

    Returns:
        (metadata_dict, body_markdown, warnings)
    """
    warnings: list[str] = []

    if not text:
        return {}, text, warnings

    lines = text.split("\n")
    if not lines:
        return {}, text, warnings

    first_line = lines[0].strip()

    if first_line == "---":
        end_index = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_index = i
                break

        if end_index > 0:
            return _parse_yaml_front_matter(lines[1:end_index], "\n".join(lines[end_index + 1:]), warnings)
        else:
            warnings.append("YAML front matter not closed, treating as regular markdown")

    if first_line == "+++":
        end_index = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "+++":
                end_index = i
                break

        if end_index > 0:
            return _parse_toml_front_matter(lines[1:end_index], "\n".join(lines[end_index + 1:]), warnings)
        else:
            warnings.append("TOML front matter not closed, treating as regular markdown")

    return {}, text, warnings


def _parse_yaml_front_matter(front_lines: list[str], body: str, warnings: list[str]) -> tuple[dict[str, Any], str, list[str]]:
    """Parse simple YAML front matter without external dependencies."""
    metadata: dict[str, Any] = {}
    known_keys = {"title", "tags", "folder", "created_at", "updated_at"}
    pending_tags: list[str] = []
    current_list_key: str | None = None

    for line in front_lines:
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("- ") or re.match(r"^\s+-\s+", line):
            match = re.search(r"-\s+(.+)", line)
            if match:
                tag_value = match.group(1).strip().strip('"').strip("'")
                if tag_value:
                    pending_tags.append(tag_value)
                if current_list_key is None:
                    current_list_key = "tags"
            continue

        colon_idx = line.find(":")
        if colon_idx == -1:
            continue

        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()

        if not key:
            continue

        if pending_tags and key != current_list_key:
            metadata[current_list_key] = pending_tags
            pending_tags = []
            current_list_key = None

        if key in known_keys:
            if key == "tags":
                if current_list_key == "tags":
                    metadata[key] = pending_tags
                    pending_tags = []
                    current_list_key = None
                elif value:
                    metadata[key] = _parse_tags_value(value)
                else:
                    current_list_key = "tags"
            else:
                metadata[key] = value
        else:
            if "extra" not in metadata:
                metadata["extra"] = {}
            metadata["extra"][key] = value

    if pending_tags:
        metadata[current_list_key] = pending_tags

    return metadata, body, warnings


def _parse_toml_front_matter(front_lines: list[str], body: str, warnings: list[str]) -> tuple[dict[str, Any], str, list[str]]:
    """Parse simple TOML front matter (basic support)."""
    metadata: dict[str, Any] = {}
    known_keys = {"title", "tags", "folder", "created_at", "updated_at"}

    for line in front_lines:
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"')

            if key in known_keys:
                if key == "tags":
                    metadata[key] = _parse_tags_value(value)
                else:
                    metadata[key] = value
            else:
                if "extra" not in metadata:
                    metadata["extra"] = {}
                metadata["extra"][key] = value

    return metadata, body, warnings


def _parse_tags_value(value: str) -> list[str]:
    """Parse tags value from various formats."""
    value = value.strip()

    if not value:
        return []

    if value.startswith("["):
        content = value[1:-1]
        if not content:
            return []
        parts = [p.strip().strip('"').strip("'") for p in content.split(",")]
        return [p for p in parts if p]

    if value.startswith("("):
        content = value[1:-1]
        if not content:
            return []
        parts = [p.strip().strip('"').strip("'") for p in content.split(",")]
        return [p for p in parts if p]

    if "," in value:
        parts = [p.strip().strip('"').strip("'") for p in value.split(",")]
        return [p for p in parts if p]

    return [value]


def serialize_front_matter(metadata: MarkdownMetadata) -> str:
    """Serialize MarkdownMetadata to YAML front matter string."""
    lines: list[str] = ["---"]

    if metadata.title:
        lines.append(f"title: {metadata.title}")

    if metadata.tags:
        tags_str = ", ".join(metadata.tags)
        lines.append(f"tags: [{tags_str}]")

    if metadata.folder:
        lines.append(f"folder: {metadata.folder}")

    if metadata.created_at:
        lines.append(f"created_at: {metadata.created_at}")

    if metadata.updated_at:
        lines.append(f"updated_at: {metadata.updated_at}")

    for key, value in metadata.extra.items():
        if isinstance(value, str):
            lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            tags_str = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{tags_str}]")

    lines.append("---")

    return "\n".join(lines)


def parse_markdown_document(text: str, source_path: str | None = None) -> MarkdownDocument:
    """Parse markdown text into MarkdownDocument.

    On parse failure, preserves original text in body_markdown.
    """
    warnings: list[str] = []

    try:
        metadata_dict, body, parse_warnings = split_front_matter(text)
        warnings.extend(parse_warnings)
    except Exception as e:
        warnings.append(f"Front matter parse error: {e}")
        return MarkdownDocument(
            body_markdown=text,
            source_path=source_path,
            warnings=warnings
        )

    metadata = MarkdownMetadata()

    if "title" in metadata_dict:
        metadata.title = metadata_dict["title"]

    if "tags" in metadata_dict:
        tags = metadata_dict["tags"]
        metadata.tags = tags if isinstance(tags, list) else []

    if "folder" in metadata_dict:
        metadata.folder = metadata_dict["folder"]

    if "created_at" in metadata_dict:
        metadata.created_at = metadata_dict["created_at"]

    if "updated_at" in metadata_dict:
        metadata.updated_at = metadata_dict["updated_at"]

    if "extra" in metadata_dict:
        metadata.extra = metadata_dict["extra"]

    return MarkdownDocument(
        metadata=metadata,
        body_markdown=body,
        source_path=source_path,
        warnings=warnings
    )
