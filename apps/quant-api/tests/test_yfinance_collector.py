"""Unit tests for YFinanceCollector. The yfinance library is fully mocked."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd

from app.ingestion.contracts import CollectionRequest
from app.ingestion.yfinance_collector import (
    YFinanceCollector,
    _normalize_debt_to_equity,
    _to_decimal,
)


class FakeTicker:
    """Stand-in for yfinance.Ticker that returns canned history/info."""

    def __init__(self, history_df: pd.DataFrame | None, info: dict | None) -> None:
        self._history_df = history_df
        self._info = info

    def history(self, **_kwargs) -> pd.DataFrame:  # noqa: ANN003
        if self._history_df is None:
            return pd.DataFrame()
        return self._history_df

    @property
    def info(self) -> dict:
        return self._info or {}


def _build_history_df(rows: list[tuple[datetime, float, float, float, float, int]]) -> pd.DataFrame:
    """rows = [(ts, O, H, L, C, V), ...]"""
    df = pd.DataFrame(rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
    df.index = pd.DatetimeIndex(df["ts"])
    df = df.drop(columns=["ts"])
    return df


def test_to_decimal_handles_none_nan_and_floats() -> None:
    assert _to_decimal(None) is None
    assert _to_decimal(float("nan")) is None
    assert _to_decimal("not a number") is None
    assert _to_decimal(12.5) == Decimal("12.5")
    assert _to_decimal(0) == Decimal("0")


def test_normalize_debt_to_equity_passthrough_for_small_values() -> None:
    assert _normalize_debt_to_equity(None) is None
    assert _normalize_debt_to_equity(Decimal("0.8")) == Decimal("0.8")
    assert _normalize_debt_to_equity(Decimal("4.99")) == Decimal("4.99")


def test_normalize_debt_to_equity_divides_by_100_for_large_values() -> None:
    # yfinance occasionally returns percentages (e.g. 80.5 = 0.805)
    result = _normalize_debt_to_equity(Decimal("80.5"))
    assert result == Decimal("0.8050")


def test_collect_prices_sorts_ascending_and_uses_yfinance_source(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    # yfinance returns DESCENDING; collector must sort ascending.
    rows_desc = [
        (base + timedelta(days=4), 110, 115, 105, 112, 1000),
        (base + timedelta(days=3), 105, 110, 100, 108, 900),
        (base + timedelta(days=2), 100, 105, 95, 103, 800),
        (base + timedelta(days=1), 95, 100, 90, 98, 700),
        (base + timedelta(days=0), 90, 95, 85, 93, 600),
    ]
    df = _build_history_df(rows_desc)
    fake = FakeTicker(history_df=df, info=None)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["BBCA"], start_date=None, end_date=None, interval="1d")
    records = list(collector.collect_prices(request))

    assert len(records) == 5
    # Ascending order
    for prev, curr in zip(records, records[1:]):
        assert curr.time > prev.time
    # yfinance source + suffix
    assert all(r.source == "yfinance" for r in records)
    assert all(r.source_record_id == "BBCA.JK" for r in records)
    # Symbol is uppercased, OHLCV is Decimal
    assert all(r.symbol == "BBCA" for r in records)
    assert all(isinstance(r.open, Decimal) for r in records)
    # All timestamps are tz-aware UTC
    assert all(r.time.tzinfo is not None for r in records)
    # Payload checksum is stable
    assert all(r.payload_checksum is not None for r in records)
    assert len(set(r.payload_checksum for r in records)) == 1


def test_collect_prices_drops_nan_rows(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    rows = [
        (base + timedelta(days=2), 110, 115, 105, 112, 1000),
        (base + timedelta(days=1), float("nan"), 100, 90, 95, 700),  # NaN open
        (base + timedelta(days=0), 90, 95, 85, 93, 600),
    ]
    df = _build_history_df(rows)
    fake = FakeTicker(history_df=df, info=None)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["TLKM"], start_date=None, end_date=None, interval="1d")
    records = list(collector.collect_prices(request))

    assert len(records) == 2
    assert all(r.close > 0 for r in records)


def test_collect_prices_appends_suffix_when_missing(monkeypatch) -> None:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    rows = [(base, 100, 105, 95, 102, 500)]
    df = _build_history_df(rows)
    fake = FakeTicker(history_df=df, info=None)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    # Lowercase input — collector should still produce the right yfinance symbol.
    request = CollectionRequest(symbols=["bbca"], start_date=None, end_date=None, interval="1d")
    records = list(collector.collect_prices(request))
    assert records[0].source_record_id == "BBCA.JK"
    assert records[0].symbol == "BBCA"


def test_collect_prices_handles_empty_history(monkeypatch) -> None:
    fake = FakeTicker(history_df=pd.DataFrame(), info=None)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["NONE"], start_date=None, end_date=None, interval="1d")
    assert list(collector.collect_prices(request)) == []


def test_collect_prices_continues_after_exception(monkeypatch) -> None:
    def exploding(_symbol, **_kwargs):
        raise RuntimeError("yfinance down")

    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", exploding)
    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["BBCA", "TLKM"], start_date=None, end_date=None, interval="1d")
    assert list(collector.collect_prices(request)) == []


def test_collect_fundamentals_maps_info_to_metrics(monkeypatch) -> None:
    info = {
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
        "debtToEquity": 0.8,  # already a ratio
        "revenueGrowth": 0.10,
        "earningsGrowth": 0.12,
    }
    fake = FakeTicker(history_df=None, info=info)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["BBCA"], start_date=None, end_date=None, interval="1d")
    records = list(collector.collect_fundamentals(request))

    assert len(records) == 1
    rec = records[0]
    assert rec.source == "yfinance"
    assert rec.source_record_id == "BBCA.JK:info"
    assert rec.period_type == "TTM"
    assert rec.metrics["pe_ratio"] == Decimal("12.5")
    assert rec.metrics["pb_ratio"] == Decimal("1.8")
    assert rec.metrics["roe"] == Decimal("0.18")
    assert rec.metrics["debt_to_equity"] == Decimal("0.8")  # not divided


def test_collect_fundamentals_normalizes_large_debt_to_equity(monkeypatch) -> None:
    info = {
        "currency": "IDR",
        "trailingPE": 10.0,
        "priceToBook": 1.0,
        "returnOnEquity": 0.10,
        "returnOnAssets": 0.04,
        "debtToEquity": 80.0,  # percent, will be divided by 100
        "revenueGrowth": 0.05,
        "earningsGrowth": 0.07,
    }
    fake = FakeTicker(history_df=None, info=info)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["TLKM"], start_date=None, end_date=None, interval="1d")
    rec = list(collector.collect_fundamentals(request))[0]
    assert rec.metrics["debt_to_equity"] == Decimal("0.8000")


def test_collect_fundamentals_skips_when_no_metrics(monkeypatch) -> None:
    info = {"currency": "IDR", "longName": "Foo"}  # no ratio fields
    fake = FakeTicker(history_df=None, info=info)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    request = CollectionRequest(symbols=["EMPTY"], start_date=None, end_date=None, interval="1d")
    assert list(collector.collect_fundamentals(request)) == []


def test_collect_metadata_returns_expected_fields(monkeypatch) -> None:
    info = {
        "longName": "Bank Central Asia Tbk",
        "sector": "Financial Services",
        "exchange": "JKT",
        "marketCap": 1_200_000_000_000_000.0,
        "currency": "IDR",
        "exchangeTimezoneShortName": "Asia/Jakarta",
    }
    fake = FakeTicker(history_df=None, info=info)
    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", lambda *_a, **_k: fake)

    collector = YFinanceCollector()
    meta = collector.collect_metadata("BBCA")
    assert meta.name == "Bank Central Asia Tbk"
    assert meta.sector == "Financial Services"
    assert meta.exchange == "JKT"
    assert meta.market_cap == 1_200_000_000_000_000.0
    assert meta.currency == "IDR"
    assert meta.timezone == "Asia/Jakarta"


def test_collect_metadata_falls_back_safely_on_exception(monkeypatch) -> None:
    def exploding(_symbol, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("app.ingestion.yfinance_collector.yfinance.Ticker", exploding)
    collector = YFinanceCollector()
    meta = collector.collect_metadata("BBCA")
    assert meta.currency == "IDR"
    assert meta.timezone == "Asia/Jakarta"
    assert meta.name is None
