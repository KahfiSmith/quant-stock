from collections.abc import Iterable

from app.ingestion.contracts import CollectedFundamental, CollectedPrice


class IngestionValidationError(ValueError):
    pass


def validate_price(record: CollectedPrice) -> CollectedPrice:
    item = record.normalized()
    if not item.symbol or not item.interval or not item.source:
        raise IngestionValidationError("symbol, interval, and source are required")
    if item.high < item.low:
        raise IngestionValidationError("high must be greater than or equal to low")
    if not item.low <= item.open <= item.high:
        raise IngestionValidationError("open must be within low-high range")
    if not item.low <= item.close <= item.high:
        raise IngestionValidationError("close must be within low-high range")
    if item.open < 0 or item.high < 0 or item.low < 0 or item.close < 0 or item.volume < 0:
        raise IngestionValidationError("price and volume values must be non-negative")
    return item


def validate_price_batch(records: Iterable[CollectedPrice]) -> list[CollectedPrice]:
    validated = [validate_price(record) for record in records]
    keys = [(item.symbol, item.time, item.interval, item.source) for item in validated]
    if len(keys) != len(set(keys)):
        raise IngestionValidationError("duplicate candle timestamps are not allowed")
    if keys != sorted(keys, key=lambda key: (key[0], key[2], key[3], key[1])):
        raise IngestionValidationError("candles must be strictly time-ordered")
    return validated


def validate_fundamental(record: CollectedFundamental) -> CollectedFundamental:
    if not record.symbol or not record.period_type or not record.currency:
        raise IngestionValidationError("symbol, period type, and currency are required")
    if not record.source or not record.source_record_id or not record.retrieved_at:
        raise IngestionValidationError("fundamental provenance is required")
    if record.published_at > record.retrieved_at:
        raise IngestionValidationError("published_at cannot be after retrieved_at")
    return record


__all__ = [
    "IngestionValidationError",
    "validate_fundamental",
    "validate_price",
    "validate_price_batch",
]
