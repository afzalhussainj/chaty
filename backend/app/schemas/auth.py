"""Auth request/response models."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import AdminRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminMeResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: AdminRole
    tenant_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}
