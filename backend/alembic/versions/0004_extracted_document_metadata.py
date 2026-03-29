"""Add metadata JSONB to extracted_documents.

Revision ID: 0004_extracted_document_metadata
Revises: 0003_tenant_admin_fields
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB

revision: str = "0004_extracted_document_metadata"
down_revision: str | None = "0003_tenant_admin_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "extracted_documents",
        sa.Column("metadata", PGJSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("extracted_documents", "metadata")
