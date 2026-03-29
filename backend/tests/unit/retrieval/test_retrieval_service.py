"""Retrieval service behavior (lightweight mocks)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.retrieval.retrieval_service import retrieve_hybrid
from app.retrieval.types import RetrievalFilters


def test_empty_query_skips_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[object] = []

    def boom_embed(_: object) -> list[list[float]]:
        called.append(True)
        return [[0.0] * 1536]

    monkeypatch.setattr(
        "app.retrieval.retrieval_service.OpenAIEmbeddingGenerator",
        lambda: MagicMock(embed_batch=boom_embed),
    )
    session = MagicMock()
    r = retrieve_hybrid(session, tenant_id=1, query="  \t  ")
    assert r.chunks == ()
    assert called == []


def test_filters_passed_to_search(monkeypatch: pytest.MonkeyPatch) -> None:
    v_args: dict[str, object] = {}
    f_args: dict[str, object] = {}

    def fake_v(_session: object, **kw: object) -> list:
        v_args.update(kw)
        return []

    def fake_f(_session: object, **kw: object) -> list:
        f_args.update(kw)
        return []

    monkeypatch.setattr("app.retrieval.retrieval_service._vector_search", fake_v)
    monkeypatch.setattr("app.retrieval.retrieval_service._fts_search", fake_f)

    gen = MagicMock()
    gen.embed_batch.return_value = [[0.1] * 1536]

    flt = RetrievalFilters(source_ids=(42,), page_number=3)
    session = MagicMock()
    retrieve_hybrid(
        session,
        tenant_id=7,
        query="hello world",
        filters=flt,
        embedding_generator=gen,
        top_k=2,
    )
    assert v_args["tenant_id"] == 7
    assert v_args["filters"] is flt
    assert f_args["tenant_id"] == 7
    assert f_args["filters"] is flt
