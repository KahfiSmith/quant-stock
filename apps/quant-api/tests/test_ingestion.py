from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.api.errors import ApiError
from app.ingestion import (
    CollectedFundamental,
    CollectedPrice,
    IngestionValidationError,
    ingest_prices,
    validate_fundamental,
    validate_price_batch,
)
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
