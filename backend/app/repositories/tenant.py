"""Tenant persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant


class TenantRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, tenant_id: int) -> Tenant | None:
        return self._session.get(Tenant, tenant_id)

    def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        return self._session.scalars(stmt).first()

    def list_all(self) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.id)
        return list(self._session.scalars(stmt).all())

    def list_for_tenant_id(self, tenant_id: int) -> list[Tenant]:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        return list(self._session.scalars(stmt).all())

    def add(self, tenant: Tenant) -> Tenant:
        self._session.add(tenant)
        self._session.flush()
        return tenant

    def delete(self, tenant: Tenant) -> None:
        self._session.delete(tenant)
