"""Create and inspect crawl jobs (queue worker execution)."""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.rbac import can_read_crawl_config, can_write_crawl_config
from app.core.exceptions import NotFoundError
from app.models.admin import AdminUser
from app.models.enums import AuditAction, JobStatus
from app.models.job import CrawlJob
from app.repositories.crawl_config import CrawlConfigRepository
from app.repositories.crawl_job import CrawlJobRepository
from app.schemas.crawl_job import CrawlJobCreate, CrawlJobResponse
from app.services.audit_service import write_audit


def get_job(session: Session, tenant_id: int, job_id: int, actor: AdminUser) -> CrawlJobResponse:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlJobRepository(session)
    job = repo.get(job_id, tenant_id)
    if job is None:
        raise NotFoundError("Crawl job not found")
    return CrawlJobResponse.model_validate(job)


def create_job(
    session: Session,
    tenant_id: int,
    body: CrawlJobCreate,
    actor: AdminUser,
    request: Request,
) -> CrawlJobResponse:
    if not can_write_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    cfg_repo = CrawlConfigRepository(session)
    cfg = cfg_repo.get(body.crawl_config_id, tenant_id)
    if cfg is None:
        raise NotFoundError("Crawl configuration not found")

    stats: dict = {"dry_run": body.dry_run, "use_sitemap": body.use_sitemap}
    if body.seed_url is not None:
        stats["seed_url"] = str(body.seed_url)
    if body.workflow:
        stats["workflow"] = body.workflow

    job = CrawlJob(
        tenant_id=tenant_id,
        crawl_config_id=body.crawl_config_id,
        job_type=body.job_type,
        status=JobStatus.queued,
        stats=stats,
        created_by_id=actor.id,
    )
    repo = CrawlJobRepository(session)
    repo.add(job)
    session.flush()

    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant_id,
        action=AuditAction.crawl_triggered,
        resource_type="CrawlJob",
        resource_id=str(job.id),
        details={
            "job_type": body.job_type.value,
            "crawl_config_id": body.crawl_config_id,
            "dry_run": body.dry_run,
            "workflow": body.workflow,
        },
        request=request,
    )

    from app.workers.tasks.crawl import run_crawl_job_task

    run_crawl_job_task.delay(job.id)

    return CrawlJobResponse.model_validate(job)


def list_jobs(
    session: Session,
    tenant_id: int,
    actor: AdminUser,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[CrawlJobResponse]:
    if not can_read_crawl_config(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = CrawlJobRepository(session)
    jobs = repo.list_for_tenant(tenant_id, limit=limit, offset=offset)
    return [CrawlJobResponse.model_validate(j) for j in jobs]
