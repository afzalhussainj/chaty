"""Crawl job API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, Field, computed_field, model_validator

from app.models.enums import CrawlJobType, JobStatus


class CrawlJobCreate(BaseModel):
    crawl_config_id: int = Field(ge=1)
    job_type: CrawlJobType
    seed_url: AnyHttpUrl | None = None
    dry_run: bool = False
    """If true, no `Source` rows are written; stats include discovery counts only."""

    use_sitemap: bool = False
    """When `job_type` is full crawl, also load URLs from `/sitemap.xml` (best-effort)."""

    workflow: str | None = Field(
        default=None,
        description="Logical operation label stored in job.stats (audit / admin UI).",
    )

    @model_validator(mode="after")
    def validate_seed(self) -> CrawlJobCreate:
        needs_seed = self.job_type in (
            CrawlJobType.incremental_url,
            CrawlJobType.incremental_pdf,
            CrawlJobType.add_source,
        )
        if needs_seed and self.seed_url is None:
            msg = "seed_url is required for this job type"
            raise ValueError(msg)
        return self


class CrawlJobResponse(BaseModel):
    id: int
    tenant_id: int
    crawl_config_id: int | None
    job_type: CrawlJobType
    status: JobStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    stats: dict[str, Any] | None

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def workflow(self) -> str | None:
        """Human-readable operation label from `stats.workflow` (incremental APIs)."""
        if not self.stats:
            return None
        w = self.stats.get("workflow")
        return w if isinstance(w, str) else None
