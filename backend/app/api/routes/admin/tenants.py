"""Tenant administration."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from app.api.deps import SessionDep
from app.auth.deps import CurrentAdminDep, SuperAdminDep, TenantReaderDep
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["admin-tenants"])


@router.get("", response_model=list[TenantResponse])
def list_tenants(
    session: SessionDep,
    actor: TenantReaderDep,
) -> list[TenantResponse]:
    tenants = tenant_service.list_tenants(session, actor)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    body: TenantCreate,
    session: SessionDep,
    actor: SuperAdminDep,
    request: Request,
) -> TenantResponse:
    tenant = tenant_service.create_tenant(session, body, actor, request)
    return TenantResponse.model_validate(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: int,
    session: SessionDep,
    actor: TenantReaderDep,
) -> TenantResponse:
    tenant = tenant_service.get_tenant(session, tenant_id, actor)
    return TenantResponse.model_validate(tenant)


@router.patch("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    body: TenantUpdate,
    session: SessionDep,
    actor: CurrentAdminDep,
    request: Request,
) -> TenantResponse:
    tenant = tenant_service.update_tenant(session, tenant_id, body, actor, request)
    return TenantResponse.model_validate(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: int,
    session: SessionDep,
    actor: SuperAdminDep,
    request: Request,
) -> Response:
    tenant_service.delete_tenant(session, tenant_id, actor, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
