from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.market_data import Stock


class Fundamental(Base):
    __tablename__ = "fundamentals"
    __table_args__ = (
        UniqueConstraint("stock_id", "period_end", "period_type", name="uq_fundamentals_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_type: Mapped[str] = mapped_column(String(16), nullable=False, default="TTM")
    pe_ratio: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    pb_ratio: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    roe: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    roa: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    debt_to_equity: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    revenue_growth: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    eps_growth: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="sample")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    stock: Mapped[Stock] = relationship(back_populates="fundamentals")  # noqa: F821
