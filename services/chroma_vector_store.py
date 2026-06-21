from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class ChromaVectorStore:
    def __init__(
        self,
        persist_dir: str | Path,
        collection_name: str = "ai_document_chunks",
    ):
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._enabled = False

        try:
            import chromadb

            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = self._client.get_or_create_collection(name=self.collection_name)
            self._enabled = True
            logger.info("[ChromaVectorStore] initialized: path=%s collection=%s", self.persist_dir, self.collection_name)
        except Exception as e:
            logger.warning("[ChromaVectorStore] disabled: %s", e)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._collection is not None

    def upsert_chunks(
        self,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
    ) -> int:
        if not self.enabled:
            return 0

        valid_ids: list[str] = []
        valid_embeddings: list[list[float]] = []
        valid_texts: list[str] = []
        valid_metadatas: list[dict] = []

        for idx, chunk_id in enumerate(chunk_ids):
            if idx >= len(embeddings):
                continue
            embedding = embeddings[idx] or []
            if not embedding:
                continue

            valid_ids.append(chunk_id)
            valid_embeddings.append(embedding)
            valid_texts.append(texts[idx] if idx < len(texts) else "")
            if metadatas and idx < len(metadatas):
                valid_metadatas.append(metadatas[idx])
            else:
                valid_metadatas.append({})

        if not valid_ids:
            return 0

        self._collection.upsert(
            ids=valid_ids,
            embeddings=valid_embeddings,
            documents=valid_texts,
            metadatas=valid_metadatas,
        )
        return len(valid_ids)

    def delete_document_chunks(self, document_id: str) -> None:
        if not self.enabled:
            return
        self._collection.delete(where={"document_id": document_id})

    def delete_chunk_ids(self, chunk_ids: list[str]) -> None:
        if not self.enabled or not chunk_ids:
            return
        self._collection.delete(ids=chunk_ids)

    def clear_all(self) -> None:
        if not self.enabled:
            return
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)

    def query(self, embedding: list[float], limit: int = 10) -> list[str]:
        if not self.enabled or not embedding:
            return []

        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=max(1, limit),
            include=["distances"],
        )

        ids = result.get("ids", [])
        if not ids:
            return []
        return [chunk_id for chunk_id in ids[0] if chunk_id]
