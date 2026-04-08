"""Tenant business logic."""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.rbac import can_manage_tenants, can_read_tenant, can_write_tenant
from app.core.exceptions import ConflictError, NotFoundError
from app.models.admin import AdminUser
from app.models.enums import AuditAction
from app.models.tenant import Tenant
from app.repositories.tenant import TenantRepository
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.audit_service import write_audit


def list_tenants(session: Session, actor: AdminUser) -> list[Tenant]:
    repo = TenantRepository(session)
    if can_manage_tenants(actor):
        return repo.list_all()
    if actor.tenant_id is None:
        return []
    t = repo.get(actor.tenant_id)
    return [t] if t else []


def get_tenant(session: Session, tenant_id: int, actor: AdminUser) -> Tenant:
    repo = TenantRepository(session)
    tenant = repo.get(tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found")
    if not can_read_tenant(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return tenant


def create_tenant(
    session: Session,
    data: TenantCreate,
    actor: AdminUser,
    request: Request,
) -> Tenant:
    if not can_manage_tenants(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = TenantRepository(session)
    if repo.get_by_slug(data.slug):
        raise ConflictError("Slug already in use", code="slug_taken")

    tenant = Tenant(
        name=data.name,
        slug=data.slug,
        status=data.status,
        base_url=str(data.base_url) if data.base_url else None,
        allowed_domains=data.allowed_domains or None,
        branding=data.branding.model_dump(mode="json") if data.branding else None,
        prompt_settings=(
            data.prompt_settings.model_dump(mode="json") if data.prompt_settings else None
        ),
        crawl_settings=data.crawl_settings,
        default_crawl_config_id=data.default_crawl_config_id,
        settings=data.settings,
    )
    repo.add(tenant)
    session.flush()
    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant.id,
        action=AuditAction.create,
        resource_type="Tenant",
        resource_id=str(tenant.id),
        details={"slug": tenant.slug},
        request=request,
    )
    return tenant


def update_tenant(
    session: Session,
    tenant_id: int,
    data: TenantUpdate,
    actor: AdminUser,
    request: Request,
) -> Tenant:
    if not can_write_tenant(actor, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = TenantRepository(session)
    tenant = repo.get(tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found")

    changed: dict = {}
    if data.name is not None:
        tenant.name = data.name
        changed["name"] = data.name
    if data.status is not None:
        tenant.status = data.status
        changed["status"] = data.status.value
    if "base_url" in data.model_fields_set:
        tenant.base_url = str(data.base_url) if data.base_url else None
        changed["base_url"] = tenant.base_url
    if data.allowed_domains is not None:
        tenant.allowed_domains = data.allowed_domains
        changed["allowed_domains"] = data.allowed_domains
    if data.branding is not None:
        tenant.branding = data.branding.model_dump(mode="json")
        changed["branding"] = tenant.branding
    if data.prompt_settings is not None:
        tenant.prompt_settings = data.prompt_settings.model_dump(mode="json")
        changed["prompt_settings"] = tenant.prompt_settings
    if data.crawl_settings is not None:
        tenant.crawl_settings = data.crawl_settings
        changed["crawl_settings"] = data.crawl_settings
    if "default_crawl_config_id" in data.model_fields_set:
        tenant.default_crawl_config_id = data.default_crawl_config_id
        changed["default_crawl_config_id"] = data.default_crawl_config_id
    if data.settings is not None:
        tenant.settings = data.settings
        changed["settings"] = data.settings

    session.flush()
    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant.id,
        action=AuditAction.update,
        resource_type="Tenant",
        resource_id=str(tenant.id),
        details=changed or None,
        request=request,
    )
    return tenant


def delete_tenant(
    session: Session,
    tenant_id: int,
    actor: AdminUser,
    request: Request,
) -> None:
    if not can_manage_tenants(actor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    repo = TenantRepository(session)
    tenant = repo.get(tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found")
    tenant.default_crawl_config_id = None
    session.flush()
    write_audit(
        session,
        admin_user_id=actor.id,
        tenant_id=tenant_id,
        action=AuditAction.delete,
        resource_type="Tenant",
        resource_id=str(tenant_id),
        details=None,
        request=request,
    )
    repo.delete(tenant)
