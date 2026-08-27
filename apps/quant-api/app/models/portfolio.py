from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.market_data import Stock
    from app.models.user import User


class Portfolio(Base):
    __tablename__ = "portfolios"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_portfolio_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="IDR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="portfolios")  # type: ignore[name-defined]
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="portfolio", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    fee: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0.0)
    transacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    portfolio: Mapped[Portfolio] = relationship(back_populates="transactions")
    stock: Mapped[Stock] = relationship()
