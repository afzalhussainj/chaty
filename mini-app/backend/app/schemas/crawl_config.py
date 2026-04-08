"""Crawl configuration API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from app.models.crawl_config import CrawlConfig
from app.models.enums import CrawlFrequency


class CrawlConfigBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    base_url: HttpUrl
    is_active: bool = True
    max_depth: int | None = Field(default=None, ge=0, le=100)
    max_pages: int | None = Field(default=None, ge=1, le=10_000_000)
    respect_robots_txt: bool = True
    user_agent: str | None = Field(default=None, max_length=512)
    allow_pdf_crawling: bool = True
    allow_js_rendering: bool = False
    crawl_frequency: CrawlFrequency = CrawlFrequency.manual
    allowed_hosts: list[str] = Field(default_factory=list)
    include_path_rules: list[str] = Field(
        default_factory=list,
        description="Path prefixes to stay under (stored as path_prefixes)",
    )
    exclude_path_rules: list[str] = Field(
        default_factory=list,
        description="Glob patterns to exclude (stored as exclude_globs)",
    )
    extras: dict[str, Any] | None = None


class CrawlConfigCreate(CrawlConfigBase):
    pass


class CrawlConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: HttpUrl | None = None
    is_active: bool | None = None
    max_depth: int | None = Field(default=None, ge=0, le=100)
    max_pages: int | None = Field(default=None, ge=1, le=10_000_000)
    respect_robots_txt: bool | None = None
    user_agent: str | None = Field(default=None, max_length=512)
    allow_pdf_crawling: bool | None = None
    allow_js_rendering: bool | None = None
    crawl_frequency: CrawlFrequency | None = None
    allowed_hosts: list[str] | None = None
    include_path_rules: list[str] | None = None
    exclude_path_rules: list[str] | None = None
    extras: dict[str, Any] | None = None


class CrawlConfigResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    base_url: HttpUrl
    is_active: bool
    max_depth: int | None
    max_pages: int | None
    respect_robots_txt: bool
    user_agent: str | None
    allow_pdf_crawling: bool
    allow_js_rendering: bool
    crawl_frequency: CrawlFrequency
    allowed_hosts: list[str]
    include_path_rules: list[str]
    exclude_path_rules: list[str]
    extras: dict[str, Any] | None

    @classmethod
    def from_model(cls, m: CrawlConfig) -> CrawlConfigResponse:
        return cls(
            id=m.id,
            tenant_id=m.tenant_id,
            name=m.name,
            base_url=HttpUrl(m.base_url),
            is_active=m.is_active,
            max_depth=m.max_depth,
            max_pages=m.max_pages,
            respect_robots_txt=m.respect_robots_txt,
            user_agent=m.user_agent,
            allow_pdf_crawling=m.allow_pdf_crawling,
            allow_js_rendering=m.allow_js_rendering,
            crawl_frequency=m.crawl_frequency,
            allowed_hosts=list(m.allowed_hosts or []),
            include_path_rules=list(m.path_prefixes or []),
            exclude_path_rules=list(m.exclude_globs or []),
            extras=m.extras,
        )
