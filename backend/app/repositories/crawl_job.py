"""Crawl job persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import CrawlJob


class CrawlJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, job_id: int, tenant_id: int) -> CrawlJob | None:
        stmt = select(CrawlJob).where(CrawlJob.id == job_id, CrawlJob.tenant_id == tenant_id)
        return self._session.scalars(stmt).first()

    def get_by_id(self, job_id: int) -> CrawlJob | None:
        return self._session.get(CrawlJob, job_id)

    def add(self, job: CrawlJob) -> CrawlJob:
        self._session.add(job)
        self._session.flush()
        return job
