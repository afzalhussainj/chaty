"""Database-backed enumerations (stable string values for API compatibility)."""

from __future__ import annotations

import enum


class TenantStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"


class SourceType(str, enum.Enum):
    html_page = "html_page"
    pdf = "pdf"
    manual_text = "manual_text"


class SourceStatus(str, enum.Enum):
    pending = "pending"
    discovered = "discovered"
    fetching = "fetching"
    fetched = "fetched"
    extraction_failed = "extraction_failed"
    ready_to_index = "ready_to_index"
    indexing = "indexing"
    indexed = "indexed"
    failed = "failed"
    stale = "stale"


class CrawlJobType(str, enum.Enum):
    full_crawl = "full_crawl"
    incremental_url = "incremental_url"
    incremental_pdf = "incremental_pdf"
    add_source = "add_source"
    full_recrawl = "full_recrawl"
    sync_changed = "sync_changed"


class IndexJobType(str, enum.Enum):
    full_reindex = "full_reindex"
    incremental_document = "incremental_document"
    incremental_source = "incremental_source"
    tenant_reindex = "tenant_reindex"
    embed_backfill = "embed_backfill"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    retrying = "retrying"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class ChatRole(str, enum.Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class AdminRole(str, enum.Enum):
    """Platform vs tenant roles (see AdminUser model docstring for invariants)."""

    super_admin = "super_admin"
    tenant_admin = "tenant_admin"
    tenant_viewer = "tenant_viewer"


class CrawlFrequency(str, enum.Enum):
    """Scheduled crawl cadence (enforcement is via Celery beat in a later phase)."""

    manual = "manual"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    login = "login"
    logout = "logout"
    crawl_triggered = "crawl_triggered"
    index_triggered = "index_triggered"
    settings_changed = "settings_changed"
