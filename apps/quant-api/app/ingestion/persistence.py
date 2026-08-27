from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.ingestion.contracts import CollectedPrice
from app.ingestion.validation import validate_price_batch
from app.models.market_data import Price, Stock


def ingest_prices(db: Session, records: Iterable[CollectedPrice]) -> int:
    validated = validate_price_batch(records)
    persisted = 0
    for record in validated:
        stock = db.scalar(select(Stock).where(Stock.symbol == record.symbol))
        if stock is None:
            raise ApiError(422, "UNKNOWN_SYMBOL", f"Unknown symbol: {record.symbol}")
        existing = db.scalar(
            select(Price).where(
                Price.stock_id == stock.id,
                Price.time == record.time,
                Price.interval == record.interval,
                Price.source == record.source,
            )
        )
        values = {
            "source_record_id": record.source_record_id,
            "retrieved_at": record.retrieved_at,
            "payload_checksum": record.payload_checksum,
            "validation_state": "valid",
        }
        if existing is None:
            db.add(
                Price(
                    stock_id=stock.id,
                    time=record.time,
                    open=record.open,
                    high=record.high,
                    low=record.low,
                    close=record.close,
                    volume=record.volume,
                    interval=record.interval,
                    source=record.source,
                    **values,
                )
            )
        else:
            for key, value in values.items():
                setattr(existing, key, value)
        persisted += 1
    db.commit()
    return persisted
