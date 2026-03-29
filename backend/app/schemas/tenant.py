"""Tenant API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.enums import TenantStatus


class BrandingInfo(BaseModel):
    """Optional UI branding for the tenant chat/admin surfaces."""

    logo_url: HttpUrl | None = None
    primary_color: str | None = Field(default=None, max_length=32)
    app_title: str | None = Field(default=None, max_length=255)


class PromptSettings(BaseModel):
    """LLM prompt overrides (structure may evolve)."""

    system_prompt: str | None = Field(default=None, max_length=32000)
    temperature: float | None = Field(default=None, ge=0, le=2)


class TenantBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(
        min_length=2,
        max_length=128,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    status: TenantStatus = TenantStatus.active
    base_url: HttpUrl | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    branding: BrandingInfo | None = None
    prompt_settings: PromptSettings | None = None
    crawl_settings: dict[str, Any] | None = None
    default_crawl_config_id: int | None = None
    settings: dict[str, Any] | None = None

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def strip_domains(cls, v: Any) -> Any:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip().lower() for x in v if str(x).strip()]
        return v


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: TenantStatus | None = None
    base_url: HttpUrl | None = None
    allowed_domains: list[str] | None = None
    branding: BrandingInfo | None = None
    prompt_settings: PromptSettings | None = None
    crawl_settings: dict[str, Any] | None = None
    default_crawl_config_id: int | None = None
    settings: dict[str, Any] | None = None


class TenantResponse(TenantBase):
    id: int

    model_config = {"from_attributes": True}
