"""Source soft lifecycle: active flag + deactivation timestamp.

Revision ID: 0006_source_active_incremental
Revises: 0005_indexing_chunk_metadata
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_source_active_incremental"
down_revision: str | None = "0005_indexing_chunk_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column(
        "sources",
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_sources_is_active"), "sources", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sources_is_active"), table_name="sources")
    op.drop_column("sources", "deactivated_at")
    op.drop_column("sources", "is_active")
