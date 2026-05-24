from pathlib import Path
from typing import Optional

from services.ai_index_database import AiIndexDatabase
from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_document_index_service import AiDocumentIndexService
from services.ai_search_service import AiSearchService
from services.ai_context_builder import AiContextBuilder
from services.ai_rag_prompt_builder import AiRagPromptBuilder
from services.ai_rag_service import AiRagService, RagQueryOptions
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ollama_llm_client import OllamaLlmClient
from services.document_chunk_model import IndexedDocument
from services.ai_search_service import SearchResultChunk
from services.ai_rag_service import RagAnswer, RagCitation


class FakeLlmClient(LlmClient):
    def __init__(self, response_text: str = "Fake response", warnings: list[str] = None):
        self.response_text = response_text
        self.warnings = warnings or []
        self.last_options: Optional[LlmGenerateOptions] = None

    def generate(
        self, system_prompt: str, user_prompt: str, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        self.last_options = options
        return LlmGenerateResult(
            text=self.response_text,
            model=options.model if options else "llama3.2:3b",
            provider="fake",
            raw={"response": self.response_text},
            warnings=self.warnings,
        )

    def generate_from_payload(
        self, payload, options: LlmGenerateOptions | None = None
    ) -> LlmGenerateResult:
        return self.generate(payload.system_prompt, payload.user_prompt, options)


class AiRagApplicationService:
    def __init__(
        self,
        db_path: str | Path | None = None,
        llm_client: LlmClient | None = None,
        default_model: str = "llama3.2:3b",
    ):
        self._db_path = db_path
        self._default_model = default_model
        self._llm_client = llm_client
        self._db: Optional[AiIndexDatabase] = None
        self._repo: Optional[AiDocumentIndexRepository] = None
        self._index_service: Optional[AiDocumentIndexService] = None
        self._search_service: Optional[AiSearchService] = None
        self._context_builder: Optional[AiContextBuilder] = None
        self._prompt_builder: Optional[AiRagPromptBuilder] = None
        self._rag_service: Optional[AiRagService] = None
        self._last_answer: Optional[RagAnswer] = None
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return

        self._db = AiIndexDatabase(self._db_path)
        self._db.initialize()
        self._repo = AiDocumentIndexRepository(self._db)
        self._index_service = AiDocumentIndexService(self._repo)
        self._search_service = AiSearchService(self._repo)
        self._context_builder = AiContextBuilder(self._repo)
        self._prompt_builder = AiRagPromptBuilder()

        llm = self._llm_client
        if llm is None:
            llm = OllamaLlmClient(default_model=self._default_model)

        self._rag_service = AiRagService(
            search_service=self._search_service,
            context_builder=self._context_builder,
            prompt_builder=self._prompt_builder,
            llm_client=llm,
        )

        self._initialized = True

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None
        self._repo = None
        self._index_service = None
        self._search_service = None
        self._context_builder = None
        self._prompt_builder = None
        self._rag_service = None
        self._initialized = False

    def clear_index(self) -> None:
        self._ensure_initialized()
        self._repo.clear_all()
        self._last_answer = None

    def index_current_note(
        self,
        note_id: str,
        title: str | None,
        content: str,
        tags: list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> IndexedDocument:
        self._ensure_initialized()
        return self._index_service.index_note_content(
            note_id=note_id,
            title=title,
            content=content,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
        )

    def index_markdown_file(self, path: str | Path) -> IndexedDocument:
        self._ensure_initialized()
        return self._index_service.index_markdown_file(path)

    def index_hwpx_file(self, path: str | Path) -> IndexedDocument:
        self._ensure_initialized()
        return self._index_service.index_hwpx_file(path)

    def index_hwp_file(self, path: str | Path) -> IndexedDocument:
        self._ensure_initialized()
        return self._index_service.index_hwp_file(path)

    def index_external_files(
        self,
        file_paths: list[str | Path],
    ) -> dict:
        self._ensure_initialized()

        indexed_count = 0
        failed_count = 0
        warnings: list[str] = []
        document_ids: list[str] = []

        for path in file_paths:
            try:
                path_obj = Path(path)
                ext = path_obj.suffix.lower()

                if ext in (".md", ".markdown"):
                    doc = self._index_service.index_markdown_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext == ".hwpx":
                    doc = self._index_service.index_hwpx_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext == ".hwp":
                    doc = self._index_service.index_hwp_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                else:
                    warnings.append(f"지원하지 않는 파일 형식: {path}")
                    failed_count += 1
            except Exception as e:
                warnings.append(f"파일 색인 실패: {path} - {e}")
                failed_count += 1

        return {
            "indexed_count": indexed_count,
            "failed_count": failed_count,
            "warnings": warnings,
            "document_ids": document_ids,
        }

    def search_index(self, query: str, limit: int = 20, offset: int = 0) -> list[SearchResultChunk]:
        self._ensure_initialized()
        return self._search_service.search_keyword(query, limit=limit, offset=offset)

    def ask_indexed_documents(
        self, question: str, options: RagQueryOptions | None = None
    ) -> RagAnswer:
        self._ensure_initialized()
        self._last_answer = self._rag_service.answer_question(question, options)
        return self._last_answer

    def ask_indexed_document(
        self, document_id: str, question: str, options: RagQueryOptions | None = None
    ) -> RagAnswer:
        self._ensure_initialized()
        self._last_answer = self._rag_service.answer_question_in_document(document_id, question, options)
        return self._last_answer

    def get_last_answer(self) -> RagAnswer | None:
        return self._last_answer

    def get_citations_for_last_answer(self) -> list[RagCitation]:
        if self._last_answer is None:
            return []
        return self._last_answer.citations

    def index_note_items(
        self,
        note_items: list[dict],
        scope_label: str = "manual",
    ) -> dict:
        self._ensure_initialized()

        indexed_count = 0
        failed_count = 0
        warnings: list[str] = []
        document_ids: list[str] = []

        for item in note_items:
            try:
                note_id = item.get("note_id") or item.get("id")
                if not note_id:
                    warnings.append(f"Missing note_id, skipping")
                    failed_count += 1
                    continue

                title = item.get("title")
                content = item.get("content", "")
                tags = item.get("tags")
                created_at = item.get("created_at")
                updated_at = item.get("updated_at")

                doc = self._index_service.index_note_content(
                    note_id=note_id,
                    title=title,
                    content=content,
                    tags=tags,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                indexed_count += 1
                document_ids.append(doc.document_id)
            except Exception as e:
                note_id = item.get("note_id") or item.get("id", "unknown")
                warnings.append(f"Failed to index {note_id}: {e}")
                failed_count += 1

        return {
            "indexed_count": indexed_count,
            "failed_count": failed_count,
            "warnings": warnings,
            "document_ids": document_ids,
        }

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()
