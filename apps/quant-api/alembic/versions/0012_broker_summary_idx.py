"""add broker_summary_idx table for idx.co.id broker activity data

Revision ID: 0012_broker_summary_idx
Revises: 0011_idx_platform_architecture
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_broker_summary_idx"
down_revision: str | None = "0011_idx_platform_architecture"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "broker_summary_idx",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("broker_code", sa.String(8), nullable=False, index=True),
        sa.Column("broker_name", sa.String(128), nullable=False),
        sa.Column("date", sa.Date, nullable=False, index=True),
        sa.Column("total_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("volume", sa.Numeric(18, 0), nullable=False, server_default="0"),
        sa.Column("frequency", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source", sa.String(32), nullable=False, server_default="idx_web"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("broker_code", "date", name="uq_broker_date_summary"),
    )


def downgrade() -> None:
    op.drop_table("broker_summary_idx")
