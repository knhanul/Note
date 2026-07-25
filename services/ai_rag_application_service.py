import logging
from pathlib import Path
from typing import Optional, Callable

from services.ai_index_database import AiIndexDatabase
from services.ai_document_index_repository import AiDocumentIndexRepository
from services.ai_document_index_service import AiDocumentIndexService
from services.ai_search_service import AiSearchService
from services.ai_context_builder import AiContextBuilder
from services.ai_rag_prompt_builder import AiRagPromptBuilder
from services.ai_rag_service import AiRagService, RagQueryOptions
from services.ai_llm_client import LlmClient, LlmGenerateOptions, LlmGenerateResult
from services.ollama_llm_client import OllamaLlmClient
from services.ollama_health import OllamaHealthResult
from services.document_chunk_model import IndexedDocument, IndexedDocumentSummary
from services.ai_search_service import SearchResultChunk
from services.ai_rag_service import RagAnswer, RagCitation
from services.hwp_policy import HWP_RAG_FILE_MESSAGE, format_hwp_folder_skip_message
from services.rag_answer_prompt_loader import RagAnswerPromptLoader
from services.ollama_embedding_service import OllamaEmbeddingService
from services.chroma_vector_store import ChromaVectorStore
from packages.ollama_plugin.ai_settings import AISettingsManager


logger = logging.getLogger(__name__)


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


ProgressCallback = Callable[[str, str, int, int], None]


