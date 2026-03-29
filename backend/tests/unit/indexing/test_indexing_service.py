"""index_extracted_document: hash skip and re-index path (mocked session, no OpenAI)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.indexing.indexing_service import index_extracted_document
from app.models.extracted import ExtractedDocument
from app.models.source import Source


def test_skips_embedding_when_extraction_hash_unchanged() -> None:
    doc = MagicMock(spec=ExtractedDocument)
    doc.id = 7
    doc.source_id = 3
    doc.extraction_hash = "same"
    doc.indexed_extraction_hash = "same"
    doc.full_text = "## H\nbody"
    src = MagicMock(spec=Source)
    src.id = 3

    session = MagicMock()

    def _get(model: type, pk: object) -> object | None:
        if model is ExtractedDocument and pk == 7:
            return doc
        if model is Source and pk == 3:
            return src
        return None

    session.get.side_effect = _get
    session.scalar.return_value = 4

    gen = MagicMock()
    gen.embed_batch.side_effect = AssertionError("embed_batch must not run when skipped")

    out = index_extracted_document(session, 7, force=False, embedding_generator=gen)

    assert out.skipped is True
    assert out.chunk_count == 4
    assert out.extraction_hash == "same"
    gen.embed_batch.assert_not_called()


def test_force_reindex_embeds_even_when_hash_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = MagicMock(spec=ExtractedDocument)
    doc.id = 7
    doc.source_id = 3
    doc.extraction_hash = "same"
    doc.indexed_extraction_hash = "same"
    doc.full_text = "hello world"

    src = MagicMock(spec=Source)
    src.id = 3
    src.status = MagicMock()

    session = MagicMock()

    def _get(model: type, pk: object) -> object | None:
        if model is ExtractedDocument and pk == 7:
            return doc
        if model is Source and pk == 3:
            return src
        return None

    session.get.side_effect = _get

    from app.indexing.chunker import ChunkDraft

    drafts = [ChunkDraft(content="only chunk", heading=None, page_number=None)]

    monkeypatch.setattr(
        "app.indexing.indexing_service.chunk_extracted_document",
        lambda _doc, **_: drafts,
    )
    monkeypatch.setattr(
        "app.indexing.indexing_service.replace_chunks",
        lambda *_a, **_k: None,
    )

    gen = MagicMock()
    gen.embed_batch.return_value = [[0.1] * 1536]

    out = index_extracted_document(session, 7, force=True, embedding_generator=gen)

    assert out.skipped is False
    assert out.chunk_count == 1
    gen.embed_batch.assert_called_once()
    assert gen.embed_batch.call_args[0][0] == ["only chunk"]
