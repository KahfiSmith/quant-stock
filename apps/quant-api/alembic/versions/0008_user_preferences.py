"""add user profile preferences

Revision ID: 0008_user_preferences
Revises: 0007_price_provenance
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_user_preferences"
down_revision: str | None = "0007_price_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("theme_preference", sa.String(length=16), nullable=False, server_default="system"),
    )
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
    op.drop_column("users", "theme_preference")
