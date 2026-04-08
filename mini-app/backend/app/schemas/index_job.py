"""Index job API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import IndexJobType, JobStatus


class IndexJobResponse(BaseModel):
    id: int
    tenant_id: int
    source_id: int | None
    extracted_document_id: int | None
    job_type: IndexJobType
    status: JobStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    stats: dict[str, Any] | None

    model_config = {"from_attributes": True}
