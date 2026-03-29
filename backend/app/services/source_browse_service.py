"""List sources and inspect extraction (admin UI)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.rbac import can_read_crawl_config, can_write_crawl_config
from app.core.exceptions import NotFoundError
from app.models.admin import AdminUser
from app.models.enums import SourceType
from app.models.extracted import DocumentChunk, ExtractedDocument
from app.repositories.source import SourceRepository
from app.schemas.admin_source import (
    ChunkInspectItem,
    ExtractedDocumentInspectResponse,
    RetryExtractionResponse,
    SourceExtractionInspectResponse,
    SourceSummaryResponse,
)
from app.services.html_extraction_service import extract_html_source
from app.services.pdf_extraction_service import extract_pdf_source

_MAX_CHUNK_CHARS = 12_000
_MAX_FULL_TEXT_PREVIEW = 24_000


def list_sources(
    session: Session,
    tenant_id: int,
    actor: AdminUser,
    *,
    source_type: str | None,
    source_status: str | None,
    is_active: bool | None,
    limit: int,
    offset: int,
) -> list[SourceSummaryResponse]:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    st_enum = None
    if source_type:
        try:
            st_enum = SourceType(source_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid source_type",
            ) from e

    status_enum = None
    if source_status:
        from app.models.enums import SourceStatus

        try:
            status_enum = SourceStatus(source_status)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid source_status",
            ) from e

    repo = SourceRepository(session)
    rows = repo.list_for_tenant(
        tenant_id,
        source_type=st_enum,
        status=status_enum,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return [SourceSummaryResponse.model_validate(s) for s in rows]


def inspect_source_extraction(
    session: Session,
    tenant_id: int,
    source_id: int,
    actor: AdminUser,
    *,
    chunk_limit: int,
    chunk_offset: int,
) -> SourceExtractionInspectResponse:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    repo = SourceRepository(session)
    source = repo.get_for_tenant(source_id, tenant_id)
    if source is None:
        raise NotFoundError("Source not found")

    doc_stmt = (
        select(ExtractedDocument)
        .where(
            ExtractedDocument.tenant_id == tenant_id,
            ExtractedDocument.source_id == source_id,
        )
        .order_by(ExtractedDocument.id.desc())
        .limit(1)
    )
    doc = session.scalars(doc_stmt).first()

    count_total = 0
    chunks_out: list[ChunkInspectItem] = []
    doc_response: ExtractedDocumentInspectResponse | None = None

    if doc is not None:
        count_stmt = select(func.count()).select_from(DocumentChunk).where(
            DocumentChunk.extracted_document_id == doc.id,
        )
        count_total = int(session.scalar(count_stmt) or 0)

        chunk_stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.extracted_document_id == doc.id)
            .order_by(DocumentChunk.chunk_index)
            .limit(chunk_limit)
            .offset(chunk_offset)
        )
        for c in session.scalars(chunk_stmt).all():
            text = c.content
            if len(text) > _MAX_CHUNK_CHARS:
                text = text[:_MAX_CHUNK_CHARS] + "…"
            chunks_out.append(
                ChunkInspectItem(
                    id=c.id,
                    chunk_index=c.chunk_index,
                    heading=c.heading,
                    page_number=c.page_number,
                    content=text,
                ),
            )

        preview = doc.full_text
        if preview is not None and len(preview) > _MAX_FULL_TEXT_PREVIEW:
            preview = preview[:_MAX_FULL_TEXT_PREVIEW] + "…"

        doc_response = ExtractedDocumentInspectResponse(
            id=doc.id,
            source_id=doc.source_id,
            source_snapshot_id=doc.source_snapshot_id,
            title=doc.title,
            language=doc.language,
            page_count=doc.page_count,
            extraction_hash=doc.extraction_hash,
            indexed_extraction_hash=doc.indexed_extraction_hash,
            indexed_at=doc.indexed_at,
            full_text_preview=preview,
            extraction_metadata=doc.extraction_metadata,
        )

    return SourceExtractionInspectResponse(
        source=SourceSummaryResponse.model_validate(source),
        document=doc_response,
        chunks=chunks_out,
        chunk_total=count_total,
        chunk_limit=chunk_limit,
        chunk_offset=chunk_offset,
    )


def retry_source_extraction(
    session: Session,
    tenant_id: int,
    source_id: int,
    actor: AdminUser,
) -> RetryExtractionResponse:
    if not can_write_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    repo = SourceRepository(session)
    source = repo.get_for_tenant(source_id, tenant_id)
    if source is None:
        raise NotFoundError("Source not found")

    if source.source_type == SourceType.html_page:
        doc = extract_html_source(session, source_id, tenant_id=tenant_id, force=True)
    elif source.source_type == SourceType.pdf:
        doc = extract_pdf_source(session, source_id, tenant_id=tenant_id, force=True)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Retry extraction is only supported for HTML and PDF sources.",
        )

    return RetryExtractionResponse(
        source_type=source.source_type,
        extracted_document_id=doc.id,
    )
