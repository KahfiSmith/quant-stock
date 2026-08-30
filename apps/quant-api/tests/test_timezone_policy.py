"""Regression tests for timestamp policy.

These tests pin the production timezone semantics:
1. Persisted timestamps are UTC-tagged on write.
2. The `ensure_utc` helper re-attaches UTC on read for naive datetimes
   (SQLite test environment).
3. UTC-tagged datetimes are returned unchanged.
4. Non-UTC tagged datetimes are converted to UTC.

The unit-level tests use the SQLite test fixture from conftest.py.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from app.db.timezone import ensure_utc


def test_ensure_utc_tags_naive_as_utc() -> None:
    naive = datetime(2026, 1, 15, 9, 0, 0)
    result = ensure_utc(naive)
    assert result.tzinfo is not None
    assert result.tzinfo == UTC
    assert result.year == 2026 and result.month == 1 and result.day == 15


def test_ensure_utc_keeps_utc_untouched() -> None:
    aware = datetime(2026, 1, 15, 9, 0, 0, tzinfo=UTC)
    result = ensure_utc(aware)
    assert result == aware


def test_ensure_utc_converts_other_timezones_to_utc() -> None:

    jakarta = timezone(timedelta(hours=7))
    aware_jakarta = datetime(2026, 1, 15, 16, 0, 0, tzinfo=jakarta)
    result = ensure_utc(aware_jakarta)

    assert result.hour == 9
    assert result.tzinfo == UTC


def test_persisted_prices_have_utc_tagged_times_after_roundtrip(client) -> None:
    """End-to-end: a yfinance-shaped row written via ingest_prices roundtrips
    with UTC-tagged timestamps on PostgreSQL semantics. SQLite strips tzinfo
    on read by default; the ensure_utc helper re-attaches it."""
    from unittest.mock import patch

    import pandas as pd
    from sqlalchemy import select

    from app.ingestion import YFinanceCollector, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Price, Stock

    class FakeTicker:
        def __init__(self, symbol, **_):
            self._symbol = symbol
        def history(self, **kwargs):
            idx = pd.date_range(
                end=datetime(2026, 1, 15, tzinfo=UTC),
                periods=2,
                freq="D",
            )
            return pd.DataFrame(
                {
                    "Open": [100.0, 101.0],
                    "High": [105.0, 106.0],
                    "Low": [95.0, 96.0],
                    "Close": [102.0, 103.0],
                    "Volume": [1_000_000, 1_100_000],
                },
                index=idx,
            )

    with patch(
        "app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker
    ):
        collector = YFinanceCollector()
        db = client.app.state.database.session()
        try:
            stock = db.scalar(select(Stock).where(Stock.symbol == "TEST"))
            if stock is None:
                stock = Stock(
                    symbol="TEST", name="Test", currency="IDR"
                )
                db.add(stock)
                db.commit()
            req = CollectionRequest(
                symbols=["TEST"], start_date=None, end_date=None, interval="1d"
            )
            records = list(collector.collect_prices(req))
            assert len(records) > 0

            for r in records:
                assert r.time.tzinfo is not None, (
                    f"Record time must be UTC-tagged at write, got naive: {r.time}"
                )
                assert r.time.tzinfo == UTC
            ingest_prices(db, records)


            stored = db.query(Price).filter(Price.stock_id == stock.id).all()
            assert len(stored) == len(records)
            for p in stored:


                normalized = ensure_utc(p.time)
                assert normalized.tzinfo == UTC
        finally:
            db.close()
