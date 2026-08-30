"""Regression tests for freshness metadata on price/portfolio responses.

These tests pin the audit fix for MEDIUM issue #1: `as_of` was misleading
(used request time, not data time). The new contract is:
  - `as_of` = response wall-clock time (unchanged)
  - `price_as_of` = market observation time of the latest returned price
  - `data_lag` = semantic staleness label (e.g. "eod_1d")
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import numpy as np
import pandas as pd


class FakeTicker:
    def __init__(self, symbol, **_):
        self._symbol = symbol

    def history(self, **kwargs):
        end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        dates = pd.date_range(end=end, periods=300, freq="D")
        np.random.seed(7)
        closes = 5000 + np.cumsum(np.random.randn(len(dates)) * 50)
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
            "longName": "Bank Central Asia",
            "sector": "Financial Services",
            "exchange": "JKT",
            "marketCap": 1_200_000_000_000_000,
            "currency": "IDR",
            "trailingPE": 14.2,
            "priceToBook": 2.8,
            "returnOnEquity": 0.21,
            "returnOnAssets": 0.034,
            "debtToEquity": 0.5,
            "revenueGrowth": 0.09,
            "earningsGrowth": 0.12,
        }


def test_prices_response_exposes_distinct_as_of_and_price_as_of(client) -> None:
    """PricesResponse must have separate as_of (request time) and price_as_of
    (market observation time of the latest returned candle)."""
    from sqlalchemy import select

    from app.ingestion import YFinanceCollector, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Stock


    with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
        collector = YFinanceCollector()
        db = client.app.state.database.session()
        try:
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
            req = CollectionRequest(
                symbols=["BBCA"], start_date=None, end_date=None, interval="1d"
            )
            ingest_prices(db, list(collector.collect_prices(req)))
        finally:
            db.close()


    client.post(
        "/api/v1/auth/register",
        json={
            "email": "fresh@example.com",
            "password": "Test1234!",
            "name": "Fresh Test",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "fresh@example.com", "password": "Test1234!"},
    )
    token = login.json()["data"]["access_token"]


    res = client.get(
        "/api/v1/stocks/BBCA/prices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()["data"]


    assert "as_of" in body, "PricesResponse must include as_of"
    assert "price_as_of" in body, "PricesResponse must include price_as_of"
    assert "data_lag" in body, "PricesResponse must include data_lag"


    items = body["items"]
    assert len(items) > 0
    last_item_time = items[-1]["time"]
    assert body["price_as_of"] is not None

    assert body["price_as_of"][:10] == last_item_time[:10], (
        f"price_as_of ({body['price_as_of']}) should match last item time ({last_item_time})"
    )


    assert body["data_lag"] == "eod_1d", (
        f"data_lag should be 'eod_1d' for yfinance data, got {body['data_lag']}"
    )


def test_screener_response_includes_data_lag(client) -> None:
    """ScreenerResponse should include data_lag when any item is yfinance-backed."""
    from sqlalchemy import select

    from app.ingestion import YFinanceCollector, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Stock

    with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
        collector = YFinanceCollector()
        db = client.app.state.database.session()
        try:
            for sym in ["BBCA", "TLKM"]:
                stock = db.scalar(select(Stock).where(Stock.symbol == sym))
                if stock is None:
                    meta = collector.collect_metadata(sym)
                    db.add(
                        Stock(
                            symbol=sym,
                            name=meta["name"],
                            sector=meta["sector"],
                            exchange=meta["exchange"],
                            market_cap=meta["market_cap"],
                            currency=meta["currency"],
                            timezone=meta["timezone"],
                        )
                    )
                    db.commit()
                req = CollectionRequest(
                    symbols=[sym], start_date=None, end_date=None, interval="1d"
                )
                ingest_prices(db, list(collector.collect_prices(req)))
        finally:
            db.close()

    client.post(
        "/api/v1/auth/register",
        json={"email": "scr@example.com", "password": "Test1234!", "name": "Scr Test"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "scr@example.com", "password": "Test1234!"},
    )
    token = login.json()["data"]["access_token"]
    res = client.post(
        "/api/v1/screener",
        headers={"Authorization": f"Bearer {token}"},
        json={"sort_by": "score", "page_size": 10},
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert "data_lag" in body
    assert body["data_lag"] == "eod_1d"
    for item in body["items"]:
        assert "price_as_of" in item, "ScreenerItem must include price_as_of"
        if item["close_price"] is not None:
            assert item["price_as_of"] is not None
