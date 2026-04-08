#!/usr/bin/env python3
"""Single-site operational CLI (crawl/update/index without admin UI)."""

from __future__ import annotations

import argparse

from app.core.settings import get_settings
from app.db.session import SessionLocal, get_engine
from app.indexing.embeddings import OpenAIEmbeddingGenerator
from app.indexing.indexing_service import index_source_latest
from app.models.enums import CrawlJobType, JobStatus, SourceType
from app.models.job import CrawlJob
from app.models.source import Source
from app.repositories.crawl_config import CrawlConfigRepository
from app.repositories.tenant import TenantRepository
from app.services.crawl_execution_service import run_job_to_completion
from app.services.html_extraction_service import extract_html_source
from app.services.pdf_extraction_service import extract_pdf_source


def _resolve_site(session):
    settings = get_settings()
    tenant = TenantRepository(session).get_by_slug(settings.site_slug)
    if tenant is None:
        raise RuntimeError(
            f"Site slug '{settings.site_slug}' not found. "
            "Start API once to bootstrap.",
        )
    if tenant.default_crawl_config_id is None:
        raise RuntimeError("Site has no default crawl config.")
    cfg = CrawlConfigRepository(session).get(tenant.default_crawl_config_id, tenant.id)
    if cfg is None:
        raise RuntimeError("Default crawl config not found.")
    return tenant, cfg


def _run_job(
    session,
    tenant_id: int,
    crawl_config_id: int,
    job_type: CrawlJobType,
    *,
    seed_url: str | None,
    workflow: str,
):
    stats: dict[str, object] = {"workflow": workflow, "dry_run": False, "use_sitemap": False}
    if seed_url:
        stats["seed_url"] = seed_url
    job = CrawlJob(
        tenant_id=tenant_id,
        crawl_config_id=crawl_config_id,
        job_type=job_type,
        status=JobStatus.queued,
        stats=stats,
        created_by_id=None,
    )
    session.add(job)
    session.flush()
    ok = run_job_to_completion(session, job.id)
    session.flush()
    if not ok:
        raise RuntimeError(f"Crawl job failed: {job.error_message}")
    return job


def _extract_and_index_touched_sources(session, tenant_id: int, job: CrawlJob) -> None:
    touched_raw = (job.stats or {}).get("touched_source_ids")
    ids: list[int] = []
    if isinstance(touched_raw, list):
        for x in touched_raw:
            try:
                ids.append(int(x))
            except (TypeError, ValueError):
                continue
    if not ids:
        return
    rows = session.query(Source).filter(Source.tenant_id == tenant_id, Source.id.in_(ids)).all()
    for src in rows:
        if src.source_type == SourceType.html_page:
            extract_html_source(session, src.id, tenant_id=tenant_id)
        elif src.source_type == SourceType.pdf:
            extract_pdf_source(session, src.id, tenant_id=tenant_id)
        index_source_latest(session, src.id, embedding_generator=OpenAIEmbeddingGenerator())


def _cmd_full_crawl() -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.full_recrawl,
            seed_url=None,
            workflow="full_recrawl",
        )
        _extract_and_index_touched_sources(session, tenant.id, job)
        session.commit()
        print(f"full_crawl_ok job_id={job.id}")
    finally:
        session.close()


def _cmd_refresh_page(url: str) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.incremental_url,
            seed_url=url,
            workflow="refresh_page",
        )
        _extract_and_index_touched_sources(session, tenant.id, job)
        session.commit()
        print(f"refresh_page_ok job_id={job.id}")
    finally:
        session.close()


def _cmd_refresh_pdf(url: str) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.incremental_pdf,
            seed_url=url,
            workflow="refresh_pdf",
        )
        _extract_and_index_touched_sources(session, tenant.id, job)
        session.commit()
        print(f"refresh_pdf_ok job_id={job.id}")
    finally:
        session.close()


def _cmd_add_source(url: str) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.add_source,
            seed_url=url,
            workflow="add_source",
        )
        _extract_and_index_touched_sources(session, tenant.id, job)
        session.commit()
        print(f"add_source_ok job_id={job.id}")
    finally:
        session.close()


def _cmd_sync_changed() -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.sync_changed,
            seed_url=None,
            workflow="sync_changed",
        )
        session.commit()
        print(f"sync_changed_ok job_id={job.id}")
    finally:
        session.close()


def _cmd_reindex_source(source_id: int) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        src = session.get(Source, source_id)
        if src is None:
            raise RuntimeError("source not found")
        index_source_latest(
            session,
            src.id,
            embedding_generator=OpenAIEmbeddingGenerator(),
            force=True,
        )
        session.commit()
        print(f"reindex_source_ok source_id={source_id}")
    finally:
        session.close()


def _cmd_rebuild_all() -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, _cfg = _resolve_site(session)
        rows = (
            session.query(Source)
            .filter(Source.tenant_id == tenant.id, Source.is_active.is_(True))
            .order_by(Source.id.asc())
            .all()
        )
        for src in rows:
            if src.source_type == SourceType.html_page:
                extract_html_source(session, src.id, tenant_id=tenant.id, force=True)
            elif src.source_type == SourceType.pdf:
                extract_pdf_source(session, src.id, tenant_id=tenant.id, force=True)
            index_source_latest(
                session,
                src.id,
                embedding_generator=OpenAIEmbeddingGenerator(),
                force=True,
            )
        session.commit()
        print(f"rebuild_all_ok sources={len(rows)}")
    finally:
        session.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Single-site crawl/index CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("full-crawl")
    rp = sub.add_parser("refresh-page")
    rp.add_argument("--url", required=True)
    rpdf = sub.add_parser("refresh-pdf")
    rpdf.add_argument("--url", required=True)
    add = sub.add_parser("add-source")
    add.add_argument("--url", required=True)
    sub.add_parser("sync-changed")
    ri = sub.add_parser("reindex-source")
    ri.add_argument("--source-id", type=int, required=True)
    sub.add_parser("rebuild-all")
    args = p.parse_args()

    if args.cmd == "full-crawl":
        _cmd_full_crawl()
    elif args.cmd == "refresh-page":
        _cmd_refresh_page(args.url)
    elif args.cmd == "refresh-pdf":
        _cmd_refresh_pdf(args.url)
    elif args.cmd == "add-source":
        _cmd_add_source(args.url)
    elif args.cmd == "sync-changed":
        _cmd_sync_changed()
    elif args.cmd == "reindex-source":
        _cmd_reindex_source(args.source_id)
    elif args.cmd == "rebuild-all":
        _cmd_rebuild_all()


if __name__ == "__main__":
    main()
