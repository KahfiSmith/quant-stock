"""create market data tables (stocks, prices hypertable)

Revision ID: 0002_market_data
Revises: 0001_authentication
Create Date: 2026-08-25

The `prices` table is a TimescaleDB hypertable on PostgreSQL. On non-Postgres
dialects (e.g. SQLite in tests) it is created as a plain table so the schema
can be exercised without the TimescaleDB extension.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_market_data"
down_revision: str | None = "0001_authentication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name.startswith("postgres")


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=128), nullable=True),
        sa.Column("market_cap", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="IDR"),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"])

    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("high", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("low", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("volume", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("interval", sa.String(length=8), nullable=False, server_default="1d"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="sample"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_id", "time", "interval", "source", name="uq_prices_ingest"
        ),
    )
    op.create_index("ix_prices_stock_id", "prices", ["stock_id"])

    if _is_postgres():
        op.execute("SELECT create_hypertable('prices', by_range('time'))")


def downgrade() -> None:
    op.drop_index("ix_prices_stock_id", table_name="prices")
    op.drop_table("prices")
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.drop_table("stocks")