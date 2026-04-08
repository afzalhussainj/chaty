"""Unauthenticated public endpoints (tenant branding + chat by slug)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import SessionDep, SettingsDep
from app.core.rate_limit import public_limiter
from app.core.settings import get_settings
from app.models.enums import TenantStatus
from app.repositories.tenant import TenantRepository
from app.schemas.chat_query import ChatQueryRequest, ChatQueryResponse
from app.schemas.public_tenant import PublicTenantBranding, PublicTenantResponse
from app.services.chat_query_service import execute_chat_query

router = APIRouter(prefix="/public", tags=["public"])

_PUBLIC_CHAT_RATE = get_settings().public_chat_rate_limit


def _branding_from_tenant(raw: dict | None) -> PublicTenantBranding | None:
    if not raw or not isinstance(raw, dict):
        return None
    logo = raw.get("logo_url")
    pc = raw.get("primary_color")
    at = raw.get("app_title")
    return PublicTenantBranding(
        logo_url=str(logo) if logo else None,
        primary_color=pc if isinstance(pc, str) else None,
        app_title=at if isinstance(at, str) else None,
    )


@router.get("/tenants/{slug}", response_model=PublicTenantResponse)
def get_public_tenant_by_slug(slug: str, session: SessionDep) -> PublicTenantResponse:
    repo = TenantRepository(session)
    tenant = repo.get_by_slug(slug)
    if tenant is None or tenant.status != TenantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return PublicTenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        branding=_branding_from_tenant(tenant.branding),
    )


@router.post(
    "/tenants/{slug}/chat/query",
    response_model=ChatQueryResponse,
)
@public_limiter.limit(_PUBLIC_CHAT_RATE)
def post_public_chat_query(
    request: Request,
    slug: str,
    body: ChatQueryRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> ChatQueryResponse:
    if not settings.public_chat_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public chat is disabled",
        )
    repo = TenantRepository(session)
    tenant = repo.get_by_slug(slug)
    if tenant is None or tenant.status != TenantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return execute_chat_query(session, tenant.id, body)


@router.get("/site", response_model=PublicTenantResponse)
def get_single_site_info(session: SessionDep, settings: SettingsDep) -> PublicTenantResponse:
    """Return branding/name for the configured single-site app."""
    repo = TenantRepository(session)
    tenant = repo.get_by_slug(settings.site_slug)
    if tenant is None or tenant.status != TenantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not initialized",
        )
    return PublicTenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        branding=_branding_from_tenant(tenant.branding),
    )


@router.post("/chat/query", response_model=ChatQueryResponse)
@public_limiter.limit(_PUBLIC_CHAT_RATE)
def post_single_site_chat_query(
    request: Request,
    body: ChatQueryRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> ChatQueryResponse:
    """Single-site chat endpoint (no tenant slug in URL)."""
    if not settings.public_chat_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public chat is disabled",
        )
    repo = TenantRepository(session)
    tenant = repo.get_by_slug(settings.site_slug)
    if tenant is None or tenant.status != TenantStatus.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not initialized",
        )
    return execute_chat_query(session, tenant.id, body)
