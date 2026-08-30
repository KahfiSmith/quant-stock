from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.api.errors import ApiError
from app.ingestion import (
    CollectedFundamental,
    CollectedPrice,
    IngestionValidationError,
    ingest_fundamentals,
    ingest_prices,
    validate_fundamental,
    validate_price_batch,
)
from app.models.fundamental import Fundamental
from app.models.market_data import Price, Stock


def _record(symbol: str = "BBCA", day: int = 1, close: str = "105") -> CollectedPrice:
    return CollectedPrice(
        symbol=symbol,
        time=datetime(2026, 1, day),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal(close),
        volume=Decimal("1000"),
        interval="1d",
        source="fixture",
    )


def test_validate_price_normalizes_symbol_and_timestamp() -> None:
    result = validate_price_batch([_record("bbca")])[0]
    assert result.symbol == "BBCA"
    assert result.time.tzinfo == UTC


def test_validate_price_rejects_invalid_ohlcv() -> None:
    invalid = _record()
    invalid = CollectedPrice(**{**invalid.__dict__, "close": Decimal("120")})
    with pytest.raises(IngestionValidationError):
        validate_price_batch([invalid])


def test_validate_price_rejects_duplicates_and_unsorted_batches() -> None:
    with pytest.raises(IngestionValidationError):
        validate_price_batch([_record(day=1), _record(day=1)])
    with pytest.raises(IngestionValidationError):
        validate_price_batch([_record(day=2), _record(day=1)])


def test_validate_fundamental_requires_traceable_provenance() -> None:
    record = CollectedFundamental(
        symbol="BBCA",
        period_end=date(2025, 12, 31),
        published_at=datetime(2026, 1, 15, tzinfo=UTC),
        currency="IDR",
        period_type="TTM",
        metrics={"roe": Decimal("0.2")},
        source="sample",
        source_record_id="fixture-1",
        retrieved_at=datetime(2026, 1, 16, tzinfo=UTC),
    )
    assert validate_fundamental(record) == record
    with pytest.raises(IngestionValidationError):
        validate_fundamental(record.__class__(**{**record.__dict__, "source_record_id": ""}))


def test_ingest_prices_is_idempotent_and_preserves_provenance(client) -> None:
    db = client.app.state.database.session()
    try:
        stock = Stock(symbol="BBCA", name="Bank Central Asia", currency="IDR")
        db.add(stock)
        db.commit()
        record = _record()
        assert ingest_prices(db, [record]) == 1
        assert ingest_prices(db, [CollectedPrice(**{**record.__dict__, "payload_checksum": "updated"})]) == 1
        rows = db.query(Price).all()
        assert len(rows) == 1
        assert rows[0].payload_checksum == "updated"
    finally:
        db.close()


def test_ingest_prices_rejects_unknown_symbol(client) -> None:
    db = client.app.state.database.session()
    try:
        with pytest.raises(ApiError) as error:
            ingest_prices(db, [_record("UNKNOWN")])
        assert error.value.code == "UNKNOWN_SYMBOL"
    finally:
        db.close()


def test_ingest_fundamentals_is_idempotent_and_calculates_score(client) -> None:
    db = client.app.state.database.session()
    try:
        stock = Stock(symbol="BBCA", name="Bank Central Asia", currency="IDR")
        db.add(stock)
        db.commit()

        fund_record = CollectedFundamental(
            symbol="BBCA",
            period_end=date(2025, 12, 31),
            published_at=datetime(2026, 1, 15, tzinfo=UTC),
            currency="IDR",
            period_type="TTM",
            metrics={
                "pe_ratio": Decimal("12.5"),
                "pb_ratio": Decimal("1.8"),
                "roe": Decimal("0.18"),
                "roa": Decimal("0.05"),
                "debt_to_equity": Decimal("0.4"),
                "revenue_growth": Decimal("0.12"),
                "eps_growth": Decimal("0.15"),
            },
            source="sec_filing",
            source_record_id="filing-2025-q4",
            retrieved_at=datetime(2026, 1, 16, tzinfo=UTC),
            payload_checksum="chk-1234",
        )

        assert ingest_fundamentals(db, [fund_record]) == 1
        rows = db.query(Fundamental).all()
        assert len(rows) == 1
        assert float(rows[0].pe_ratio) == 12.5
        assert float(rows[0].score) > 80.0
        assert rows[0].validation_state == "valid"
        assert rows[0].source_record_id == "filing-2025-q4"


        updated_record = CollectedFundamental(
            symbol="BBCA",
            period_end=date(2025, 12, 31),
            published_at=datetime(2026, 1, 15, tzinfo=UTC),
            currency="IDR",
            period_type="TTM",
            metrics={
                "pe_ratio": Decimal("10.0"),
                "pb_ratio": Decimal("1.5"),
                "roe": Decimal("0.20"),
                "roa": Decimal("0.06"),
                "debt_to_equity": Decimal("0.3"),
                "revenue_growth": Decimal("0.15"),
                "eps_growth": Decimal("0.18"),
            },
            source="sec_filing",
            source_record_id="filing-2025-q4-amended",
            retrieved_at=datetime(2026, 1, 17, tzinfo=UTC),
            payload_checksum="chk-amended",
        )
        assert ingest_fundamentals(db, [updated_record]) == 1
        rows = db.query(Fundamental).all()
        assert len(rows) == 1
        assert float(rows[0].pe_ratio) == 10.0
        assert rows[0].source_record_id == "filing-2025-q4-amended"
        assert rows[0].payload_checksum == "chk-amended"
    finally:
        db.close()


def test_ingest_fundamentals_rejects_unknown_symbol(client) -> None:
    db = client.app.state.database.session()
    try:
        fund_record = CollectedFundamental(
            symbol="UNKNOWN",
            period_end=date(2025, 12, 31),
            published_at=datetime(2026, 1, 15, tzinfo=UTC),
            currency="IDR",
            period_type="TTM",
            metrics={},
            source="sec_filing",
            source_record_id="rec-1",
            retrieved_at=datetime(2026, 1, 16, tzinfo=UTC),
        )
        with pytest.raises(ApiError) as error:
            ingest_fundamentals(db, [fund_record])
        assert error.value.code == "UNKNOWN_SYMBOL"
    finally:
        db.close()
