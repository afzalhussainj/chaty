"""Indexing pipeline against Postgres: chunks, metadata, skip, re-index, PDF pages."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.db.session import SessionLocal, get_engine
from app.indexing.embeddings import FakeEmbeddingGenerator
from app.indexing.indexing_service import index_extracted_document, index_source_latest
from app.models.enums import SourceStatus, SourceType, TenantStatus
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.models.source import Source, SourceSnapshot
from app.models.tenant import Tenant

pytestmark = pytest.mark.integration


@pytest.fixture
def idx_session(integration_database_url: str):
    session = SessionLocal(bind=get_engine())
    try:
        yield session
    finally:
        session.close()


def _seed_html_extracted(idx_session) -> tuple[int, int]:
    slug = f"idx-{uuid.uuid4().hex[:12]}"
    tenant = Tenant(name="Idx Tenant", slug=slug, status=TenantStatus.active)
    idx_session.add(tenant)
    idx_session.flush()

    source = Source(
        tenant_id=tenant.id,
        crawl_config_id=None,
        url="https://example.edu/page",
        canonical_url="https://example.edu/page",
        title="Page title",
        source_type=SourceType.html_page,
        status=SourceStatus.ready_to_index,
    )
    idx_session.add(source)
    idx_session.flush()

    snap = SourceSnapshot(
        source_id=source.id,
        version=1,
        raw_content_hash="raw1",
        byte_length=100,
        mime_type="text/html",
    )
    idx_session.add(snap)
    idx_session.flush()

    doc = ExtractedDocument(
        tenant_id=tenant.id,
        source_id=source.id,
        source_snapshot_id=snap.id,
        extraction_hash="exh-initial",
        title="Doc title",
        full_text="## A\n" + ("alpha " * 50) + "\n\n## B\n" + ("beta " * 50),
        page_count=1,
        extraction_metadata={"fetched_url": "https://example.edu/page-final", "headings": []},
    )
    idx_session.add(doc)
    idx_session.commit()
    return source.id, doc.id


def test_index_metadata_and_skip_reindex(idx_session) -> None:
    source_id, doc_id = _seed_html_extracted(idx_session)
    gen = FakeEmbeddingGenerator()

    out1 = index_extracted_document(idx_session, doc_id, embedding_generator=gen, index_job=None)
    assert out1.skipped is False
    assert out1.chunk_count >= 1
    idx_session.commit()

    src_row = idx_session.get(Source, source_id)
    assert src_row is not None

    chunks = idx_session.scalars(
        select(DocumentChunk).where(DocumentChunk.extracted_document_id == doc_id).order_by(
            DocumentChunk.chunk_index,
        ),
    ).all()
    assert chunks[0].tenant_id == src_row.tenant_id
    assert chunks[0].source_id == source_id
    assert chunks[0].extracted_document_id == doc_id
    assert chunks[0].source_url == "https://example.edu/page-final"
    assert chunks[0].title == "Doc title"
    assert chunks[0].chunk_index == 0
    assert chunks[0].content_hash
    assert chunks[0].embedding is not None
    assert len(chunks[0].embedding) == 1536

    src = idx_session.get(Source, source_id)
    assert src is not None
    assert src.status == SourceStatus.indexed

    out2 = index_extracted_document(idx_session, doc_id, embedding_generator=gen, index_job=None)
    assert out2.skipped is True
    idx_session.commit()


def test_force_reindex_replaces_chunks(idx_session) -> None:
    _, doc_id = _seed_html_extracted(idx_session)
    gen = FakeEmbeddingGenerator()
    index_extracted_document(idx_session, doc_id, embedding_generator=gen)
    idx_session.commit()

    doc = idx_session.get(ExtractedDocument, doc_id)
    assert doc is not None
    doc.full_text = "## Only\nnew content here."
    doc.extraction_hash = "exh-updated"
    idx_session.commit()

    index_extracted_document(idx_session, doc_id, force=True, embedding_generator=gen)
    idx_session.commit()

    chunks = idx_session.scalars(
        select(DocumentChunk).where(DocumentChunk.extracted_document_id == doc_id),
    ).all()
    assert len(chunks) >= 1
    assert "new content" in chunks[0].content


def test_pdf_chunks_carry_page_numbers(idx_session) -> None:
    slug = f"pdf-{uuid.uuid4().hex[:12]}"
    tenant = Tenant(name="Pdf Tenant", slug=slug, status=TenantStatus.active)
    idx_session.add(tenant)
    idx_session.flush()

    source = Source(
        tenant_id=tenant.id,
        crawl_config_id=None,
        url="https://example.edu/a.pdf",
        canonical_url="https://example.edu/a.pdf",
        title="PDF",
        source_type=SourceType.pdf,
        status=SourceStatus.ready_to_index,
    )
    idx_session.add(source)
    idx_session.flush()

    snap = SourceSnapshot(
        source_id=source.id,
        version=1,
        raw_content_hash="rawp",
        byte_length=1000,
        mime_type="application/pdf",
    )
    idx_session.add(snap)
    idx_session.flush()

    doc = ExtractedDocument(
        tenant_id=tenant.id,
        source_id=source.id,
        source_snapshot_id=snap.id,
        extraction_hash="exh-pdf",
        title="PDF doc",
        full_text="[[PAGE 1]]\nhello\n\n[[PAGE 2]]\nworld",
        page_count=2,
        extraction_metadata={"kind": "pdf", "fetched_url": "https://example.edu/a.pdf"},
    )
    idx_session.add(doc)
    idx_session.commit()

    gen = FakeEmbeddingGenerator()
    index_extracted_document(idx_session, doc.id, embedding_generator=gen)
    idx_session.commit()

    by_page = {
        c.page_number: c.content.strip()
        for c in idx_session.scalars(select(DocumentChunk).where(DocumentChunk.extracted_document_id == doc.id)).all()
    }
    assert 1 in by_page and "hello" in by_page[1]
    assert 2 in by_page and "world" in by_page[2]


def test_index_source_latest(idx_session) -> None:
    sid, doc_id = _seed_html_extracted(idx_session)
    gen = FakeEmbeddingGenerator()
    out = index_source_latest(idx_session, sid, embedding_generator=gen)
    assert out.chunk_count >= 1
    idx_session.commit()