class AiRagApplicationService:
    def __init__(
        self,
        db_path: str | Path | None = None,
        llm_client: LlmClient | None = None,
        default_model: str = "llama3.2:3b",
        app_data_dir: Path | None = None,
    ):
        self._db_path = db_path
        self._default_model = default_model
        self._llm_client = llm_client
        self._app_data_dir = app_data_dir
        self._settings_manager: Optional[AISettingsManager] = None
        self._db: Optional[AiIndexDatabase] = None
        self._repo: Optional[AiDocumentIndexRepository] = None
        self._index_service: Optional[AiDocumentIndexService] = None
        self._search_service: Optional[AiSearchService] = None
        self._context_builder: Optional[AiContextBuilder] = None
        self._prompt_builder: Optional[AiRagPromptBuilder] = None
        self._rag_service: Optional[AiRagService] = None
        self._rag_prompt_loader: Optional[RagAnswerPromptLoader] = None
        self._embedding_service: Optional[OllamaEmbeddingService] = None
        self._vector_store: Optional[ChromaVectorStore] = None
        self._last_answer: Optional[RagAnswer] = None
        self._initialized = False
        self._cancel_requested = False

    def initialize(self) -> None:
        if self._initialized:
            return

        self._db = AiIndexDatabase(self._db_path)
        self._db.initialize()
        self._repo = AiDocumentIndexRepository(self._db)
        self._context_builder = AiContextBuilder(self._repo)
        self._prompt_builder = AiRagPromptBuilder()
        self._rag_prompt_loader = RagAnswerPromptLoader()
        self._rag_prompt_loader.load()

        embedding_model = "kure"
        embedding_base_url = "http://localhost:11434"

        # Initialize settings manager to get model from AI settings
        if self._app_data_dir:
            self._settings_manager = AISettingsManager(self._app_data_dir)
            settings_model = self._settings_manager.settings.chat_model
            if settings_model:
                self._default_model = settings_model
            if self._settings_manager.settings.embedding_model:
                embedding_model = self._settings_manager.settings.embedding_model
            if self._settings_manager.settings.base_url:
                embedding_base_url = self._settings_manager.settings.base_url

        vector_dir = self._resolve_vector_store_dir()
        self._embedding_service = OllamaEmbeddingService(
            base_url=embedding_base_url,
            model=embedding_model,
            timeout_sec=30.0,
        )
        self._vector_store = ChromaVectorStore(
            persist_dir=vector_dir,
            collection_name="ai_document_chunks",
        )

        self._index_service = AiDocumentIndexService(
            self._repo,
            embedding_service=self._embedding_service,
            vector_store=self._vector_store,
        )
        self._search_service = AiSearchService(
            self._repo,
            embedding_service=self._embedding_service,
            vector_store=self._vector_store,
        )

        llm = self._llm_client
        if llm is None:
            llm = OllamaLlmClient(default_model=self._default_model)

        self._rag_service = AiRagService(
            search_service=self._search_service,
            context_builder=self._context_builder,
            prompt_builder=self._prompt_builder,
            llm_client=llm,
            default_model=self._default_model,
            rag_prompt_loader=self._rag_prompt_loader,
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
        self._embedding_service = None
        self._vector_store = None
        self._initialized = False
        self._cancel_requested = False

    def cancel_indexing(self) -> None:
        """Request cancellation of ongoing indexing operations."""
        self._cancel_requested = True

    def clear_index(self) -> None:
        self._ensure_initialized()
        self._repo.clear_all()
        if self._vector_store and self._vector_store.enabled:
            self._vector_store.clear_all()
        self._last_answer = None

    def remove_document(self, document_id: str) -> bool:
        self._ensure_initialized()
        try:
            if self._vector_store and self._vector_store.enabled:
                self._vector_store.delete_document_chunks(document_id)
            self._repo.delete_document(document_id)
            return True
        except Exception:
            return False

    def _resolve_vector_store_dir(self) -> Path:
        if self._app_data_dir:
            return (self._app_data_dir / "ai" / "chroma").resolve()

        if self._db_path and str(self._db_path) != ":memory:":
            return (Path(self._db_path).resolve().parent / "chroma").resolve()

        return (Path.cwd() / "app_data" / "ai" / "chroma").resolve()

    def _is_vector_store_active(self) -> bool:
        return (
            self._vector_store is not None
            and self._vector_store.enabled
            and self._embedding_service is not None
        )

    def index_current_note(
        self,
        note_id: str,
        title: str | None,
        content: str,
        tags: list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> IndexedDocument:
        self._ensure_initialized()
        result = self._index_service.index_note_content(
            note_id=note_id,
            title=title,
            content=content,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._notify_progress(progress_callback, "note", title or note_id or "", 1, 1)
        return result

    def index_markdown_file(self, path: str | Path) -> IndexedDocument:
        self._ensure_initialized()
        return self._index_service.index_markdown_file(path)

    def index_hwpx_file(self, path: str | Path) -> IndexedDocument:
        self._ensure_initialized()
        return self._index_service.index_hwpx_file(path)

    def index_hwp_file(self, path: str | Path) -> IndexedDocument:
        self._ensure_initialized()
        logger.warning(
            "[AiRagApplicationService] index_hwp_file called but HWP support is disabled: path=%s",
            path,
        )
        raise RuntimeError(HWP_RAG_FILE_MESSAGE)

    def _notify_progress(
        self,
        callback: ProgressCallback | None,
        kind: str,
        label: str,
        current: int,
        total: int,
    ) -> None:
        if not callback:
            return
        try:
            callback(kind, label, current, total)
        except Exception:
            pass

    def index_external_files(
        self,
        file_paths: list[str | Path],
        progress_callback: ProgressCallback | None = None,
    ) -> dict:
        self._ensure_initialized()
        self._cancel_requested = False

        indexed_count = 0
        failed_count = 0
        warnings: list[str] = []
        document_ids: list[str] = []
        total = len(file_paths)
        processed = 0

        skipped_hwp_paths: list[str] = []

        for path in file_paths:
            if self._cancel_requested:
                warnings.append("색인 작업이 중지되었습니다.")
                break

            processed += 1
            label = Path(path).name or str(path)
            self._notify_progress(progress_callback, "file", label, processed, total or processed)
            try:
                path_obj = Path(path)
                ext = path_obj.suffix.lower()

                if path_obj.name.startswith("~$"):
                    logger.info(
                        "[AiRagApplicationService] Skipped temporary Office file: %s",
                        path_obj.name,
                    )
                    continue

                if ext in (".md", ".markdown"):
                    doc = self._index_service.index_markdown_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext in (".txt",):
                    doc = self._index_service.index_text_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext in (".html", ".htm"):
                    doc = self._index_service.index_html_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext == ".docx":
                    doc = self._index_service.index_docx_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext == ".hwpx":
                    doc = self._index_service.index_hwpx_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext == ".pdf":
                    doc = self._index_service.index_pdf_file(path)
                    indexed_count += 1
                    document_ids.append(doc.document_id)
                elif ext == ".hwp":
                    skipped_hwp_paths.append(str(path_obj))
                    warnings.append(HWP_RAG_FILE_MESSAGE)
                    logger.info(
                        "[AiRagApplicationService] Skipped unsupported HWP file: path=%s",
                        path_obj,
                    )
                    failed_count += 1
                else:
                    warnings.append(f"지원하지 않는 파일 형식: {path}")
                    failed_count += 1
            except Exception as e:
                warnings.append(f"파일 색인 실패: {path} - {e}")
                failed_count += 1

        result = {
            "indexed_count": indexed_count,
            "failed_count": failed_count,
            "warnings": warnings,
            "document_ids": document_ids,
            "skipped_hwp_count": len(skipped_hwp_paths),
        }

        if indexed_count > 0 and not self._is_vector_store_active():
            result["warnings"].append(
                "벡터 DB가 비활성화되어 문서가 색인되었지만 벡터 검색에 사용할 수 없습니다. "
                "chromadb 패키지 설치 상태를 확인해 주세요."
            )
            logger.warning(
                "[AiRagApplicationService] Vector store is inactive - documents indexed without vector embeddings"
            )

        return result

    def list_indexed_documents(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[IndexedDocumentSummary], int]:
        self._ensure_initialized()
        return self._repo.list_document_summaries(limit=limit, offset=offset)

    def index_external_folder(
        self,
        folder_path: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> dict:
        self._ensure_initialized()

        folder = Path(folder_path)
        if not folder.is_dir():
            return {
                "indexed_count": 0,
                "failed_count": 0,
                "warnings": ["폴더가 아닙니다"],
                "document_ids": [],
            }

        supported_extensions = {".md", ".markdown", ".txt", ".html", ".htm", ".docx", ".hwpx", ".pdf"}
        candidate_paths: list[str] = []
        skipped_hwp: list[str] = []

        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("~$"):
                logger.info(
                    "[AiRagApplicationService] Skipped temporary Office file: %s",
                    path.name,
                )
                continue
            ext = path.suffix.lower()
            if ext == ".hwp":
                skipped_hwp.append(str(path))
                continue
            if ext in supported_extensions:
                candidate_paths.append(str(path))

        if not candidate_paths:
            warnings: list[str] = []
            if skipped_hwp:
                warning_text = format_hwp_folder_skip_message(len(skipped_hwp))
                warnings.append(warning_text)
                logger.info(
                    "[AiRagApplicationService] Skipped unsupported HWP files in folder: count=%d",
                    len(skipped_hwp),
                )
            return {
                "indexed_count": 0,
                "failed_count": 0,
                "warnings": warnings or ["지원하는 파일이 없습니다"],
                "document_ids": [],
                "skipped_hwp_count": len(skipped_hwp),
            }

        result = self.index_external_files(candidate_paths, progress_callback=progress_callback)
        logger.info(
            "[AiRagApplicationService] Folder indexing complete: folder=%s, candidates=%d, indexed=%d, failed=%d, warnings=%s",
            folder,
            len(candidate_paths),
            result.get("indexed_count", 0),
            result.get("failed_count", 0),
            result.get("warnings", []),
        )
        if skipped_hwp:
            warning_text = format_hwp_folder_skip_message(len(skipped_hwp))
            result.setdefault("warnings", []).append(warning_text)
            result["skipped_hwp_count"] = len(skipped_hwp)
            logger.info(
                "[AiRagApplicationService] Skipped unsupported HWP files in folder: count=%d",
                len(skipped_hwp),
            )
        return result

    def search_index(self, query: str, limit: int = 20, offset: int = 0) -> list[SearchResultChunk]:
        self._ensure_initialized()
        return self._search_service.search_keyword(query, limit=limit, offset=offset)

    def check_ollama_health(self) -> OllamaHealthResult:
        """Check if the configured Ollama server is reachable.

        This only applies when the underlying LLM client is an OllamaLlmClient.
        Other clients (e.g. FakeLlmClient) are considered always healthy.
        """
        if isinstance(self._llm_client, OllamaLlmClient):
            return self._llm_client.check_health()
        return OllamaHealthResult(
            reachable=True,
            server_ok=True,
            message="Non-Ollama LLM client is active.",
            base_url="",
        )

    def check_ollama_model(self) -> OllamaHealthResult:
        """Check if the default model is available on the Ollama server."""
        if isinstance(self._llm_client, OllamaLlmClient):
            return self._llm_client.check_model(self._default_model)
        return OllamaHealthResult(
            reachable=True,
            server_ok=True,
            model_available=True,
            message="Non-Ollama LLM client is active.",
            base_url="",
        )

    def ask_indexed_documents(
        self,
        question: str,
        prompt_id: str = "default_answer",
        options: RagQueryOptions | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> RagAnswer:
        self._ensure_initialized()

        # Pre-flight check: fail fast if Ollama is not reachable or the model is missing.
        if options is None:
            options = RagQueryOptions()
        if on_token is not None:
            options.on_token = on_token
        model = options.model or self._default_model
        if isinstance(self._llm_client, OllamaLlmClient):
            health = self._llm_client.check_model(model)
            if not health.is_healthy:
                logger.warning(f"[AiRagApplicationService] Cannot answer: {health.message}")
                return RagAnswer(
                    answer_text="",
                    citations=[],
                    prompt_payload=None,
                    llm_result=None,
                    warnings=["[OLLAMA_CONNECTION_FAILED]", health.message],
                )
            if health.model_available is False:
                logger.warning(f"[AiRagApplicationService] Cannot answer: {health.message}")
                return RagAnswer(
                    answer_text="",
                    citations=[],
                    prompt_payload=None,
                    llm_result=None,
                    warnings=["[OLLAMA_MODEL_NOT_FOUND]", health.message],
                )

        self._last_answer = self._rag_service.answer_question(question, prompt_id, options)
        return self._last_answer

    def ask_indexed_document(
        self,
        document_id: str,
        question: str,
        options: RagQueryOptions | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> RagAnswer:
        self._ensure_initialized()
        if on_token is not None:
            if options is None:
                options = RagQueryOptions()
            options.on_token = on_token
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
        progress_callback: ProgressCallback | None = None,
    ) -> dict:
        self._ensure_initialized()
        self._cancel_requested = False

        indexed_count = 0
        failed_count = 0
        warnings: list[str] = []
        document_ids: list[str] = []
        total_items = len(note_items)
        processed = 0

        for item in note_items:
            if self._cancel_requested:
                warnings.append("색인 작업이 중지되었습니다.")
                break

            processed += 1
            label = (
                item.get("title")
                or item.get("source_path")
                or item.get("note_id")
                or item.get("id")
                or ""
            )
            self._notify_progress(progress_callback, "note", label, processed, total_items or processed)
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
