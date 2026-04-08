"""FastAPI dependencies for admin authentication."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import SessionDep, SettingsDep
from app.auth.tokens import decode_token
from app.models.admin import AdminUser
from app.models.enums import AdminRole
from app.repositories.admin_user import AdminUserRepository

_bearer = HTTPBearer(auto_error=False)


def get_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
) -> str:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return creds.credentials


def get_current_admin(
    session: SessionDep,
    settings: SettingsDep,
    token: Annotated[str, Depends(get_token)],
) -> AdminUser:
    try:
        payload = decode_token(token, settings)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None

    repo = AdminUserRepository(session)
    user = repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


CurrentAdminDep = Annotated[AdminUser, Depends(get_current_admin)]


def require_roles(*roles: AdminRole):
    def _dep(user: AdminUser = Depends(get_current_admin)) -> AdminUser:  # noqa: B008
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _dep


SuperAdminDep = Annotated[AdminUser, Depends(require_roles(AdminRole.super_admin))]
TenantAdminDep = Annotated[
    AdminUser,
    Depends(require_roles(AdminRole.super_admin, AdminRole.tenant_admin)),
]
TenantReaderDep = Annotated[
    AdminUser,
    Depends(
        require_roles(
            AdminRole.super_admin,
            AdminRole.tenant_admin,
            AdminRole.tenant_viewer,
        )
    ),
]
