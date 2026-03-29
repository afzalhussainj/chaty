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
    scalar_result = MagicMock()
    scalar_result.all.return_value = [42]
    session.scalars.return_value = scalar_result

    retrieve_hybrid(
        session,
        tenant_id=7,
        query="hello world",
        filters=flt,
        embedding_generator=gen,
        top_k=2,
    )
    assert v_args["tenant_id"] == 7
    assert v_args["filters"].source_ids == (42,)
    assert v_args["filters"].page_number == 3
    assert f_args["tenant_id"] == 7
    assert f_args["filters"].source_ids == (42,)


def test_no_embedding_when_filtered_sources_miss_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    embed_calls: list[object] = []

    def capture_embed(_: object) -> MagicMock:
        m = MagicMock()

        def _batch(texts: list[str]) -> list[list[float]]:
            embed_calls.append(texts)
            return [[0.1] * 1536]

        m.embed_batch.side_effect = _batch
        return m

    monkeypatch.setattr(
        "app.retrieval.retrieval_service.OpenAIEmbeddingGenerator",
        capture_embed,
    )
    monkeypatch.setattr("app.retrieval.retrieval_service._vector_search", lambda *a, **k: [])
    monkeypatch.setattr("app.retrieval.retrieval_service._fts_search", lambda *a, **k: [])

    session = MagicMock()
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars.return_value = scalar_result

    r = retrieve_hybrid(
        session,
        tenant_id=1,
        query="hello",
        filters=RetrievalFilters(source_ids=(99999,)),
        top_k=4,
    )
    assert r.chunks == ()
    assert embed_calls == []


def test_cross_tenant_source_ids_removed_before_search(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_filters: list[RetrievalFilters | None] = []

    def fake_v(_session: object, **kw: object) -> list:
        seen_filters.append(kw.get("filters"))
        return []

    def fake_f(_session: object, **kw: object) -> list:
        return []

    monkeypatch.setattr("app.retrieval.retrieval_service._vector_search", fake_v)
    monkeypatch.setattr("app.retrieval.retrieval_service._fts_search", fake_f)

    gen = MagicMock()
    gen.embed_batch.return_value = [[0.1] * 1536]

    session = MagicMock()
    scalar_result = MagicMock()
    scalar_result.all.return_value = [10]
    session.scalars.return_value = scalar_result

    retrieve_hybrid(
        session,
        tenant_id=1,
        query="q",
        filters=RetrievalFilters(source_ids=(10, 99)),
        embedding_generator=gen,
    )
    assert seen_filters and seen_filters[0] is not None
    assert seen_filters[0].source_ids == (10,)
