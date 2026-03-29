"""Ensure hybrid retrieval passes tenant_id through every stage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.retrieval.retrieval_service import retrieve_hybrid
from app.retrieval.types import RetrievalFilters


def test_retrieve_hybrid_threads_tenant_id_to_search_and_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stages: list[tuple[str, int]] = []

    def fake_v(
        _session: object,
        *,
        tenant_id: int,
        query_embedding: list[float],
        filters: RetrievalFilters,
        limit: int,
    ) -> list:
        stages.append(("vector", tenant_id))
        return []

    def fake_f(
        _session: object,
        *,
        tenant_id: int,
        fts_text: str,
        filters: RetrievalFilters,
        limit: int,
    ) -> list:
        stages.append(("fts", tenant_id))
        return []

    def fake_load(
        _session: object,
        *,
        tenant_id: int,
        chunk_ids: set[int],
    ) -> dict:
        stages.append(("load", tenant_id))
        return {}

    monkeypatch.setattr("app.retrieval.retrieval_service._vector_search", fake_v)
    monkeypatch.setattr("app.retrieval.retrieval_service._fts_search", fake_f)
    monkeypatch.setattr("app.retrieval.retrieval_service._load_chunk_rows", fake_load)
    monkeypatch.setattr(
        "app.retrieval.retrieval_service.merge_hybrid",
        lambda **_: (),
    )

    gen = MagicMock()
    gen.embed_batch.return_value = [[0.05] * 1536]

    session = MagicMock()
    retrieve_hybrid(
        session,
        tenant_id=42,
        query="hello",
        embedding_generator=gen,
    )

    assert stages == [("vector", 42), ("fts", 42), ("load", 42)]
