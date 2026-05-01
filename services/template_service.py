"""Template service for managing note templates in the current library database."""
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from .database import Database


class TemplateService:
    """Handles template database operations."""

    VARIABLE_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

    DEFAULT_EXAMPLE_TITLE = "새 템플릿 - {{date}}"
    DEFAULT_EXAMPLE_CONTENT = (
        "# 새 템플릿 - {{date}}\n"
        "\n"
        "이 템플릿은 예시입니다. 불필요한 부분을 삭제하고 원하는 내용을 작성하세요.\n"
        "\n"
        "## 사용 가능한 변수\n"
        "\n"
        "템플릿에는 아래 변수를 넣을 수 있습니다. 새 노트를 만들 때 실제 값으로 치환됩니다.\n"
        "\n"
        "| 변수 | 설명 | 예시 |\n"
        "| --- | --- | --- |\n"
        "| `{{date}}` | 오늘 날짜 | 2026-05-01 |\n"
        "| `{{time}}` | 현재 시간 | 14:30 |\n"
        "| `{{datetime}}` | 날짜와 시간 | 2026-05-01 14:30 |\n"
        "| `{{year}}` | 연도 | 2026 |\n"
        "| `{{month}}` | 월 | 05 |\n"
        "| `{{day}}` | 일 | 01 |\n"
        "| `{{folder_name}}` | 현재 폴더 이름 | 문서 |\n"
        "| `{{folder_id}}` | 현재 폴더 ID | abc123 |\n"
        "| `{{title}}` | 템플릿 제목 | 새 템플릿 - 2026-05-01 |\n"
        "| `{{now:%Y-%m-%d}}` | 포맷형 날짜 | 2026.05.01 |\n"
        "\n"
        "### 변수 사용 예시\n"
        "\n"
        "- 첫 줄(제목): `# {{folder_name}} 회의록 - {{date}}`\n"
        "- 본문: `생성 시각: {{datetime}}`\n"
        "\n"
        "## 마크다운 포맷 예시\n"
        "\n"
        "### 제목 (Heading)\n"
        "```markdown\n"
        "# 큰 제목\n"
        "## 중간 제목\n"
        "### 작은 제목\n"
        "```\n"
        "\n"
        "### 목록 (List)\n"
        "\n"
        "- 첫 번째 항목\n"
        "- 두 번째 항목\n"
        "  - 들여쓰기 항목\n"
        "\n"
        "1. 순서 있는 항목\n"
        "2. 두 번째 순서\n"
        "\n"
        "### 인용 (Blockquote)\n"
        "\n"
        "> 중요한 내용을 인용합니다.\n"
        ">\n"
        "> 여러 줄도 가능합니다.\n"
        "\n"
        "### 코드 블록 (Code Block)\n"
        "\n"
        "```python\n"
        "# 여기에 코드를 작성하세요\n"
        "print('Hello, Note2!')\n"
        "```\n"
        "\n"
        "### 체크리스트 (Checklist)\n"
        "\n"
        "- [ ] 할 일 1\n"
        "- [x] 완료된 일\n"
        "- [ ] 할 일 2\n"
        "\n"
        "### 표 (Table)\n"
        "\n"
        "| 항목 | 내용 | 상태 |\n"
        "| --- | --- | --- |\n"
        "| 설계 | 아키텍처 검토 | 완료 |\n"
        "| 개발 | 기능 구현 | 진행중 |\n"
        "| 테스트 | 단위 테스트 | 예정 |\n"
        "\n"
        "---\n"
        "\n"
        "아래부터 원하는 내용을 작성하세요.\n"
    )

    def __init__(self, database: Database):
        self.db = database

    @classmethod
    def render_text(
        cls,
        text: str,
        folder_id: str = "",
        folder_name: str = "",
        note_title: str = "",
        now: Optional[datetime] = None,
    ) -> str:
        """Render supported template variables inside text."""
        if not text:
            return ""

        current = now or datetime.now()
        base_values = {
            "date": current.strftime("%Y-%m-%d"),
            "time": current.strftime("%H:%M"),
            "datetime": current.strftime("%Y-%m-%d %H:%M"),
            "year": current.strftime("%Y"),
            "month": current.strftime("%m"),
            "day": current.strftime("%d"),
            "hour": current.strftime("%H"),
            "minute": current.strftime("%M"),
            "folder_name": folder_name or "",
            "folder": folder_name or "",
            "folder_id": folder_id or "",
            "title": note_title or "",
        }

        def replace(match: re.Match) -> str:
            token = match.group(1).strip()
            normalized = token.lower()

            if normalized in base_values:
                return base_values[normalized]

            if ":" in token:
                key, fmt = token.split(":", 1)
                key = key.strip().lower()
                fmt = fmt.strip()
                if key in {"now", "date", "time", "datetime"} and fmt:
                    try:
                        return current.strftime(fmt)
                    except ValueError:
                        return match.group(0)

            return match.group(0)

        return cls.VARIABLE_PATTERN.sub(replace, text)

    @classmethod
    def render_template_fields(
        cls,
        title: str,
        content: str,
        folder_id: str = "",
        folder_name: str = "",
        now: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """Render a template's title and content with the same context."""
        current = now or datetime.now()
        rendered_title = cls.render_text(title or "", folder_id, folder_name, "", current)
        rendered_content = cls.render_text(
            content or "", folder_id, folder_name, rendered_title, current
        )
        return {
            "title": rendered_title,
            "content": rendered_content,
        }

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all templates ordered for display."""
        return self.db.fetch_all(
            "SELECT * FROM templates ORDER BY sort_order, created_at"
        )

    def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        return self.db.fetch_one(
            "SELECT * FROM templates WHERE id = ?",
            (template_id,)
        )

    def create(
        self,
        template_id: str,
        name: str,
        title: str = "",
        content: str = "",
        description: str = "",
    ) -> bool:
        """Create a new template.

        If both title and content are empty, a default example template
        with markdown formatting guide and variable reference is used.
        """
        effective_title = title if title or content else self.DEFAULT_EXAMPLE_TITLE
        effective_content = content if title or content else self.DEFAULT_EXAMPLE_CONTENT
        try:
            now = Database.now_iso()
            cursor = self.db.execute(
                """INSERT INTO templates (id, name, title, content, description, sort_order, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?,
                           (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM templates),
                           ?, ?)""",
                (template_id, name, effective_title, effective_content, description, now, now)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

    def update(
        self,
        template_id: str,
        name: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Update template fields."""
        try:
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if content is not None:
                updates.append("content = ?")
                params.append(content)
            if description is not None:
                updates.append("description = ?")
                params.append(description)

            if not updates:
                return False

            updates.append("updated_at = ?")
            params.append(Database.now_iso())
            params.append(template_id)

            query = f"UPDATE templates SET {', '.join(updates)} WHERE id = ?"
            cursor = self.db.execute(query, tuple(params))
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

    def delete(self, template_id: str) -> bool:
        """Delete a template and clear folder defaults that reference it."""
        try:
            self.db.execute(
                "UPDATE folders SET default_template_id = NULL WHERE default_template_id = ?",
                (template_id,)
            )
            cursor = self.db.execute(
                "DELETE FROM templates WHERE id = ?",
                (template_id,)
            )
            self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
