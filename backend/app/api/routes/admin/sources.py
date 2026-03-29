"""Per-source operations (HTML and PDF extraction)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SessionDep
from app.auth.deps import TenantAdminDep, TenantReaderDep
from app.schemas.admin_source import (
    RetryExtractionResponse,
    SourceExtractionInspectResponse,
    SourceSummaryResponse,
)
from app.schemas.extraction import (
    ExtractHtmlRequest,
    ExtractHtmlResponse,
    ExtractPdfRequest,
    ExtractPdfResponse,
)
from app.services import source_browse_service
from app.services.html_extraction_service import extract_html_source
from app.services.pdf_extraction_service import extract_pdf_source

router = APIRouter(prefix="/tenants/{tenant_id}/sources", tags=["admin-sources"])


@router.get("", response_model=list[SourceSummaryResponse])
def list_sources(
    tenant_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
    source_type: Annotated[str | None, Query(description="html_page | pdf | manual_text")] = None,
    source_status: Annotated[str | None, Query(alias="status")] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> list[SourceSummaryResponse]:
    return source_browse_service.list_sources(
        session,
        tenant_id,
        actor,
        source_type=source_type,
        source_status=source_status,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get("/{source_id}/extraction", response_model=SourceExtractionInspectResponse)
def get_source_extraction(
    tenant_id: int,
    source_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
    chunk_limit: Annotated[int, Query(ge=1, le=500)] = 100,
    chunk_offset: Annotated[int, Query(ge=0)] = 0,
) -> SourceExtractionInspectResponse:
    return source_browse_service.inspect_source_extraction(
        session,
        tenant_id,
        source_id,
        actor,
        chunk_limit=chunk_limit,
        chunk_offset=chunk_offset,
    )


@router.post("/{source_id}/retry-extraction", response_model=RetryExtractionResponse)
def post_retry_source_extraction(
    tenant_id: int,
    source_id: int,
    session: SessionDep,
    actor: TenantAdminDep,
) -> RetryExtractionResponse:
    return source_browse_service.retry_source_extraction(session, tenant_id, source_id, actor)


@router.post(
    "/{source_id}/extract",
    response_model=ExtractHtmlResponse,
    status_code=status.HTTP_200_OK,
)
def extract_html_for_source(
    tenant_id: int,
    source_id: int,
    body: ExtractHtmlRequest,
    session: SessionDep,
    _actor: TenantAdminDep,
) -> ExtractHtmlResponse:
    try:
        doc = extract_html_source(
            session,
            source_id,
            tenant_id=tenant_id,
            force=body.force,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    return ExtractHtmlResponse(
        extracted_document_id=doc.id,
        source_snapshot_id=doc.source_snapshot_id,
        title=doc.title,
        language=doc.language,
        extraction_hash=doc.extraction_hash,
    )


@router.post(
    "/{source_id}/extract-pdf",
    response_model=ExtractPdfResponse,
    status_code=status.HTTP_200_OK,
)
def extract_pdf_for_source(
    tenant_id: int,
    source_id: int,
    body: ExtractPdfRequest,
    session: SessionDep,
    _actor: TenantAdminDep,
) -> ExtractPdfResponse:
    try:
        doc = extract_pdf_source(
            session,
            source_id,
            tenant_id=tenant_id,
            force=body.force,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    return ExtractPdfResponse(
        extracted_document_id=doc.id,
        source_snapshot_id=doc.source_snapshot_id,
        title=doc.title,
        page_count=doc.page_count,
        extraction_hash=doc.extraction_hash,
    )
