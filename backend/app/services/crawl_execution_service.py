"""Execute `CrawlJob` rows using `CrawlEngine` (invoked from API or Celery)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.crawler.engine import CrawlEngine, CrawlRunResult
from app.crawler.fetch import HttpxFetcher
from app.crawler.rules import CrawlRules
from app.crawler.sink import DryRunSink
from app.crawler.types import CrawlMode, CrawlStats
from app.models.crawl_config import CrawlConfig
from app.models.enums import CrawlJobType, JobStatus
from app.models.job import CrawlJob
from app.models.tenant import Tenant
from app.repositories.crawl_job import CrawlJobRepository
from app.services.crawl_db_sink import DatabaseCrawlSink


def crawl_stats_to_dict(s: CrawlStats) -> dict[str, object]:
    return {
        "pages_fetched": s.pages_fetched,
        "pdfs_registered": s.pdfs_registered,
        "html_sources_upserted": s.html_sources_upserted,
        "html_discovered_registered": s.html_discovered_registered,
        "skipped_robots": s.skipped_robots,
        "skipped_not_allowed": s.skipped_not_allowed,
        "skipped_depth": s.skipped_depth,
        "skipped_max_pages": s.skipped_max_pages,
        "fetch_errors": s.fetch_errors,
        "sitemap_seeds": s.sitemap_seeds,
        "touched_source_ids": list(s.touched_source_ids),
        **s.extras,
    }


def _mode_for_job(job_type: CrawlJobType) -> CrawlMode:
    if job_type in (CrawlJobType.full_crawl, CrawlJobType.full_recrawl):
        return CrawlMode.full
    if job_type == CrawlJobType.incremental_url:
        return CrawlMode.single_page
    # Default: single-URL style (add_source / incremental_pdf) — fetch one resource.
    return CrawlMode.single_page


def _seed_urls(job: CrawlJob, config: CrawlConfig) -> list[str]:
    stats = job.stats or {}
    if job.job_type in (
        CrawlJobType.incremental_url,
        CrawlJobType.incremental_pdf,
        CrawlJobType.add_source,
    ):
        seed = stats.get("seed_url")
        if not seed or not isinstance(seed, str):
            msg = f"{job.job_type.value} job requires stats.seed_url"
            raise ValueError(msg)
        return [seed]
    return [config.base_url]


def execute_crawl_job(session: Session, job_id: int) -> CrawlRunResult:
    repo = CrawlJobRepository(session)
    job = repo.get_by_id(job_id)
    if job is None:
        msg = "Crawl job not found"
        raise ValueError(msg)
    if job.job_type == CrawlJobType.sync_changed:
        from app.services.incremental_sync_service import execute_sync_changed_job

        return execute_sync_changed_job(session, job)

    if job.crawl_config_id is None:
        msg = "Crawl job has no crawl_config_id"
        raise ValueError(msg)

    cfg = session.get(CrawlConfig, job.crawl_config_id)
    if cfg is None or cfg.tenant_id != job.tenant_id:
        msg = "Crawl configuration not found for this job"
        raise ValueError(msg)

    tenant = session.get(Tenant, job.tenant_id)
    if tenant is None:
        msg = "Tenant not found"
        raise ValueError(msg)

    opts = job.stats or {}
    dry_run = bool(opts.get("dry_run", False))
    use_sitemap = bool(opts.get("use_sitemap", False))

    rules = CrawlRules.from_config(cfg, tenant)
    settings = get_settings()
    ua = cfg.user_agent or f"{settings.app_name}/crawler"

    fetcher = HttpxFetcher(user_agent=ua)
    mode = _mode_for_job(job.job_type)

    sink: DatabaseCrawlSink | DryRunSink
    if dry_run:
        sink = DryRunSink()
    else:
        sink = DatabaseCrawlSink(session, job.tenant_id, job.crawl_config_id)

    engine = CrawlEngine(
        rules,
        fetcher,
        mode=mode,
        max_depth=cfg.max_depth,
        max_pages=cfg.max_pages,
        allow_pdf_crawling=cfg.allow_pdf_crawling,
        respect_robots_txt=cfg.respect_robots_txt,
        user_agent=ua,
        use_sitemap=use_sitemap and mode == CrawlMode.full,
        dry_run=dry_run,
    )

    seeds = _seed_urls(job, cfg)
    return engine.run(seeds, sink)


def run_job_to_completion(session: Session, job_id: int) -> bool:
    """Load job, transition status, execute, persist stats (caller commits). Returns success."""
    repo = CrawlJobRepository(session)
    job = repo.get_by_id(job_id)
    if job is None:
        return False
    now = datetime.now(timezone.utc)
    if job.status not in (JobStatus.queued, JobStatus.retrying):
        return False

    prior_stats = dict(job.stats or {})
    job.status = JobStatus.running
    job.started_at = now
    job.error_message = None
    session.flush()

    try:
        result = execute_crawl_job(session, job_id)
    except Exception as exc:  # noqa: BLE001 — surface failure on job row
        job.status = JobStatus.failed
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = str(exc)[:10000]
        job.stats = {
            **prior_stats,
            "error_type": type(exc).__name__,
            "error": str(exc)[:2000],
        }
        return False

    job.status = JobStatus.succeeded
    job.completed_at = datetime.now(timezone.utc)
    job.stats = {
        **prior_stats,
        **crawl_stats_to_dict(result.stats),
        "dry_run_records_count": len(result.dry_run_records),
    }
    return True
