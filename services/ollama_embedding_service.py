import json
import logging
import socket
import urllib.error
import urllib.request
from typing import Any


logger = logging.getLogger(__name__)


class OllamaEmbeddingService:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "kure",
        timeout_sec: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_sec = timeout_sec

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            return []

        payload = {"model": self.model, "prompt": text}
        endpoint = "/api/embeddings"

        result = self._post_json(endpoint, payload)
        if result is None:
            fallback_payload = {"model": self.model, "input": text}
            result = self._post_json("/api/embed", fallback_payload)

        if not result:
            return []

        if isinstance(result.get("embedding"), list):
            return [float(x) for x in result["embedding"]]

        embeddings = result.get("embeddings")
        if isinstance(embeddings, list) and embeddings and isinstance(embeddings[0], list):
            return [float(x) for x in embeddings[0]]

        return []

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 16,
        progress_callback=None,
    ) -> list[list[float]]:
        if not texts:
            return []

        batch_size = max(1, int(batch_size or 1))
        total = len(texts)
        vectors: list[list[float]] = []

        batch_success = False
        for start in range(0, total, batch_size):
            batch = texts[start : start + batch_size]
            payload = {"model": self.model, "input": batch}
            result = self._post_json("/api/embed", payload)

            if not result:
                batch_success = False
                vectors = []
                break

            embeddings = result.get("embeddings")
            if not isinstance(embeddings, list):
                batch_success = False
                vectors = []
                break

            batch_success = True
            for index, embedding in enumerate(embeddings):
                current = start + index + 1
                if isinstance(embedding, list):
                    vectors.append([float(x) for x in embedding])
                else:
                    vectors.append([])

                if progress_callback:
                    progress_callback(current, total)

        if batch_success and len(vectors) == total:
            return vectors

        logger.info("[OllamaEmbeddingService] Falling back to per-chunk embedding requests")
        vectors = []
        for index, text in enumerate(texts):
            vectors.append(self.embed_text(text))
            if progress_callback:
                progress_callback(index + 1, total)
        return vectors

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                return json.loads(response.read().decode("utf-8"))
        except socket.timeout:
            logger.warning("[OllamaEmbeddingService] Request timeout(%.1fs): endpoint=%s", self.timeout_sec, endpoint)
            return None
        except urllib.error.URLError as e:
            logger.warning("[OllamaEmbeddingService] Request failed: endpoint=%s error=%s", endpoint, e)
            return None
        except TimeoutError:
            logger.warning("[OllamaEmbeddingService] Request timeout: endpoint=%s", endpoint)
            return None
        except Exception as e:
            logger.warning("[OllamaEmbeddingService] Unexpected error: endpoint=%s error=%s", endpoint, e)
            return None
