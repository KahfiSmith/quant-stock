"""create portfolio and transaction tables

Revision ID: 0004_portfolios
Revises: 0003_fundamentals
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_portfolios"
down_revision: str | None = "0003_fundamentals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="IDR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_user_portfolio_name"),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=8), nullable=False),  # BUY or SELL
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("fee", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("transacted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_portfolio_id", "transactions", ["portfolio_id"])
    op.create_index("ix_transactions_stock_id", "transactions", ["stock_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_stock_id", table_name="transactions")
    op.drop_index("ix_transactions_portfolio_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_portfolios_user_id", table_name="portfolios")
    op.drop_table("portfolios")
