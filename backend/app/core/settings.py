"""Application settings loaded from environment (Pydantic Settings v2)."""

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration; use get_settings() for a cached instance."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "university-chatbot-api"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = False

    # Database (PostgreSQL; use postgresql+psycopg driver URL)
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/chaty",
    )
    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=1, le=300)
    database_echo: bool = False

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")

    # Auth — set JWT_SECRET_KEY to a long random value in production
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Optional one-time bootstrap (development only; leave unset in production)
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    """Model for grounded chat (OpenAI Responses API)."""

    chat_retrieval_top_k: int = Field(default=8, ge=1, le=32)
    chat_openai_timeout_s: float = Field(default=120.0, ge=10.0, le=600.0)

    # Hybrid retrieval (vector + FTS merge)
    retrieval_default_top_k: int = Field(default=8, ge=1, le=100)
    retrieval_vector_candidate_multiplier: int = Field(default=3, ge=1, le=20)
    retrieval_fts_candidate_multiplier: int = Field(default=3, ge=1, le=20)
    retrieval_weight_vector: float = Field(default=0.62, ge=0.0, le=1.0)
    retrieval_weight_fts: float = Field(default=0.38, ge=0.0, le=1.0)
    retrieval_max_query_chars: int = Field(default=8000, ge=100, le=32000)

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    public_chat_enabled: bool = True
    """Allow unauthenticated POST /public/tenants/{slug}/chat/query (disable in lockdown)."""

    public_chat_rate_limit: str = "30/minute"
    """slowapi limit string for public chat POST (per client IP)."""

    crawl_http_timeout_s: float = Field(default=45.0, ge=5.0, le=300.0)
    crawl_http_max_retries: int = Field(default=3, ge=0, le=10)
    crawl_http_retry_backoff_s: float = Field(default=0.5, ge=0.0, le=30.0)

    extraction_http_timeout_s: float = Field(default=120.0, ge=10.0, le=600.0)
    extraction_http_max_retries: int = Field(default=2, ge=0, le=8)

    health_check_celery_workers: bool = False
    """If True, readiness calls Celery inspect (adds latency; requires workers reachable)."""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: Any) -> Any:
        if value is None:
            return ["http://localhost:3000"]
        if isinstance(value, str):
            parts = [item.strip() for item in value.split(",") if item.strip()]
            return parts if parts else ["http://localhost:3000"]
        return value

    @model_validator(mode="after")
    def production_safety(self) -> "Settings":
        if self.app_env == "production":
            if self.jwt_secret_key.strip() in ("", "change-me"):
                msg = "JWT_SECRET_KEY must be set to a strong secret when APP_ENV=production"
                raise ValueError(msg)
            if self.debug:
                msg = "DEBUG must be false when APP_ENV=production"
                raise ValueError(msg)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings (call get_settings.cache_clear() in tests when env changes)."""
    return Settings()
