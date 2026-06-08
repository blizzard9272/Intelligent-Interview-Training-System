"""add document kind metadata

Revision ID: 20260608_0003
Revises: 20260606_0002
Create Date: 2026-06-08 15:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260608_0003"
down_revision = "20260606_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("document_kind", sa.String(length=40), nullable=False, server_default="general"),
    )


def downgrade() -> None:
    op.drop_column("documents", "document_kind")
