"""Integration tests for the backfill_market_data script.

Mocks the yfinance library to feed deterministic data through the full
ingestion path (metadata + prices + fundamentals), without any network access.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from sqlalchemy import select

from app.models.fundamental import Fundamental
from app.models.market_data import Price, Stock
from scripts.backfill_market_data import _ensure_stocks, run


class FakeTicker:
    def __init__(self, symbol: str) -> None:
        self._symbol = symbol
        self._meta = {
            "BBCA.JK": {
                "longName": "Bank Central Asia Tbk",
                "sector": "Financial Services",
                "exchange": "JKT",
                "marketCap": 1_200_000_000_000_000,
                "currency": "IDR",
                "exchangeTimezoneShortName": "Asia/Jakarta",
                "trailingPE": 12.5,
                "priceToBook": 1.8,
                "returnOnEquity": 0.18,
                "returnOnAssets": 0.05,
                "debtToEquity": 0.8,
                "revenueGrowth": 0.10,
                "earningsGrowth": 0.12,
            },
            "TLKM.JK": {
                "longName": "Telkom Indonesia",
                "sector": "Communication Services",
                "exchange": "JKT",
                "marketCap": 400_000_000_000_000,
                "currency": "IDR",
                "exchangeTimezoneShortName": "Asia/Jakarta",
                "trailingPE": 14.0,
                "priceToBook": 2.0,
                "returnOnEquity": 0.15,
                "returnOnAssets": 0.06,
                "debtToEquity": 0.7,
                "revenueGrowth": 0.05,
                "earningsGrowth": 0.08,
            },
        }

    def history(self, **_kwargs) -> pd.DataFrame:  # noqa: ANN003
        base = datetime(2024, 1, 1, tzinfo=UTC)
        rows = [
            (base, 100, 105, 95, 102, 1_000_000),
            (base.replace(day=2), 102, 108, 101, 107, 1_100_000),
            (base.replace(day=3), 107, 110, 105, 109, 1_050_000),
        ]
        df = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
        df.index = pd.DatetimeIndex(df["ts"])
        return df.drop(columns=["ts"])

    @property
    def info(self) -> dict:
        return self._meta.get(self._symbol, {})


@pytest.fixture()
def fake_ticker_factory(monkeypatch):
    def factory(symbol: str, **_kwargs) -> FakeTicker:
        return FakeTicker(symbol)

    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", factory)
    return factory


def test_ensure_stocks_creates_rows_with_real_metadata(client, fake_ticker_factory) -> None:
    db = client.app.state.database.session()
    try:
        from app.ingestion.yfinance_collector import YFinanceCollector

        collector = YFinanceCollector()
        resolved = _ensure_stocks(db, collector, ["BBCA", "TLKM"])

        assert set(resolved.keys()) == {"BBCA", "TLKM"}
        bbca = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
        assert bbca is not None
        assert bbca.name == "Bank Central Asia Tbk"
        assert bbca.sector == "Financial Services"
        assert bbca.currency == "IDR"
        assert bbca.timezone == "Asia/Jakarta"
        assert bbca.market_cap is not None
    finally:
        db.close()


def test_ensure_stocks_updates_existing_rows(client, fake_ticker_factory) -> None:
    db = client.app.state.database.session()
    try:

        existing = Stock(
            symbol="BBCA",
            name="Placeholder",
            sector="Unknown",
            currency="IDR",
        )
        db.add(existing)
        db.commit()

        from app.ingestion.yfinance_collector import YFinanceCollector

        collector = YFinanceCollector()
        _ensure_stocks(db, collector, ["BBCA"])

        refreshed = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
        assert refreshed.name == "Bank Central Asia Tbk"
        assert refreshed.sector == "Financial Services"
    finally:
        db.close()


def test_run_end_to_end_ingests_prices_and_fundamentals(client, fake_ticker_factory) -> None:
    """Full backfill run with mocked yfinance; assert rows land in the DB."""
    monkeypatch_symbols = ["BBCA", "TLKM"]


    test_settings = client.app.state.settings


    db = client.app.state.database.session()
    try:
        for sym in monkeypatch_symbols:
            db.add(Stock(symbol=sym, name=sym, currency="IDR"))
        db.commit()

        exit_code = run(
            ["--symbols", "BBCA,TLKM", "--rate-limit-seconds", "0"],
            settings=test_settings,
            db=db,
        )
        assert exit_code == 0

        prices = db.query(Price).filter(Price.source == "yfinance").all()

        assert len(prices) == 6

        assert all(p.payload_checksum is not None for p in prices)

        funds = db.query(Fundamental).filter(Fundamental.source == "yfinance").all()
        assert len(funds) == 2

        assert all(f.score is not None for f in funds)


        bbca = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
        assert bbca.sector == "Financial Services"
        assert bbca.exchange == "IDX"
        assert bbca.name == "Bank Central Asia Tbk"
    finally:
        db.close()


def test_run_is_idempotent_on_rerun(client, fake_ticker_factory) -> None:
    """Re-running the backfill must not duplicate price rows."""
    test_settings = client.app.state.settings
    db = client.app.state.database.session()
    try:
        for sym in ["BBCA", "TLKM"]:
            db.add(Stock(symbol=sym, name=sym, currency="IDR"))
        db.commit()

        run(
            ["--symbols", "BBCA,TLKM", "--rate-limit-seconds", "0"],
            settings=test_settings,
            db=db,
        )
        run(
            ["--symbols", "BBCA,TLKM", "--rate-limit-seconds", "0"],
            settings=test_settings,
            db=db,
        )

        prices = db.query(Price).filter(Price.source == "yfinance").all()

        assert len(prices) == 6
    finally:
        db.close()


def test_run_skip_fundamentals_only_ingests_prices(client, fake_ticker_factory) -> None:
    test_settings = client.app.state.settings
    db = client.app.state.database.session()
    try:
        db.add(Stock(symbol="BBCA", name="BBCA", currency="IDR"))
        db.commit()

        run(
            ["--symbols", "BBCA", "--skip-fundamentals", "--rate-limit-seconds", "0"],
            settings=test_settings,
            db=db,
        )

        assert db.query(Price).count() == 3
        assert db.query(Fundamental).count() == 0
    finally:
        db.close()
