"""add idx universe, pit fundamentals, market flows, corporate actions, and factor rotation tables

Revision ID: 0011_idx_platform_architecture
Revises: 0010_backtest_jobs
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_idx_platform_architecture"
down_revision: str | None = "0010_backtest_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add IDX Universe columns to stocks
    with op.batch_alter_table("stocks") as batch_op:
        batch_op.add_column(sa.Column("sub_sector", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("listing_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("liquidity_status", sa.String(length=32), nullable=False, server_default="liquid"))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        batch_op.add_column(sa.Column("board", sa.String(length=32), nullable=True, server_default="MAIN"))
        batch_op.add_column(sa.Column("avg_daily_turnover_20d", sa.Numeric(18, 2), nullable=True))
        batch_op.add_column(sa.Column("avg_daily_frequency_20d", sa.Numeric(12, 2), nullable=True))
        batch_op.create_index("ix_stocks_is_active", ["is_active"])

    # 2. Create financial_statements_pit table
    op.create_table(
        "financial_statements_pit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_quarter", sa.String(length=8), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False, index=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="IDR"),
        sa.Column("revenue", sa.Numeric(20, 2), nullable=True),
        sa.Column("gross_profit", sa.Numeric(20, 2), nullable=True),
        sa.Column("operating_profit", sa.Numeric(20, 2), nullable=True),
        sa.Column("net_income", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_assets", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_liabilities", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_equity", sa.Numeric(20, 2), nullable=True),
        sa.Column("operating_cash_flow", sa.Numeric(20, 2), nullable=True),
        sa.Column("free_cash_flow", sa.Numeric(20, 2), nullable=True),
        sa.Column("eps", sa.Numeric(12, 4), nullable=True),
        sa.Column("bvps", sa.Numeric(12, 4), nullable=True),
        sa.Column("roe", sa.Numeric(8, 4), nullable=True),
        sa.Column("roa", sa.Numeric(8, 4), nullable=True),
        sa.Column("debt_to_equity", sa.Numeric(8, 4), nullable=True),
        sa.Column("net_profit_margin", sa.Numeric(8, 4), nullable=True),
        sa.Column("dividend_per_share", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("is_audited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="idx_filing"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("stock_id", "fiscal_year", "fiscal_quarter", name="uq_stock_pit_period"),
    )

    # 3. Create market_flows_idx table
    op.create_table(
        "market_flows_idx",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("foreign_buy_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("foreign_sell_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("net_foreign_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("foreign_buy_volume", sa.Numeric(18, 0), nullable=False, server_default="0"),
        sa.Column("foreign_sell_volume", sa.Numeric(18, 0), nullable=False, server_default="0"),
        sa.Column("top3_buyer_broker_val", sa.Numeric(18, 2), nullable=True),
        sa.Column("top3_seller_broker_val", sa.Numeric(18, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("stock_id", "date", name="uq_stock_date_flow"),
    )

    # 4. Create corporate_actions_idx table
    op.create_table(
        "corporate_actions_idx",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("stock_id", sa.Integer(), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("cum_date", sa.Date(), nullable=True),
        sa.Column("ex_date", sa.Date(), nullable=False, index=True),
        sa.Column("recording_date", sa.Date(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("ratio_from", sa.Numeric(12, 4), nullable=True),
        sa.Column("ratio_to", sa.Numeric(12, 4), nullable=True),
        sa.Column("cash_amount", sa.Numeric(12, 4), nullable=True),
        sa.Column("exercise_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 5. Create benchmark_prices table
    op.create_table(
        "benchmark_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=16), nullable=False, server_default="^JKSE", index=True),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("open", sa.Numeric(18, 4), nullable=False),
        sa.Column("high", sa.Numeric(18, 4), nullable=False),
        sa.Column("low", sa.Numeric(18, 4), nullable=False),
        sa.Column("close", sa.Numeric(18, 4), nullable=False),
        sa.Column("volume", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("symbol", "time", name="uq_benchmark_time"),
    )

    # 6. Create strategy_definitions table
    op.create_table(
        "strategy_definitions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("strategy_type", sa.String(length=32), nullable=False, server_default="factor_rotation"),
        sa.Column("factor_weights", sa.JSON(), nullable=False),
        sa.Column("selection_rules", sa.JSON(), nullable=False),
        sa.Column("rebalance_frequency", sa.String(length=16), nullable=False, server_default="monthly"),
        sa.Column("performance_summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 7. Create idx_factor_rotation_backtests table
    op.create_table(
        "idx_factor_rotation_backtests",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("strategy_name", sa.String(length=128), nullable=False),
        sa.Column("universe", sa.JSON(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("initial_capital", sa.Float(), nullable=False),
        sa.Column("final_equity", sa.Float(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("equity_curve", sa.JSON(), nullable=False),
        sa.Column("rebalance_history", sa.JSON(), nullable=False),
        sa.Column("trade_logs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("idx_factor_rotation_backtests")
    op.drop_table("strategy_definitions")
    op.drop_table("benchmark_prices")
    op.drop_table("corporate_actions_idx")
    op.drop_table("market_flows_idx")
    op.drop_table("financial_statements_pit")
    with op.batch_alter_table("stocks") as batch_op:
        batch_op.drop_index("ix_stocks_is_active")
        batch_op.drop_column("avg_daily_frequency_20d")
        batch_op.drop_column("avg_daily_turnover_20d")
        batch_op.drop_column("board")
        batch_op.drop_column("is_active")
        batch_op.drop_column("liquidity_status")
        batch_op.drop_column("listing_date")
        batch_op.drop_column("sub_sector")
