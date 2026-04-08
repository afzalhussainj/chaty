#!/usr/bin/env python3
"""
Create an idempotent demo tenant (slug `demo`) with a crawl config.

Run from the backend directory after migrations:

    cd backend
    set DATABASE_URL=...   # or export on Unix
    python scripts/seed_demo_tenant.py

Or inside the API container:

    docker compose exec backend python scripts/seed_demo_tenant.py
"""

from __future__ import annotations

import os
import sys

# Project root: backend/
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "development")

from app.db.session import SessionLocal, get_engine  # noqa: E402
from app.models.crawl_config import CrawlConfig  # noqa: E402
from app.models.enums import CrawlFrequency, TenantStatus  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.repositories.crawl_config import CrawlConfigRepository  # noqa: E402
from app.repositories.tenant import TenantRepository  # noqa: E402

DEMO_SLUG = "demo"
DEMO_NAME = "Demo University"


def main() -> None:
    session = SessionLocal(bind=get_engine())
    try:
        trepo = TenantRepository(session)
        existing = trepo.get_by_slug(DEMO_SLUG)
        if existing:
            print(f"Demo tenant already exists (id={existing.id}, slug={DEMO_SLUG}).")
            return

        tenant = Tenant(
            name=DEMO_NAME,
            slug=DEMO_SLUG,
            status=TenantStatus.active,
            base_url="https://example.edu/",
            allowed_domains=["example.edu"],
            branding={
                "app_title": "Demo assistant",
                "primary_color": "#2563eb",
                "logo_url": None,
            },
        )
        trepo.add(tenant)
        session.flush()

        cfg = CrawlConfig(
            tenant_id=tenant.id,
            name="Main site",
            base_url="https://example.edu/",
            allowed_hosts=["example.edu"],
            respect_robots_txt=True,
            crawl_frequency=CrawlFrequency.manual,
        )
        CrawlConfigRepository(session).add(cfg)
        tenant.default_crawl_config_id = cfg.id
        session.commit()
        print(
            f"Created demo tenant id={tenant.id} slug={DEMO_SLUG} "
            f"crawl_config_id={cfg.id}. Public chat: /chat/{DEMO_SLUG}",
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
