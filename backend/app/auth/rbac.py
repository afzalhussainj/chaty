"""Role-based access helpers for admin operations."""

from __future__ import annotations

from app.models.admin import AdminUser
from app.models.enums import AdminRole


def is_super_admin(user: AdminUser) -> bool:
    return user.role == AdminRole.super_admin


def can_manage_tenants(user: AdminUser) -> bool:
    """Create/delete tenants or list all tenants."""
    return user.role == AdminRole.super_admin


def can_write_tenant(user: AdminUser, tenant_id: int) -> bool:
    """Update tenant settings (own tenant or super admin)."""
    if user.role == AdminRole.super_admin:
        return True
    if user.role == AdminRole.tenant_admin and user.tenant_id == tenant_id:
        return True
    return False


def can_read_tenant(user: AdminUser, tenant_id: int) -> bool:
    if user.role == AdminRole.super_admin:
        return True
    return user.tenant_id == tenant_id


def can_write_crawl_config(user: AdminUser, tenant_id: int) -> bool:
    if user.role == AdminRole.super_admin:
        return True
    if user.role == AdminRole.tenant_admin and user.tenant_id == tenant_id:
        return True
    return False


def can_read_crawl_config(user: AdminUser, tenant_id: int) -> bool:
    return can_read_tenant(user, tenant_id)
