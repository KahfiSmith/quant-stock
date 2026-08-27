from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.fundamental.scoring import calculate_fundamental_score
from app.ingestion.contracts import CollectedFundamental, CollectedPrice
from app.ingestion.validation import validate_fundamental, validate_price_batch
from app.models.fundamental import Fundamental
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


def ingest_fundamentals(db: Session, records: Iterable[CollectedFundamental]) -> int:
    persisted = 0
    for raw_record in records:
        record = validate_fundamental(raw_record)
        stock = db.scalar(select(Stock).where(Stock.symbol == record.symbol.upper()))
        if stock is None:
            raise ApiError(422, "UNKNOWN_SYMBOL", f"Unknown symbol: {record.symbol}")

        m = record.metrics
        pe_ratio = float(m["pe_ratio"]) if m.get("pe_ratio") is not None else None
        pb_ratio = float(m["pb_ratio"]) if m.get("pb_ratio") is not None else None
        roe = float(m["roe"]) if m.get("roe") is not None else None
        roa = float(m["roa"]) if m.get("roa") is not None else None
        debt_to_equity = float(m["debt_to_equity"]) if m.get("debt_to_equity") is not None else None
        revenue_growth = float(m["revenue_growth"]) if m.get("revenue_growth") is not None else None
        eps_growth = float(m["eps_growth"]) if m.get("eps_growth") is not None else None

        score = calculate_fundamental_score(
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            roe=roe,
            roa=roa,
            debt_to_equity=debt_to_equity,
            revenue_growth=revenue_growth,
            eps_growth=eps_growth,
        )

        existing = db.scalar(
            select(Fundamental).where(
                Fundamental.stock_id == stock.id,
                Fundamental.period_end == record.period_end,
                Fundamental.period_type == record.period_type,
            )
        )

        data = {
            "published_at": record.published_at,
            "currency": record.currency,
            "source_record_id": record.source_record_id,
            "retrieved_at": record.retrieved_at,
            "payload_checksum": record.payload_checksum,
            "validation_state": "valid",
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "roe": roe,
            "roa": roa,
            "debt_to_equity": debt_to_equity,
            "revenue_growth": revenue_growth,
            "eps_growth": eps_growth,
            "score": score,
            "source": record.source,
        }

        if existing is None:
            db.add(
                Fundamental(
                    stock_id=stock.id,
                    period_end=record.period_end,
                    period_type=record.period_type,
                    **data,
                )
            )
        else:
            for key, value in data.items():
                setattr(existing, key, value)
        persisted += 1
    db.commit()
    return persisted
