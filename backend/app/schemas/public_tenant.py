"""Public (unauthenticated) tenant metadata for web chat."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PublicTenantBranding(BaseModel):
    logo_url: str | None = None
    primary_color: str | None = Field(default=None, max_length=32)
    app_title: str | None = Field(default=None, max_length=255)


class PublicTenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    branding: PublicTenantBranding | None = None
