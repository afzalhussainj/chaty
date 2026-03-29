"""Per-source operations (HTML and PDF extraction)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep
from app.auth.deps import TenantAdminDep
from app.schemas.extraction import (
    ExtractHtmlRequest,
    ExtractHtmlResponse,
    ExtractPdfRequest,
    ExtractPdfResponse,
)
from app.services.html_extraction_service import extract_html_source
from app.services.pdf_extraction_service import extract_pdf_source

router = APIRouter(prefix="/tenants/{tenant_id}/sources", tags=["admin-sources"])


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
