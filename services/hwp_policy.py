"""Centralized policy strings for handling legacy HWP files.

The AI Markdown Editor no longer processes .hwp files directly. All user-facing
messages and developer logs regarding this policy should reference the
constants defined here so that the guidance stays consistent across modules.
"""
from __future__ import annotations

HWP_CURRENT_NOTE_MESSAGE = (
    "HWP 파일은 AI마크다운에디터에서 직접 지원하지 않습니다.\n"
    "HWPX로 변환한 뒤 다시 불러와 주세요.\n\n"
    "별도 제공되는 HWPX 변환 프로그램을 사용하면 HWP 파일을 HWPX로 변환할 수 있습니다."
)

HWP_RAG_FILE_MESSAGE = (
    "HWP 파일은 참고문서AI에서 직접 색인할 수 없습니다. "
    "HWPX로 변환한 뒤 참고문서로 등록해 주세요."
)

_HWP_FOLDER_SKIP_TEMPLATE = (
    "HWP 파일 {count}개는 지원 대상이 아니어서 제외했습니다. "
    "HWPX로 변환한 뒤 다시 등록해 주세요."
)


def format_hwp_folder_skip_message(count: int) -> str:
    """Return the user-facing warning for skipped HWP files in folder runs."""
    return _HWP_FOLDER_SKIP_TEMPLATE.format(count=count)


__all__ = [
    "HWP_CURRENT_NOTE_MESSAGE",
    "HWP_RAG_FILE_MESSAGE",
    "format_hwp_folder_skip_message",
]
