#!/usr/bin/env python3
"""Single-site operational CLI (crawl/update/index without admin UI)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from app.core.settings import get_settings
from app.db.session import SessionLocal, get_engine
from app.indexing.embeddings import OpenAIEmbeddingGenerator
from app.indexing.indexing_service import index_source_latest
from app.models.enums import CrawlJobType, JobStatus, SourceStatus, SourceType
from app.models.job import CrawlJob
from app.models.source import Source
from app.repositories.crawl_config import CrawlConfigRepository
from app.repositories.extracted_document import ExtractedDocumentRepository
from app.repositories.tenant import TenantRepository
from app.services.crawl_execution_service import run_job_to_completion
from app.services.html_extraction_service import extract_html_source
from app.services.pdf_extraction_service import extract_pdf_source


def _cli_log(msg: str) -> None:
    """Stdout progress for long crawl/index runs (visible under `docker compose exec`)."""
    print(msg, flush=True)


def _log_crawl_config_snapshot(cfg) -> None:
    """Print effective crawl policy (common reason for zero pages: path_prefixes / allowlist)."""
    settings = get_settings()
    eff_ua = cfg.user_agent or settings.crawl_user_agent or f"{settings.app_name}/crawler"
    _cli_log(
        f"[site_cli] crawl_config id={cfg.id} base_url={cfg.base_url!r} "
        f"max_depth={cfg.max_depth} max_pages={cfg.max_pages} "
        f"allowed_hosts={cfg.allowed_hosts!r} path_prefixes={cfg.path_prefixes!r} "
        f"exclude_globs={cfg.exclude_globs!r} respect_robots_txt={cfg.respect_robots_txt} "
        f"allow_pdf_crawling={cfg.allow_pdf_crawling}",
    )
    _cli_log(
        f"[site_cli] crawl user_agent_effective={eff_ua[:200]!r}"
        + ("" if settings.crawl_user_agent else " (set CRAWL_USER_AGENT in .env if site blocks bots)"),
    )
    _cli_log(
        "[site_cli] crawl runtime "
        f"timeout_s={settings.crawl_http_timeout_s} "
        f"retries={settings.crawl_http_max_retries} "
        f"backoff_s={settings.crawl_http_retry_backoff_s} "
        f"max_concurrency={settings.crawl_max_concurrency} "
        f"max_response_bytes={settings.crawl_max_response_bytes}",
    )


def _log_crawl_stats_summary(job_id: int, st: dict[str, object] | None) -> None:
    if not st:
        _cli_log(f"[site_cli] crawl stats job_id={job_id} (empty stats)")
        return
    t = st.get("touched_source_ids")
    tlen = len(t) if isinstance(t, list) else 0
    _cli_log(
        f"[site_cli] crawl stats job_id={job_id} pages_fetched={st.get('pages_fetched', 0)} "
        f"html_upserted={st.get('html_sources_upserted', 0)} "
        f"html_discovered={st.get('html_discovered_registered', 0)} "
        f"pdfs_registered={st.get('pdfs_registered', 0)} "
        f"fetch_errors={st.get('fetch_errors', 0)} "
        f"skipped_not_allowed={st.get('skipped_not_allowed', 0)} "
        f"skipped_robots={st.get('skipped_robots', 0)} "
        f"skipped_depth={st.get('skipped_depth', 0)} "
        f"skipped_max_pages={st.get('skipped_max_pages', 0)} "
        f"sitemap_seeds={st.get('sitemap_seeds', 0)} "
        f"touched_source_ids={tlen}",
    )
    http_errs = st.get("http_status_errors")
    if isinstance(http_errs, list) and http_errs:
        _cli_log(f"[site_cli] http_status_errors (sample)={http_errs[:5]}")
    non_html = st.get("non_html_ok_responses")
    if isinstance(non_html, list) and non_html:
        _cli_log(f"[site_cli] non_html_ok_responses (sample)={non_html[:3]}")
    pf = int(st.get("pages_fetched", 0) or 0)
    fe = int(st.get("fetch_errors", 0) or 0)
    if tlen == 0 and pf == 0:
        _cli_log(
            "[site_cli] hint: 0 pages fetched — seed URL may be blocked by path_prefixes / host rules, "
            "transport timeouts (fetch_errors), or robots blocked every URL. Check crawl_config above.",
        )
    elif tlen == 0 and pf > 0 and fe > 0:
        _cli_log(
            "[site_cli] hint: fetch_errors with pages_fetched>0 means the HTTP status was treated as "
            "failure (see http_status_errors). 522 is often Cloudflare (origin timeout); retry later, "
            "raise CRAWL_HTTP_TIMEOUT_S / retries, try site root URL, or use a browser-like User-Agent.",
        )
    elif tlen == 0 and pf > 0 and fe == 0 and isinstance(non_html, list) and non_html:
        _cli_log(
            "[site_cli] hint: got 2xx but body was not HTML (see non_html_ok_responses). "
            "Site may require JS / different URL.",
        )
    elif tlen == 0 and pf > 0 and fe == 0:
        _cli_log(
            "[site_cli] hint: pages fetched but nothing upserted — check skipped_not_allowed / "
            "non-HTML body skips above.",
        )


def _print_failure_summary(failures: list[tuple[int, str, str]]) -> None:
    if not failures:
        _cli_log("[site_cli] failures: none")
        return
    _cli_log(f"[site_cli] failures: {len(failures)}")
    for sid, url, err in failures:
        _cli_log(f"  - source_id={sid} url={url[:400]}")
        _cli_log(f"    error={err[:600]}")


def _extract_one_source(
    session,
    tenant_id: int,
    src: Source,
    *,
    force: bool = False,
    emit_progress: bool = True,
) -> None:
    if emit_progress:
        url_disp = (src.url or "")[:400]
        _cli_log(f"[site_cli] extract source_id={src.id} type={src.source_type.value} url={url_disp}")
    if src.source_type == SourceType.html_page:
        extract_html_source(session, src.id, tenant_id=tenant_id, force=force)
    elif src.source_type == SourceType.pdf:
        extract_pdf_source(session, src.id, tenant_id=tenant_id, force=force)
    else:
        raise RuntimeError(f"unsupported source_type={src.source_type}")


def _index_one_source(
    session,
    src: Source,
    *,
    force: bool = False,
    emit_progress: bool = True,
) -> None:
    if emit_progress:
        url_disp = (src.url or "")[:400]
        _cli_log(f"[site_cli] index/embed source_id={src.id} type={src.source_type.value} url={url_disp}")
    index_source_latest(
        session,
        src.id,
        embedding_generator=OpenAIEmbeddingGenerator(),
        force=force,
    )


def _is_fully_indexed_for_skip(session, source_id: int) -> bool:
    """
    True when latest extraction is already indexed (no embedding churn).

    Skipping re-extract/re-index can miss site updates until a run without this flag.
    """
    doc = ExtractedDocumentRepository(session).latest_for_source(source_id)
    if doc is None or doc.extraction_hash is None:
        return False
    return doc.indexed_extraction_hash == doc.extraction_hash


def _mark_source_cli_failure(session, source_id: int, error: str) -> None:
    """Persist failure on `Source` after rollback (separate commit by caller)."""
    src = session.get(Source, source_id)
    if src is None:
        return
    extras = dict(src.extras or {})
    extras["cli_last_error"] = error[:4000]
    extras["cli_last_error_at"] = datetime.now(timezone.utc).isoformat()
    src.extras = extras
    src.status = SourceStatus.extraction_failed
    low = error.lower()
    if "http 404" in low or " 404 " in low or low.startswith("http 404"):
        src.is_active = False
        src.deactivated_at = datetime.now(timezone.utc)


def _extract_sources_resilient(
    session,
    tenant_id: int,
    sources: list[Source],
    *,
    force: bool,
) -> tuple[list[tuple[int, str, str]], set[int]]:
    """Extract only; commit per success. Returns (failures, successful_source_ids)."""
    failures: list[tuple[int, str, str]] = []
    successful_ids: set[int] = set()
    sources_sorted = sorted(sources, key=lambda s: int(s.id))
    _cli_log(f"[site_cli] extract batch sources={len(sources_sorted)} force={force}")
    for src in sources_sorted:
        try:
            _extract_one_source(session, tenant_id, src, force=force)
            session.commit()
            successful_ids.add(int(src.id))
        except Exception as exc:  # noqa: BLE001 — aggregate per-source failures
            session.rollback()
            err = str(exc)
            failures.append((int(src.id), str(src.url or ""), err))
            _cli_log(f"[site_cli] FAIL extract source_id={src.id} error={err[:800]}")
            try:
                _mark_source_cli_failure(session, int(src.id), err)
                session.commit()
            except Exception as mark_exc:  # noqa: BLE001
                session.rollback()
                _cli_log(f"[site_cli] WARN could not persist failure metadata: {mark_exc}")
    return failures, successful_ids


def _index_sources_resilient(
    session,
    sources: list[Source],
    *,
    force: bool,
    skip_already_indexed: bool,
) -> tuple[list[tuple[int, str, str]], int]:
    """Chunk + embed + persist vectors; commit per success."""
    failures: list[tuple[int, str, str]] = []
    skipped = 0
    sources_sorted = sorted(sources, key=lambda s: int(s.id))
    _cli_log(
        f"[site_cli] index/embed batch sources={len(sources_sorted)} "
        f"force={force} skip_already_indexed={skip_already_indexed}",
    )
    for src in sources_sorted:
        if skip_already_indexed and not force and _is_fully_indexed_for_skip(session, src.id):
            skipped += 1
            _cli_log(
                f"[site_cli] skip (already indexed) source_id={src.id} "
                f"type={src.source_type.value} url={(src.url or '')[:200]}",
            )
            continue
        try:
            _index_one_source(session, src, force=force)
            session.commit()
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            err = str(exc)
            failures.append((int(src.id), str(src.url or ""), err))
            _cli_log(f"[site_cli] FAIL index source_id={src.id} error={err[:800]}")
            try:
                _mark_source_cli_failure(session, int(src.id), err)
                session.commit()
            except Exception as mark_exc:  # noqa: BLE001
                session.rollback()
                _cli_log(f"[site_cli] WARN could not persist failure metadata: {mark_exc}")
    if skipped:
        _cli_log(f"[site_cli] batch skipped_already_indexed={skipped}")
    return failures, skipped


def _extract_and_index_sources_resilient(
    session,
    tenant_id: int,
    sources: list[Source],
    *,
    force: bool,
    skip_already_indexed: bool,
) -> tuple[list[tuple[int, str, str]], int]:
    """
    Extract + index each source; commit per success. Record failures and continue.

    Returns (failures, skipped_already_indexed_count).
    failures: list of (source_id, url, error_message).
    """
    failures: list[tuple[int, str, str]] = []
    skipped = 0
    sources_sorted = sorted(sources, key=lambda s: int(s.id))
    _cli_log(f"[site_cli] extract+index batch sources={len(sources_sorted)} force={force}")
    for src in sources_sorted:
        if skip_already_indexed and not force and _is_fully_indexed_for_skip(session, src.id):
            skipped += 1
            _cli_log(
                f"[site_cli] skip (already indexed) source_id={src.id} "
                f"type={src.source_type.value} url={(src.url or '')[:200]}",
            )
            continue
        try:
            url_disp = (src.url or "")[:400]
            _cli_log(f"[site_cli] begin source_id={src.id} type={src.source_type.value} url={url_disp}")
            _extract_one_source(session, tenant_id, src, force=force, emit_progress=False)
            _index_one_source(session, src, force=force, emit_progress=False)
            _cli_log(f"[site_cli] done  source_id={src.id} type={src.source_type.value}")
            session.commit()
        except Exception as exc:  # noqa: BLE001 — aggregate per-source failures
            session.rollback()
            err = str(exc)
            failures.append((int(src.id), str(src.url or ""), err))
            _cli_log(f"[site_cli] FAIL source_id={src.id} type={src.source_type.value} error={err[:800]}")
            try:
                _mark_source_cli_failure(session, int(src.id), err)
                session.commit()
            except Exception as mark_exc:  # noqa: BLE001
                session.rollback()
                _cli_log(f"[site_cli] WARN could not persist failure metadata: {mark_exc}")
    if skipped:
        _cli_log(f"[site_cli] batch skipped_already_indexed={skipped}")
    return failures, skipped


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


def _sources_for_touched_ids(session, tenant_id: int, touched_raw: object) -> list[Source]:
    ids: list[int] = []
    if isinstance(touched_raw, list):
        for x in touched_raw:
            try:
                ids.append(int(x))
            except (TypeError, ValueError):
                continue
    if not ids:
        return []
    return session.query(Source).filter(Source.tenant_id == tenant_id, Source.id.in_(ids)).all()


def _active_html_pdf_sources(session, tenant_id: int) -> list[Source]:
    return (
        session.query(Source)
        .filter(
            Source.tenant_id == tenant_id,
            Source.is_active.is_(True),
            Source.source_type.in_((SourceType.html_page, SourceType.pdf)),
        )
        .order_by(Source.id.asc())
        .all()
    )


def _parse_source_ids_csv(raw: str) -> list[int]:
    parts = [p.strip() for p in raw.split(",")]
    ids: list[int] = []
    for p in parts:
        if not p:
            continue
        ids.append(int(p))
    return ids


def _resolve_sources_for_cli(
    session,
    tenant_id: int,
    *,
    job_id: int | None,
    all_active: bool,
    source_ids_csv: str | None,
) -> list[Source]:
    modes = sum([job_id is not None, bool(all_active), source_ids_csv is not None])
    if modes != 1:
        raise RuntimeError("Specify exactly one of --job-id, --all-active, --source-ids")

    if job_id is not None:
        job = session.get(CrawlJob, job_id)
        if job is None or int(job.tenant_id) != int(tenant_id):
            raise RuntimeError(f"Invalid crawl job for this site: job_id={job_id}")
        return _sources_for_touched_ids(session, tenant_id, (job.stats or {}).get("touched_source_ids"))

    if all_active:
        return _active_html_pdf_sources(session, tenant_id)

    assert source_ids_csv is not None
    ids = _parse_source_ids_csv(source_ids_csv)
    if not ids:
        raise RuntimeError("--source-ids requires at least one numeric id")
    rows = (
        session.query(Source)
        .filter(Source.tenant_id == tenant_id, Source.id.in_(ids))
        .order_by(Source.id.asc())
        .all()
    )
    found = {int(r.id) for r in rows}
    missing = sorted(set(ids) - found)
    if missing:
        raise RuntimeError(f"Unknown source id(s) for this tenant: {missing}")
    return rows


def _cmd_crawl_only() -> None:
    """Run crawl only (persist job + discovered sources); no extract/index."""
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        _log_crawl_config_snapshot(cfg)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.full_recrawl,
            seed_url=None,
            workflow="full_recrawl",
        )
        crawl_stats = dict(job.stats or {})
        _log_crawl_stats_summary(int(job.id), crawl_stats)
        session.commit()
        _cli_log(f"[site_cli] crawl committed job_id={job.id}")
        print(
            f"crawl_only_ok job_id={job.id} "
            f"next: extract-sources --job-id {job.id} "
            f"then index-sources --job-id {job.id}",
        )
    finally:
        session.close()


def _cmd_extract_sources(*, job_id: int | None, all_active: bool, source_ids_csv: str | None, force: bool) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, _cfg = _resolve_site(session)
        rows = _resolve_sources_for_cli(
            session,
            tenant.id,
            job_id=job_id,
            all_active=all_active,
            source_ids_csv=source_ids_csv,
        )
        failures, ok_ids = _extract_sources_resilient(session, tenant.id, rows, force=force)
        _print_failure_summary(failures)
        print(
            f"extract_sources_ok sources={len(rows)} extracted_ok={len(ok_ids)} "
            f"failed={len(failures)} "
            f"next: index-sources with same scope (--job-id / --all-active / --source-ids)",
        )
    finally:
        session.close()


def _cmd_index_sources(
    *,
    job_id: int | None,
    all_active: bool,
    source_ids_csv: str | None,
    force: bool,
    skip_already_indexed: bool,
) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, _cfg = _resolve_site(session)
        rows = _resolve_sources_for_cli(
            session,
            tenant.id,
            job_id=job_id,
            all_active=all_active,
            source_ids_csv=source_ids_csv,
        )
        failures, skipped = _index_sources_resilient(
            session,
            rows,
            force=force,
            skip_already_indexed=skip_already_indexed,
        )
        _print_failure_summary(failures)
        print(
            f"index_sources_ok sources={len(rows)} failed={len(failures)} skipped_already_indexed={skipped}",
        )
    finally:
        session.close()


def _cmd_full_crawl(*, skip_already_indexed: bool) -> None:
    session = SessionLocal(bind=get_engine())
    try:
        tenant, cfg = _resolve_site(session)
        _log_crawl_config_snapshot(cfg)
        job = _run_job(
            session,
            tenant.id,
            cfg.id,
            CrawlJobType.full_recrawl,
            seed_url=None,
            workflow="full_recrawl",
        )
        crawl_stats = dict(job.stats or {})
        _log_crawl_stats_summary(int(job.id), crawl_stats)
        session.commit()
        _cli_log(f"[site_cli] crawl committed job_id={job.id}")
        touched_rows = _sources_for_touched_ids(
            session,
            tenant.id,
            crawl_stats.get("touched_source_ids"),
        )
        touched_ids = {int(s.id) for s in touched_rows}
        # Two-phase for touched rows: extract then chunk+embed (same commits per source).
        failures_e, extract_ok_ids = _extract_sources_resilient(
            session,
            tenant.id,
            touched_rows,
            force=False,
        )
        rows_to_index = [s for s in touched_rows if int(s.id) in extract_ok_ids]
        failures_i, _ = _index_sources_resilient(
            session,
            rows_to_index,
            force=False,
            skip_already_indexed=False,
        )
        failures = failures_e + failures_i
        skipped_rest = 0
        if skip_already_indexed:
            _cli_log("[site_cli] optional pass: skip-already-indexed for non-touched active sources")
            q = (
                session.query(Source)
                .filter(
                    Source.tenant_id == tenant.id,
                    Source.is_active.is_(True),
                    Source.source_type.in_((SourceType.html_page, SourceType.pdf)),
                )
                .order_by(Source.id.asc())
            )
            if touched_ids:
                q = q.filter(~Source.id.in_(touched_ids))
            rest = q.all()
            f2, skipped_rest = _extract_and_index_sources_resilient(
                session,
                tenant.id,
                rest,
                force=False,
                skip_already_indexed=True,
            )
            failures = failures + f2

        _print_failure_summary(failures)
        failed_touch_ids = {f[0] for f in failures if f[0] in touched_ids}
        ok_touch = len(touched_rows) - len(failed_touch_ids)
        print(
            f"full_crawl_ok job_id={job.id} touched={len(touched_rows)} touched_ok={ok_touch} "
            f"touched_failed={len(failed_touch_ids)} skipped_already_indexed_non_touched={skipped_rest} "
            f"total_failed={len(failures)}",
        )
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
        crawl_stats = dict(job.stats or {})
        session.commit()
        rows = _sources_for_touched_ids(
            session,
            tenant.id,
            crawl_stats.get("touched_source_ids"),
        )
        failures, skipped = _extract_and_index_sources_resilient(
            session,
            tenant.id,
            rows,
            force=False,
            skip_already_indexed=False,
        )
        _print_failure_summary(failures)
        print(f"refresh_page_ok job_id={job.id} failed={len(failures)} skipped={skipped}")
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
        crawl_stats = dict(job.stats or {})
        session.commit()
        rows = _sources_for_touched_ids(
            session,
            tenant.id,
            crawl_stats.get("touched_source_ids"),
        )
        failures, skipped = _extract_and_index_sources_resilient(
            session,
            tenant.id,
            rows,
            force=False,
            skip_already_indexed=False,
        )
        _print_failure_summary(failures)
        print(f"refresh_pdf_ok job_id={job.id} failed={len(failures)} skipped={skipped}")
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
        crawl_stats = dict(job.stats or {})
        session.commit()
        rows = _sources_for_touched_ids(
            session,
            tenant.id,
            crawl_stats.get("touched_source_ids"),
        )
        failures, skipped = _extract_and_index_sources_resilient(
            session,
            tenant.id,
            rows,
            force=False,
            skip_already_indexed=False,
        )
        _print_failure_summary(failures)
        print(f"add_source_ok job_id={job.id} failed={len(failures)} skipped={skipped}")
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
        try:
            index_source_latest(
                session,
                src.id,
                embedding_generator=OpenAIEmbeddingGenerator(),
                force=True,
            )
            session.commit()
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            _cli_log(f"[site_cli] FAIL reindex source_id={source_id} error={exc}")
            _mark_source_cli_failure(session, source_id, str(exc))
            session.commit()
            raise
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
        _cli_log(f"[site_cli] rebuild-all sources={len(rows)}")
        failures, skipped = _extract_and_index_sources_resilient(
            session,
            tenant.id,
            rows,
            force=True,
            skip_already_indexed=False,
        )
        _print_failure_summary(failures)
        print(f"rebuild_all_ok sources={len(rows)} failed={len(failures)} skipped={skipped}")
    finally:
        session.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Single-site crawl/index CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "crawl-only",
        help="Run full crawl only (persist sources); run extract-sources then index-sources next.",
    )
    fc = sub.add_parser("full-crawl")
    fc.add_argument(
        "--skip-already-indexed",
        action="store_true",
        help=(
            "After indexing all URLs touched by this crawl, run a second pass on other active "
            "HTML/PDF sources and skip extract+embed when already fully indexed "
            "(indexed_extraction_hash == extraction_hash). Touched URLs are never skipped."
        ),
    )
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

    es = sub.add_parser(
        "extract-sources",
        help="Extract HTML/PDF only for sources selected by job id, all active, or explicit ids.",
    )
    es_g = es.add_mutually_exclusive_group(required=True)
    es_g.add_argument("--job-id", type=int, default=None, help="Use touched_source_ids from this crawl_jobs row.")
    es_g.add_argument("--all-active", action="store_true", default=False, help="All active HTML/PDF sources for the site.")
    es_g.add_argument("--source-ids", type=str, default=None, metavar="IDS", help="Comma-separated source ids.")
    es.add_argument("--force", action="store_true", help="Re-run extraction even if unchanged.")

    idx = sub.add_parser(
        "index-sources",
        help="Chunk + embed + persist vectors for sources (requires extraction first).",
    )
    idx_g = idx.add_mutually_exclusive_group(required=True)
    idx_g.add_argument("--job-id", type=int, default=None)
    idx_g.add_argument("--all-active", action="store_true", default=False)
    idx_g.add_argument("--source-ids", type=str, default=None, metavar="IDS")
    idx.add_argument("--force", action="store_true", help="Rebuild chunks/embeddings from latest extraction.")
    idx.add_argument(
        "--skip-already-indexed",
        action="store_true",
        help="Skip sources where indexed_extraction_hash already matches extraction_hash.",
    )

    args = p.parse_args()

    if args.cmd == "crawl-only":
        _cmd_crawl_only()
    elif args.cmd == "full-crawl":
        _cmd_full_crawl(skip_already_indexed=bool(args.skip_already_indexed))
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
    elif args.cmd == "extract-sources":
        _cmd_extract_sources(
            job_id=args.job_id,
            all_active=bool(args.all_active),
            source_ids_csv=args.source_ids,
            force=bool(args.force),
        )
    elif args.cmd == "index-sources":
        _cmd_index_sources(
            job_id=args.job_id,
            all_active=bool(args.all_active),
            source_ids_csv=args.source_ids,
            force=bool(args.force),
            skip_already_indexed=bool(args.skip_already_indexed),
        )


if __name__ == "__main__":
    main()
