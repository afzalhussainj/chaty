"""List index jobs for admin UI."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.rbac import can_read_crawl_config
from app.models.admin import AdminUser
from app.repositories.index_job import IndexJobRepository
from app.schemas.index_job import IndexJobResponse


def list_index_jobs(
    session: Session,
    tenant_id: int,
    actor: AdminUser,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[IndexJobResponse]:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = IndexJobRepository(session)
    jobs = repo.list_for_tenant(tenant_id, limit=limit, offset=offset)
    return [IndexJobResponse.model_validate(j) for j in jobs]
