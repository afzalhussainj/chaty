"""Admin authentication (JWT bearer)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import SessionDep, SettingsDep
from app.auth.deps import CurrentAdminDep
from app.models.enums import AuditAction
from app.schemas.auth import AdminMeResponse, LoginRequest, TokenResponse
from app.services.audit_service import write_audit
from app.services.auth_service import authenticate

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    session: SessionDep,
    settings: SettingsDep,
    request: Request,
) -> TokenResponse:
    result = authenticate(session, body.email, body.password, settings)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token, expires_in, user = result
    write_audit(
        session,
        admin_user_id=user.id,
        tenant_id=user.tenant_id,
        action=AuditAction.login,
        resource_type="AdminUser",
        resource_id=str(user.id),
        details=None,
        request=request,
    )
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=AdminMeResponse)
def me(user: CurrentAdminDep) -> AdminMeResponse:
    return AdminMeResponse.model_validate(user)
