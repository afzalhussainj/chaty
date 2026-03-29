"""Admin incremental crawl / sync request bodies."""

from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel, Field


class CrawlConfigRef(BaseModel):
    """Identify which crawl policy applies."""

    crawl_config_id: int = Field(ge=1, description="Tenant crawl configuration to run under.")


class RefreshUrlRequest(CrawlConfigRef):
    """Re-crawl a single HTML page or PDF by absolute URL (hash-gated extract/index downstream)."""

    url: AnyHttpUrl


class AddSourceRequest(CrawlConfigRef):
    """Register and fetch one new URL without re-crawling the rest of the site."""

    url: AnyHttpUrl


class SyncChangedRequest(CrawlConfigRef):
    """Re-validate active sources under this config; index only when content changed."""

    pass


class FullRecrawlRequest(CrawlConfigRef):
    """Full site crawl from the config base URL (explicit operator intent)."""

    use_sitemap: bool = False
