"""IDX specialized models: Point-in-Time Fundamentals, Market Flows, Corporate Actions, and Benchmark Prices."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.market_data import Stock
    from app.models.user import User


class FinancialStatementPIT(Base):
    """Point-in-Time Financial Statements ensuring strict zero look-ahead bias."""

    __tablename__ = "financial_statements_pit"
    __table_args__ = (
        UniqueConstraint("stock_id", "fiscal_year", "fiscal_quarter", name="uq_stock_pit_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[str] = mapped_column(String(8), nullable=False)  # 'Q1', 'Q2', 'Q3', 'FY'
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    filing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # Tanggal rilis ke publik BEI
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="IDR")

    revenue: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    gross_profit: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    operating_profit: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    net_income: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_assets: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_liabilities: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    total_equity: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    operating_cash_flow: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)
    free_cash_flow: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)

    eps: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    bvps: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    roe: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    roa: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    debt_to_equity: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    net_profit_margin: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    dividend_per_share: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0.0)

    is_audited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="idx_filing")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    stock: Mapped[Stock] = relationship(back_populates="financial_statements_pit")


class MarketFlowIDX(Base):
    """Daily foreign fund flow and institutional accumulation tracking for IDX stocks."""

    __tablename__ = "market_flows_idx"
    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stock_date_flow"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    foreign_buy_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    foreign_sell_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    net_foreign_value: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    foreign_buy_volume: Mapped[float] = mapped_column(Numeric(18, 0), nullable=False, default=0.0)
    foreign_sell_volume: Mapped[float] = mapped_column(Numeric(18, 0), nullable=False, default=0.0)
    top3_buyer_broker_val: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    top3_seller_broker_val: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    stock: Mapped[Stock] = relationship(back_populates="market_flows")


class CorporateActionIDX(Base):
    """Corporate actions: Dividends, Stock Splits, Right Issues for IDX stocks."""

    __tablename__ = "corporate_actions_idx"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)  # 'DIVIDEND', 'STOCK_SPLIT', 'RIGHT_ISSUE'
    cum_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ex_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    recording_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ratio_from: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    ratio_to: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    cash_amount: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    exercise_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    stock: Mapped[Stock] = relationship(back_populates="corporate_actions")


class BenchmarkPrice(Base):
    """IHSG (^JKSE) composite index price history for Alpha/Beta benchmarking."""

    __tablename__ = "benchmark_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "time", name="uq_benchmark_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False, default="^JKSE", index=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    open: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StrategyDefinition(Base):
    """Catalog of quantitative strategies & Factor Rotation presets."""

    __tablename__ = "strategy_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    strategy_type: Mapped[str] = mapped_column(String(32), nullable=False, default="factor_rotation")
    factor_weights: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    selection_rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    rebalance_frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="monthly")
    performance_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User | None] = relationship()


class IDXFactorRotationBacktest(Base):
    """Execution results for multi-asset IDX Factor Rotation simulations."""

    __tablename__ = "idx_factor_rotation_backtests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    universe: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)
    final_equity: Mapped[float] = mapped_column(Float, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    equity_curve: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    rebalance_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    trade_logs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship()
