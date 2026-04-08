"""OpenAI embedding generation (batch API via httpx)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import httpx

from app.core.settings import get_settings
from app.models.extracted import EMBEDDING_DIMENSION


@runtime_checkable
class EmbeddingGenerator(Protocol):
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text (same order)."""
        ...


class OpenAIEmbeddingGenerator:
    """Calls OpenAI `/v1/embeddings` with configurable model (default text-embedding-3-small)."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        batch_size: int = 100,
        timeout_s: float = 120.0,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self._model = model if model is not None else settings.openai_embedding_model
        self._batch_size = max(1, min(batch_size, 2048))
        self._timeout_s = timeout_s

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._api_key:
            msg = "OPENAI_API_KEY / openai_api_key is not set"
            raise RuntimeError(msg)

        out: list[list[float]] = []
        with httpx.Client(timeout=self._timeout_s) as client:
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]
                chunk = self._post_embeddings(client, batch)
                out.extend(chunk)
        return out

    def _post_embeddings(self, client: httpx.Client, batch: list[str]) -> list[list[float]]:
        resp = client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=self._embeddings_request_body(batch),
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data") or []
        # API returns sorted by index when batching
        items = sorted(items, key=lambda x: int(x.get("index", 0)))
        vectors: list[list[float]] = []
        for item in items:
            emb = item.get("embedding")
            if not isinstance(emb, list) or len(emb) != EMBEDDING_DIMENSION:
                msg = f"Unexpected embedding shape from API (expected dim {EMBEDDING_DIMENSION})"
                raise RuntimeError(msg)
            vectors.append([float(x) for x in emb])
        if len(vectors) != len(batch):
            msg = "Embedding count does not match batch size"
            raise RuntimeError(msg)
        return vectors

    def _embeddings_request_body(self, batch: list[str]) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._model,
            "input": batch,
        }
        if self._model.startswith("text-embedding-3"):
            body["dimensions"] = EMBEDDING_DIMENSION
        return body


class FakeEmbeddingGenerator:
    """Deterministic fake vectors for tests (no network)."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for i, _ in enumerate(texts):
            base = (i % 10) / 100.0
            vec = [base + (j / float(EMBEDDING_DIMENSION)) for j in range(EMBEDDING_DIMENSION)]
            out.append(vec)
        return out
