import json
import logging
from typing import Optional, Any
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QVariant

from services.ai_rag_application_service import AiRagApplicationService
from services.ai_rag_service import RagAnswer, RagCitation
from services.ai_search_service import SearchResultChunk
from services.document_chunk_model import IndexedDocument


logger = logging.getLogger(__name__)


class FakeAppService:
    def __init__(self):
        self._initialized = False
        self._closed = False
        self._last_answer: Optional[RagAnswer] = None
        self._last_search_results: list[SearchResultChunk] = []
        self._indexed_docs: dict[str, IndexedDocument] = {}

    def initialize(self) -> None:
        self._initialized = True

    def close(self) -> None:
        self._closed = True

    def is_initialized(self) -> bool:
        return self._initialized

    def is_closed(self) -> bool:
        return self._closed

    def index_current_note(
        self,
        note_id: str,
        title: str | None,
        content: str,
        tags: list[str] | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> IndexedDocument:
        doc_id = f"note:{note_id}"
        doc = IndexedDocument(
            document_id=doc_id,
            source_type="note",
            source_path=None,
            note_id=note_id,
            title=title or "",
            body_checksum="fake_checksum",
            tags=tags or [],
        )
        self._indexed_docs[doc_id] = doc
        return doc

    def search_index(self, query: str, limit: int = 20, offset: int = 0) -> list[SearchResultChunk]:
        results = []
        for doc_id, doc in self._indexed_docs.items():
            if query.lower() in doc.title.lower():
                results.append(SearchResultChunk(
                    chunk_id=f"{doc_id}:0:fake",
                    document_id=doc_id,
                    title=doc.title,
                    source_type=doc.source_type,
                    source_path=doc.source_path,
                    note_id=doc.note_id,
                    heading_path=[],
                    chunk_text=f"Content for {doc.title}",
                    snippet=f"Snippet for {doc.title}",
                    score=1.0,
                    chunk_order=0,
                ))
        return results[:limit]

    def ask_indexed_documents(
        self, question: str, options: Any = None
    ) -> RagAnswer:
        self._last_answer = RagAnswer(
            answer_text="Fake answer from FakeAppService",
            citations=[
                RagCitation(
                    source_id="S1",
                    chunk_id="fake:0",
                    document_id="note:fake",
                    title="Fake Note",
                    source_type="note",
                    source_path=None,
                    note_id="fake",
                    heading_path=[],
                    chunk_order=0,
                    cited_in_answer=True,
                )
            ],
            prompt_payload=None,
            llm_result=None,
            warnings=[],
        )
        return self._last_answer

    def ask_indexed_document(
        self, document_id: str, question: str, options: Any = None
    ) -> RagAnswer:
        self._last_answer = RagAnswer(
            answer_text=f"Fake answer for {document_id}",
            citations=[
                RagCitation(
                    source_id="S1",
                    chunk_id=f"{document_id}:0:fake",
                    document_id=document_id,
                    title="Fake Doc",
                    source_type="note",
                    source_path=None,
                    note_id=None,
                    heading_path=[],
                    chunk_order=0,
                    cited_in_answer=True,
                )
            ],
            prompt_payload=None,
            llm_result=None,
            warnings=[],
        )
        return self._last_answer

    def clear_index(self) -> None:
        self._indexed_docs.clear()
        self._last_answer = None
        self._last_search_results = []

    def get_last_answer(self) -> RagAnswer | None:
        return self._last_answer

    def index_note_items(
        self,
        note_items: list[dict],
        scope_label: str = "manual",
    ) -> dict:
        indexed_count = 0
        failed_count = 0
        warnings: list[str] = []
        document_ids: list[str] = []

        for item in note_items:
            try:
                note_id = item.get("note_id") or item.get("id")
                if not note_id:
                    warnings.append("Missing note_id, skipping")
                    failed_count += 1
                    continue

                doc_id = f"note:{note_id}"
                doc = IndexedDocument(
                    document_id=doc_id,
                    source_type="note",
                    source_path=None,
                    note_id=note_id,
                    title=item.get("title", ""),
                    body_checksum="fake_checksum",
                    tags=item.get("tags", []),
                )
                self._indexed_docs[doc_id] = doc
                indexed_count += 1
                document_ids.append(doc_id)
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

    def index_external_files(
        self,
        file_paths: list,
    ) -> dict:
        indexed_count = 0
        failed_count = 0
        warnings: list[str] = []
        document_ids: list[str] = []

        for path in file_paths:
            try:
                doc_id = f"file:{path}"
                doc = IndexedDocument(
                    document_id=doc_id,
                    source_type="file",
                    source_path=path,
                    note_id=None,
                    title=str(path).split("/")[-1].split("\\")[-1],
                    body_checksum="fake_checksum",
                    tags=[],
                )
                self._indexed_docs[doc_id] = doc
                indexed_count += 1
                document_ids.append(doc_id)
            except Exception as e:
                warnings.append(f"Failed to index {path}: {e}")
                failed_count += 1

        return {
            "indexed_count": indexed_count,
            "failed_count": failed_count,
            "warnings": warnings,
            "document_ids": document_ids,
        }


class AiRagController(QObject):
    ragAnswerReady = pyqtSignal(str)
    ragCitationsChanged = pyqtSignal()
    ragWarningsChanged = pyqtSignal()
    indexStatusChanged = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    searchResultsChanged = pyqtSignal()

    def __init__(self, app_service: AiRagApplicationService | None = None, parent=None):
        super().__init__(parent)
        self._app_service = app_service
        self._last_answer: Optional[RagAnswer] = None
        self._last_warnings: list[str] = []
        self._last_search_results: list[SearchResultChunk] = []
        self._last_index_result: dict = {}

    def _get_app_service(self) -> AiRagApplicationService:
        if self._app_service is None:
            self._app_service = AiRagApplicationService()
        return self._app_service

    @pyqtSlot()
    def initialize(self) -> None:
        try:
            self._get_app_service().initialize()
            self.indexStatusChanged.emit("ready")
        except Exception as e:
            logger.error(f"[AiRagController] initialize failed: {e}")
            self.errorOccurred.emit(f"초기화 실패: {e}")

    @pyqtSlot()
    def close(self) -> None:
        try:
            if self._app_service is not None:
                self._app_service.close()
            self.indexStatusChanged.emit("closed")
        except Exception as e:
            logger.error(f"[AiRagController] close failed: {e}")
            self.errorOccurred.emit(f"종료 실패: {e}")

    @pyqtSlot(str, str, str, str)
    def indexCurrentNote(self, note_id: str, title: str, content: str, tags_json: str = "[]") -> None:
        try:
            tags = []
            if tags_json:
                try:
                    tags = json.loads(tags_json)
                except json.JSONDecodeError:
                    logger.warning(f"[AiRagController] Failed to parse tags_json: {tags_json}")
                    tags = []

            self._get_app_service().index_current_note(
                note_id=note_id,
                title=title or None,
                content=content,
                tags=tags if tags else None,
            )
            self.indexStatusChanged.emit("indexed_current_note")
        except Exception as e:
            logger.error(f"[AiRagController] indexCurrentNote failed: {e}")
            self.errorOccurred.emit(f"색인 실패: {e}")

    @pyqtSlot(str, int, int)
    def searchIndexedDocuments(self, query: str, limit: int = 20, offset: int = 0) -> None:
        try:
            if not query or not query.strip():
                self._last_search_results = []
                self.searchResultsChanged.emit()
                return

            self._last_search_results = self._get_app_service().search_index(
                query=query.strip(),
                limit=limit,
                offset=offset,
            )
            self.searchResultsChanged.emit()
        except Exception as e:
            logger.error(f"[AiRagController] searchIndexedDocuments failed: {e}")
            self.errorOccurred.emit(f"검색 실패: {e}")

    @pyqtSlot(str)
    def askIndexedDocuments(self, question: str) -> None:
        try:
            if not question or not question.strip():
                self.errorOccurred.emit("질문을 입력해주세요.")
                return

            self._last_answer = self._get_app_service().ask_indexed_documents(question.strip())
            self._last_warnings = self._last_answer.warnings

            self.ragAnswerReady.emit(self._last_answer.answer_text)
            self.ragCitationsChanged.emit()
            self.ragWarningsChanged.emit()
        except Exception as e:
            logger.error(f"[AiRagController] askIndexedDocuments failed: {e}")
            self.errorOccurred.emit(f"질문 실패: {e}")

    @pyqtSlot(str, str)
    def askIndexedDocument(self, document_id: str, question: str) -> None:
        try:
            if not document_id:
                self.errorOccurred.emit("문서 ID가 필요합니다.")
                return
            if not question or not question.strip():
                self.errorOccurred.emit("질문을 입력해주세요.")
                return

            self._last_answer = self._get_app_service().ask_indexed_document(
                document_id, question.strip()
            )
            self._last_warnings = self._last_answer.warnings

            self.ragAnswerReady.emit(self._last_answer.answer_text)
            self.ragCitationsChanged.emit()
            self.ragWarningsChanged.emit()
        except Exception as e:
            logger.error(f"[AiRagController] askIndexedDocument failed: {e}")
            self.errorOccurred.emit(f"질문 실패: {e}")

    @pyqtSlot()
    def clearIndex(self) -> None:
        try:
            self._get_app_service().clear_index()
            self._last_answer = None
            self._last_warnings = []
            self._last_search_results = []
            self._last_index_result = {}
            self.indexStatusChanged.emit("cleared")
        except Exception as e:
            logger.error(f"[AiRagController] clearIndex failed: {e}")
            self.errorOccurred.emit(f"초기화 실패: {e}")

    @pyqtSlot(str, str)
    def indexNotesJson(self, notes_json: str, scope_label: str = "") -> None:
        try:
            note_items = []
            if notes_json:
                try:
                    note_items = json.loads(notes_json)
                    if not isinstance(note_items, list):
                        note_items = []
                except json.JSONDecodeError:
                    logger.warning(f"[AiRagController] Failed to parse notes_json")
                    note_items = []

            if not note_items:
                self._last_index_result = {
                    "indexed_count": 0,
                    "failed_count": 0,
                    "warnings": ["No notes to index"],
                    "document_ids": [],
                }
                self.indexStatusChanged.emit("indexed_empty")
                return

            result = self._get_app_service().index_note_items(note_items, scope_label)
            self._last_index_result = result

            if scope_label == "folder":
                self.indexStatusChanged.emit("indexed_folder")
            elif scope_label == "all":
                self.indexStatusChanged.emit("indexed_all_notes")
            else:
                self.indexStatusChanged.emit("indexed_notes")
        except Exception as e:
            logger.error(f"[AiRagController] indexNotesJson failed: {e}")
            self.errorOccurred.emit(f"색인 실패: {e}")

    @pyqtSlot(str, str)
    def indexCurrentFolderNotes(self, notes_json: str, folder_id: str = "") -> None:
        self.indexNotesJson(notes_json, "folder")

    @pyqtSlot(str)
    def indexAllNotesJson(self, notes_json: str) -> None:
        self.indexNotesJson(notes_json, "all")

    @pyqtSlot(str)
    def indexExternalFilesJson(self, paths_json: str) -> None:
        try:
            file_paths = []
            if paths_json:
                try:
                    file_paths = json.loads(paths_json)
                    if not isinstance(file_paths, list):
                        file_paths = []
                except json.JSONDecodeError:
                    logger.warning(f"[AiRagController] Failed to parse paths_json")
                    file_paths = []

            if not file_paths:
                self._last_index_result = {
                    "indexed_count": 0,
                    "failed_count": 0,
                    "warnings": ["No files to index"],
                    "document_ids": [],
                }
                self.indexStatusChanged.emit("indexed_empty")
                return

            result = self._get_app_service().index_external_files(file_paths)
            self._last_index_result = result
            self.indexStatusChanged.emit("indexed_external_files")
        except Exception as e:
            logger.error(f"[AiRagController] indexExternalFilesJson failed: {e}")
            self.errorOccurred.emit(f"외부 파일 색인 실패: {e}")

    @pyqtSlot(str)
    def indexExternalFolder(self, folder_path: str) -> None:
        try:
            if not folder_path:
                self._last_index_result = {
                    "indexed_count": 0,
                    "failed_count": 0,
                    "warnings": ["No folder specified"],
                    "document_ids": [],
                }
                self.indexStatusChanged.emit("indexed_empty")
                return

            result = self._get_app_service().index_external_folder(folder_path)
            self._last_index_result = result
            self.indexStatusChanged.emit("indexed_external_folder")
        except Exception as e:
            logger.error(f"[AiRagController] indexExternalFolder failed: {e}")
            self.errorOccurred.emit(f"외부 폴더 색인 실패: {e}")

    @pyqtSlot(result=str)
    def getLastIndexResultJson(self) -> str:
        try:
            return json.dumps(self._last_index_result, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[AiRagController] getLastIndexResultJson failed: {e}")
            return "{}"

    @pyqtSlot(result=str)
    def getLastAnswerText(self) -> str:
        if self._last_answer is None:
            return ""
        return self._last_answer.answer_text

    @pyqtSlot(result=str)
    def getLastCitationsJson(self) -> str:
        if self._last_answer is None:
            return "[]"
        try:
            citations = []
            for c in self._last_answer.citations:
                citations.append({
                    "source_id": c.source_id,
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "title": c.title,
                    "source_type": c.source_type,
                    "source_path": c.source_path,
                    "note_id": c.note_id,
                    "heading_path": c.heading_path,
                    "chunk_order": c.chunk_order,
                    "cited_in_answer": c.cited_in_answer,
                })
            return json.dumps(citations, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[AiRagController] getLastCitationsJson failed: {e}")
            return "[]"

    @pyqtSlot(result=str)
    def getLastWarningsJson(self) -> str:
        try:
            return json.dumps(self._last_warnings, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[AiRagController] getLastWarningsJson failed: {e}")
            return "[]"

    @pyqtSlot(result=str)
    def getSearchResultsJson(self) -> str:
        try:
            results = []
            for r in self._last_search_results:
                results.append({
                    "chunk_id": r.chunk_id,
                    "document_id": r.document_id,
                    "title": r.title,
                    "source_type": r.source_type,
                    "source_path": r.source_path,
                    "note_id": r.note_id,
                    "heading_path": r.heading_path,
                    "chunk_order": r.chunk_order,
                    "score": r.score,
                    "snippet": r.snippet,
                })
            return json.dumps(results, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[AiRagController] getSearchResultsJson failed: {e}")
            return "[]"
