"""Index job listing (admin UI)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.auth.deps import TenantReaderDep
from app.schemas.index_job import IndexJobResponse
from app.services import index_job_admin_service

router = APIRouter(prefix="/tenants/{tenant_id}/index-jobs", tags=["admin-index-jobs"])


@router.get("", response_model=list[IndexJobResponse])
def list_index_jobs(
    tenant_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[IndexJobResponse]:
    return index_job_admin_service.list_index_jobs(
        session,
        tenant_id,
        actor,
        limit=limit,
        offset=offset,
    )
