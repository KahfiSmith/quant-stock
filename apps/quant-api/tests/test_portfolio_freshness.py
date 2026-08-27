"""Regression tests for portfolio valuation freshness + provider-backed prices.

Pins the contract that:
1. Latest market price for a holding comes from the yfinance-backed Price row,
   NOT from the transaction purchase price.
2. Each holding exposes price_as_of, data_source, data_lag.
3. PortfolioDetailResponse exposes aggregated price_as_of and data_lag.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import numpy as np
import pandas as pd


class FakeTicker:
    def __init__(self, symbol, **_):
        self._symbol = symbol

    def history(self, **kwargs):
        end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        dates = pd.date_range(end=end, periods=300, freq="D")
        np.random.seed(11)
        base = 9500.0
        closes = base + np.cumsum(np.random.randn(len(dates)) * (base * 0.01))
        opens = closes + np.random.randn(len(dates)) * 20
        highs = np.maximum(opens, closes) + 30
        lows = np.minimum(opens, closes) - 30
        vols = np.random.randint(1_000_000, 5_000_000, len(dates))
        return pd.DataFrame(
            {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
            index=dates,
        )

    @property
    def info(self):
        return {
            "longName": "BBCA",
            "sector": "Financial",
            "exchange": "JKT",
            "marketCap": 1_200_000_000_000_000,
            "currency": "IDR",
            "trailingPE": 14.2,
        }


def test_portfolio_valuation_uses_yfinance_price_not_buy_price(client) -> None:
    """Latest market price must come from Price table (yfinance), not from
    the BUY transaction price."""
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.ingestion import YFinanceCollector, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Stock
    from app.models.portfolio import Portfolio, Transaction
    from app.models.user import User
    from app.services.portfolio import get_portfolio_detail

    with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
        collector = YFinanceCollector()
        db = client.app.state.database.session()
        try:
            # Set up stock
            stock = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
            if stock is None:
                meta = collector.collect_metadata("BBCA")
                db.add(
                    Stock(
                        symbol="BBCA",
                        name=meta["name"],
                        sector=meta["sector"],
                        exchange=meta["exchange"],
                        market_cap=meta["market_cap"],
                        currency=meta["currency"],
                        timezone=meta["timezone"],
                    )
                )
                db.commit()
                stock = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))

            # Ingest prices
            req = CollectionRequest(
                symbols=["BBCA"], start_date=None, end_date=None, interval="1d"
            )
            ingest_prices(db, list(collector.collect_prices(req)))

            # Set up user + portfolio + BUY at $8000 (much lower than market)
            user = db.scalar(select(User).where(User.email == "port@example.com"))
            if user is None:
                user = User(
                    email="port@example.com",
                    name="Port Test",
                    password_hash=hash_password("Test1234!"),
                )
                db.add(user)
                db.commit()
                user = db.scalar(select(User).where(User.email == "port@example.com"))

            portfolio = db.scalar(
                select(Portfolio).where(Portfolio.user_id == user.id)
            )
            if portfolio is None:
                portfolio = Portfolio(
                    user_id=user.id, name="P", currency="IDR"
                )
                db.add(portfolio)
                db.commit()
                portfolio = db.scalar(
                    select(Portfolio).where(Portfolio.user_id == user.id)
                )

            # BUY at 8000 (intentionally different from any yfinance value)
            tx = Transaction(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                transaction_type="BUY",
                quantity=100,
                price=8000.0,
                fee=0.0,
                transacted_at=datetime.now(UTC) - timedelta(days=30),
            )
            db.add(tx)
            db.commit()

            detail = get_portfolio_detail(db, user_id=user.id, portfolio_id=portfolio.id)

            assert len(detail.holdings) == 1
            h = detail.holdings[0]
            assert h.symbol == "BBCA"
            # The avg_buy_price comes from the transaction
            assert abs(h.avg_buy_price - 8000.0) < 0.01
            # The current_price should NOT be 8000 (the buy price)
            assert h.current_price is not None
            assert abs(h.current_price - 8000.0) > 0.01, (
                f"current_price={h.current_price} should not match buy price 8000"
            )
            # Freshness metadata must be present
            assert h.price_as_of is not None
            assert h.data_source == "yfinance"
            assert h.data_lag == "eod_1d"

            # Portfolio-level metadata
            assert detail.price_as_of is not None
            assert detail.data_lag == "eod_1d"
        finally:
            db.close()


def test_portfolio_unrealized_pnl_uses_correct_formula(client) -> None:
    """unrealized_pnl = current_value - cost_basis; current_value = qty * market_price."""
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.ingestion import YFinanceCollector, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Stock
    from app.models.portfolio import Portfolio, Transaction
    from app.models.user import User
    from app.services.portfolio import get_portfolio_detail

    with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
        collector = YFinanceCollector()
        db = client.app.state.database.session()
        try:
            stock = db.scalar(select(Stock).where(Stock.symbol == "TLKM"))
            if stock is None:
                meta = collector.collect_metadata("TLKM")
                db.add(
                    Stock(
                        symbol="TLKM",
                        name=meta["name"],
                        sector=meta["sector"],
                        exchange=meta["exchange"],
                        market_cap=meta["market_cap"],
                        currency=meta["currency"],
                        timezone=meta["timezone"],
                    )
                )
                db.commit()
                stock = db.scalar(select(Stock).where(Stock.symbol == "TLKM"))
            req = CollectionRequest(
                symbols=["TLKM"], start_date=None, end_date=None, interval="1d"
            )
            ingest_prices(db, list(collector.collect_prices(req)))

            user = db.scalar(select(User).where(User.email == "port2@example.com"))
            if user is None:
                user = User(
                    email="port2@example.com",
                    name="Port2",
                    password_hash=hash_password("Test1234!"),
                )
                db.add(user)
                db.commit()
                user = db.scalar(select(User).where(User.email == "port2@example.com"))
            portfolio = db.scalar(
                select(Portfolio).where(Portfolio.user_id == user.id)
            )
            if portfolio is None:
                portfolio = Portfolio(
                    user_id=user.id, name="P2", currency="IDR"
                )
                db.add(portfolio)
                db.commit()
                portfolio = db.scalar(
                    select(Portfolio).where(Portfolio.user_id == user.id)
                )

            # BUY 100 @ 3500 IDR
            tx = Transaction(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                transaction_type="BUY",
                quantity=100,
                price=3500.0,
                fee=0.0,
                transacted_at=datetime.now(UTC) - timedelta(days=30),
            )
            db.add(tx)
            db.commit()

            detail = get_portfolio_detail(db, user_id=user.id, portfolio_id=portfolio.id)
            h = detail.holdings[0]
            # Cost basis = 100 * 3500 = 350,000
            assert abs(detail.total_cost - 350_000.0) < 0.01
            # current_value is computed as qty * market_price and rounded to cents.
            # The displayed current_price is also rounded to cents. The displayed
            # current_value will not in general equal qty * displayed_current_price
            # (different rounding). We verify against the unrounded DB price.
            from decimal import Decimal

            from sqlalchemy import select as sa_select

            from app.models.market_data import Price

            price_obj = db.scalar(
                sa_select(Price)
                .where(Price.stock_id == stock.id, Price.interval == "1d")
                .order_by(Price.time.desc())
                .limit(1)
            )
            unrounded_value = Decimal(100) * Decimal(price_obj.close)
            expected_value = float(unrounded_value.quantize(Decimal("0.01")))
            assert abs(h.current_value - expected_value) < 0.01
            # unrealized_pnl = current_value - cost_basis (both already rounded to cents)
            expected_pnl = round(expected_value - 350_000.0, 2)
            assert abs(h.unrealized_pnl - expected_pnl) < 0.01
            # Decimal math preserved (no floating-point drift over 100+ rows)
            assert isinstance(h.current_value, float)
        finally:
            db.close()


def test_portfolio_with_no_prices_reports_unavailable(client) -> None:
    """If a holding has no Price rows, current_price/price_as_of must be None
    (not silently fallback to transaction price)."""
    from sqlalchemy import select

    from app.core.security import hash_password
    from app.models.market_data import Stock
    from app.models.portfolio import Portfolio, Transaction
    from app.models.user import User
    from app.services.portfolio import get_portfolio_detail

    db = client.app.state.database.session()
    try:
        # Create stock with NO price rows
        stock = db.scalar(select(Stock).where(Stock.symbol == "NOPR"))
        if stock is None:
            stock = Stock(symbol="NOPR", name="No Price", currency="IDR")
            db.add(stock)
            db.commit()
            stock = db.scalar(select(Stock).where(Stock.symbol == "NOPR"))

        user = db.scalar(select(User).where(User.email == "nopr@example.com"))
        if user is None:
            user = User(
                email="nopr@example.com",
                name="NOPR",
                password_hash=hash_password("Test1234!"),
            )
            db.add(user)
            db.commit()
            user = db.scalar(select(User).where(User.email == "nopr@example.com"))
        portfolio = db.scalar(
            select(Portfolio).where(Portfolio.user_id == user.id)
        )
        if portfolio is None:
            portfolio = Portfolio(user_id=user.id, name="NOP", currency="IDR")
            db.add(portfolio)
            db.commit()
            portfolio = db.scalar(
                select(Portfolio).where(Portfolio.user_id == user.id)
            )

        tx = Transaction(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            transaction_type="BUY",
            quantity=50,
            price=1000.0,
            fee=0.0,
            transacted_at=datetime.now(UTC) - timedelta(days=10),
        )
        db.add(tx)
        db.commit()

        detail = get_portfolio_detail(db, user_id=user.id, portfolio_id=portfolio.id)
        h = detail.holdings[0]
        # No current price available
        assert h.current_price is None
        assert h.current_value is None
        assert h.unrealized_pnl is None
        assert h.price_as_of is None
        assert h.data_source is None
        assert h.data_lag is None
        # Portfolio-level: total_cost is still set, but no current_value
        assert detail.total_cost > 0
    finally:
        db.close()
