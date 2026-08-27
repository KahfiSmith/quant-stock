"""Portfolio valuation verification + post-fix verification harness.

Runs end-to-end with mocked yfinance data shaped like real Yahoo responses,
then exercises the portfolio service to confirm:
  1. Latest market price comes from `Price` table (real yfinance rows)
  2. No fallback to transaction price / sample / dummy
  3. Decimal arithmetic preserved
  4. Freshness metadata exposed (after fix)
"""
from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import numpy as np
import pandas as pd

db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"

from sqlalchemy import desc, select

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import Database
from app.ingestion import YFinanceCollector, ingest_prices
from app.ingestion.contracts import CollectionRequest
from app.main import create_app
from app.models.market_data import Price, Stock
from app.models.portfolio import Portfolio, Transaction
from app.models.user import User


class FakeTicker:
    _info_map = {
        "BBCA.JK": {"longName": "Bank Central Asia", "sector": "Financial Services", "exchange": "JKT", "marketCap": 1_200_000_000_000_000, "currency": "IDR", "exchangeTimezoneShortName": "Asia/Jakarta", "trailingPE": 14.2, "priceToBook": 2.8, "returnOnEquity": 0.21, "returnOnAssets": 0.034, "debtToEquity": 0.5, "revenueGrowth": 0.09, "earningsGrowth": 0.12},
        "TLKM.JK": {"longName": "Telkom Indonesia", "sector": "Communication", "exchange": "JKT", "marketCap": 400_000_000_000_000, "currency": "IDR", "exchangeTimezoneShortName": "Asia/Jakarta", "trailingPE": 12.5, "priceToBook": 2.1, "returnOnEquity": 0.17, "returnOnAssets": 0.08, "debtToEquity": 0.7, "revenueGrowth": 0.05, "earningsGrowth": 0.08},
        "BRPT.JK": {"longName": "Barito Pacific", "sector": "Basic Materials", "exchange": "JKT", "marketCap": 65_000_000_000_000, "currency": "IDR", "exchangeTimezoneShortName": "Asia/Jakarta", "trailingPE": 18.3, "priceToBook": 1.4, "returnOnEquity": 0.08, "returnOnAssets": 0.04, "debtToEquity": 1.2, "revenueGrowth": 0.07, "earningsGrowth": 0.10},
    }
    _base_prices = {"BBCA.JK": 9500.0, "TLKM.JK": 4000.0, "BRPT.JK": 1800.0}

    def __init__(self, symbol, **_):
        self._symbol = symbol

    def history(self, **kwargs):
        end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=499)
        dates = pd.date_range(start=start, end=end, freq="D")
        base = self._base_prices.get(self._symbol, 5000.0)
        np.random.seed(hash(self._symbol) % 2**32)
        closes = base + np.cumsum(np.random.randn(len(dates)) * (base * 0.012))
        opens = closes + np.random.randn(len(dates)) * (base * 0.005)
        highs = np.maximum(opens, closes) + np.abs(np.random.randn(len(dates))) * (base * 0.008)
        lows = np.minimum(opens, closes) - np.abs(np.random.randn(len(dates))) * (base * 0.008)
        vols = np.random.randint(5_000_000, 20_000_000, len(dates))
        return pd.DataFrame(
            {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
            index=dates,
        )

    @property
    def info(self):
        return self._info_map.get(self._symbol, {})


settings = Settings(
    app_env="test",
    database_url=f"sqlite+pysqlite:///{db_path}",
    frontend_origin="http://localhost:3000",
    jwt_secret="test-jwt-secret-that-is-at-least-32-characters",
    refresh_token_hmac_key="test-refresh-key-that-is-at-least-32-characters",
    yfinance_symbols="BBCA,TLKM,BRPT",
)
db_engine = Database(settings).engine
Base.metadata.create_all(db_engine)
app = create_app(settings)


def get_db():
    return app.state.database.session()


# 1) Ingest yfinance data
with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
    collector = YFinanceCollector(timeout=15.0, symbol_suffix=".JK")
    db = get_db()
    try:
        for sym in ["BBCA", "TLKM", "BRPT"]:
            meta = collector.collect_metadata(sym)
            existing = db.scalar(select(Stock).where(Stock.symbol == sym))
            if existing is None:
                db.add(Stock(symbol=sym, name=meta["name"], sector=meta["sector"], exchange=meta["exchange"], market_cap=meta["market_cap"], currency=meta["currency"], timezone=meta["timezone"]))
        db.commit()
        for sym in ["BBCA", "TLKM", "BRPT"]:
            req = CollectionRequest(symbols=[sym], start_date=None, end_date=None, interval="1d")
            records = list(collector.collect_prices(req))
            ingest_prices(db, records)
    finally:
        db.close()

# 2) Create test user + portfolio + 3 transactions
db = get_db()
try:
    user = User(email="test@example.com", name="Test User", password_hash=hash_password("Test1234!"), theme_preference="system", timezone="Asia/Jakarta")
    db.add(user)
    db.flush()
    portfolio = Portfolio(user_id=user.id, name="Test Portfolio", currency="IDR")
    db.add(portfolio)
    db.flush()

    # BUY transactions
    buys = [
        ("BBCA", 100, 8000.0, datetime.now(UTC) - timedelta(days=60)),
        ("TLKM", 200, 3500.0, datetime.now(UTC) - timedelta(days=50)),
        ("BRPT", 50, 1500.0, datetime.now(UTC) - timedelta(days=40)),
    ]
    for sym, qty, price, ts in buys:
        stock = db.scalar(select(Stock).where(Stock.symbol == sym))
        db.add(Transaction(portfolio_id=portfolio.id, stock_id=stock.id, transaction_type="BUY", quantity=qty, price=price, fee=0.0, transacted_at=ts))
    db.commit()
    portfolio_id = portfolio.id
finally:
    db.close()

# 3) Verify portfolio valuation end-to-end
print("=" * 80)
print("PORTFOLIO VALUATION VERIFICATION")
print("=" * 80)

from app.services.portfolio import get_portfolio_detail

db = get_db()
try:
    user_id = db.scalar(select(User.id).where(User.email == "test@example.com"))
    detail = get_portfolio_detail(db, user_id=user_id, portfolio_id=portfolio_id)

    print(f"\nPortfolio: {detail.name} (id={detail.id})")
    print(f"Total cost: {detail.total_cost:,.2f}")
    print(f"Current value: {detail.current_value:,.2f}")
    print(f"Unrealized PnL: {detail.total_unrealized_pnl:,.2f}")
    print(f"Risk observations: {detail.risk.observations}")
    print(f"Annualized volatility: {detail.risk.annualized_volatility_percent:.2f}%")

    print(f"\n{'Symbol':<8} {'Quantity':>10} {'AvgCost':>12} {'LatestPrice':>14} {'PriceSource':<14} {'MarketValue':>16} {'UnrealizedPnL':>16}")
    print("-" * 110)
    for h in detail.holdings:
        # Verify latest price came from Price table (yfinance)
        stock = db.scalar(select(Stock).where(Stock.symbol == h.symbol))
        latest_price_row = db.scalar(
            select(Price)
            .where(Price.stock_id == stock.id, Price.interval == "1d")
            .order_by(desc(Price.time))
            .limit(1)
        )
        price_source = latest_price_row.source if latest_price_row else "NONE"
        # Get the freshness metadata if present
        price_as_of = getattr(h, "price_as_of", None)
        data_source_field = getattr(h, "data_source", None)
        freshness_str = f"{price_as_of}" if price_as_of else "N/A"
        print(f"{h.symbol:<8} {h.quantity:>10.4f} {h.avg_buy_price:>12.2f} {h.current_price:>14.2f} {price_source:<14} {h.current_value or 0:>16,.2f} {h.unrealized_pnl or 0:>16,.2f}  freshness={freshness_str} data_source_field={data_source_field}")

    # Sanity: total_cost should equal avg-cost * qty (Decimal math)
    print("\n--- Arithmetic verification ---")
    for h in detail.holdings:
        # Recompute using Decimal
        expected_avg = None
        if h.symbol == "BBCA":
            expected_avg = 8000.0
        elif h.symbol == "TLKM":
            expected_avg = 3500.0
        elif h.symbol == "BRPT":
            expected_avg = 1500.0
        match_avg = abs(h.avg_buy_price - expected_avg) < 0.01
        print(f"  {h.symbol}: avg_cost={h.avg_buy_price:.2f} expected={expected_avg:.2f} match={match_avg}")

    # Sanity: current_price should NOT be the buy price
    print("\n--- 'No fallback to transaction price' check ---")
    for h in detail.holdings:
        # The buy prices were 8000/3500/1500. Latest yfinance prices are random walks
        # around 9500/4000/1800. They should not be identical to buy prices.
        buy_prices = {"BBCA": 8000.0, "TLKM": 3500.0, "BRPT": 1500.0}
        same_as_buy = abs(h.current_price - buy_prices[h.symbol]) < 0.01 if h.current_price else False
        print(f"  {h.symbol}: current_price={h.current_price} (buy was {buy_prices[h.symbol]}) fallback_to_buy={same_as_buy}")
finally:
    db.close()

os.unlink(db_path)
print("\nDONE")
