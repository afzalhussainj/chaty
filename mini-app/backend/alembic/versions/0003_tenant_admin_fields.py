"""Tenant branding/prompts and crawl config crawl options.

Revision ID: 0003_tenant_admin_fields
Revises: 0002_core_domain
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB

revision: str = "0003_tenant_admin_fields"
down_revision: str | None = "0002_core_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("base_url", sa.Text(), nullable=True))
    op.add_column(
        "tenants",
        sa.Column("allowed_domains", PGJSONB(), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("branding", PGJSONB(), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("prompt_settings", PGJSONB(), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("crawl_settings", PGJSONB(), nullable=True),
    )
    op.add_column("tenants", sa.Column("default_crawl_config_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tenants_default_crawl_config_id",
        "tenants",
        "crawl_configs",
        ["default_crawl_config_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_tenants_default_crawl_config_id"),
        "tenants",
        ["default_crawl_config_id"],
        unique=False,
    )

    op.add_column("crawl_configs", sa.Column("max_pages", sa.Integer(), nullable=True))
    op.add_column(
        "crawl_configs",
        sa.Column(
            "allow_pdf_crawling",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
    )
    op.add_column(
        "crawl_configs",
        sa.Column(
            "allow_js_rendering",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column(
        "crawl_configs",
        sa.Column(
            "crawl_frequency",
            sa.String(length=32),
            server_default="manual",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("crawl_configs", "crawl_frequency")
    op.drop_column("crawl_configs", "allow_js_rendering")
    op.drop_column("crawl_configs", "allow_pdf_crawling")
    op.drop_column("crawl_configs", "max_pages")

    op.drop_constraint("fk_tenants_default_crawl_config_id", "tenants", type_="foreignkey")
    op.drop_index(op.f("ix_tenants_default_crawl_config_id"), table_name="tenants")
    op.drop_column("tenants", "default_crawl_config_id")
    op.drop_column("tenants", "crawl_settings")
    op.drop_column("tenants", "prompt_settings")
    op.drop_column("tenants", "branding")
    op.drop_column("tenants", "allowed_domains")
    op.drop_column("tenants", "base_url")
