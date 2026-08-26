"""create fundamentals table

Revision ID: 0003_fundamentals
Revises: 0002_market_data
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_fundamentals"
down_revision: str | None = "0002_market_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fundamentals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_type", sa.String(length=16), nullable=False, server_default="TTM"),
        sa.Column("pe_ratio", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("pb_ratio", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("roe", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("roa", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("debt_to_equity", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("revenue_growth", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("eps_growth", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="sample"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stock_id", "period_end", "period_type", name="uq_fundamentals_period"),
    )
    op.create_index("ix_fundamentals_stock_id", "fundamentals", ["stock_id"])


def downgrade() -> None:
    op.drop_index("ix_fundamentals_stock_id", table_name="fundamentals")
    op.drop_table("fundamentals")
