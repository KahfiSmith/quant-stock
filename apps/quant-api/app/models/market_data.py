from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.fundamental import Fundamental
    from app.models.idx_models import CorporateActionIDX, FinancialStatementPIT, MarketFlowIDX


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sub_sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    listing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    liquidity_status: Mapped[str] = mapped_column(String(32), nullable=False, default="liquid")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    board: Mapped[str | None] = mapped_column(String(32), nullable=True, default="MAIN")
    avg_daily_turnover_20d: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    avg_daily_frequency_20d: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True, default="IDX")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="IDR")
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True, default="Asia/Jakarta")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    prices: Mapped[list[Price]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
    fundamentals: Mapped[list[Fundamental]] = relationship(
        "Fundamental", back_populates="stock", cascade="all, delete-orphan"
    )
    financial_statements_pit: Mapped[list[FinancialStatementPIT]] = relationship(
        "FinancialStatementPIT", back_populates="stock", cascade="all, delete-orphan"
    )
    market_flows: Mapped[list[MarketFlowIDX]] = relationship(
        "MarketFlowIDX", back_populates="stock", cascade="all, delete-orphan"
    )
    corporate_actions: Mapped[list[CorporateActionIDX]] = relationship(
        "CorporateActionIDX", back_populates="stock", cascade="all, delete-orphan"
    )


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("stock_id", "time", "interval", "source", name="uq_prices_ingest"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False, default="1d")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="sample")
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    validation_state: Mapped[str] = mapped_column(String(16), nullable=False, default="valid")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    stock: Mapped[Stock] = relationship(back_populates="prices")