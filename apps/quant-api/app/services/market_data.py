from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.market_data import Price, Stock


def pagination_meta(page: int, page_size: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def list_stocks(
    db: Session,
    *,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Stock], int, dict[str, int]]:
    statement = select(Stock)
    count_statement = select(func.count(Stock.id))

    if search:
        pattern = f"%{search.strip()}%"
        where = or_(Stock.symbol.ilike(pattern), Stock.name.ilike(pattern))
        statement = statement.where(where)
        count_statement = count_statement.where(where)

    total = db.scalar(count_statement) or 0
    rows = list(
        db.scalars(
            statement.order_by(Stock.symbol.asc()).offset((page - 1) * page_size).limit(page_size)
        )
    )
    meta = pagination_meta(page, page_size, total)
    return rows, total, meta


def get_stock_by_symbol(db: Session, symbol: str) -> Stock | None:
    return db.scalar(select(Stock).where(Stock.symbol == symbol.upper()))


def list_prices(
    db: Session,
    stock_id: int,
    *,
    interval: str = "1d",
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = 1,
    page_size: int = 200,
) -> tuple[list[Price], int, dict[str, int], str]:
    statement = select(Price).where(
        Price.stock_id == stock_id,
        Price.interval == interval,
    )
    count_statement = select(func.count(Price.id)).where(
        Price.stock_id == stock_id,
        Price.interval == interval,
    )

    if start is not None:
        statement = statement.where(Price.time >= start)
        count_statement = count_statement.where(Price.time >= start)
    if end is not None:
        statement = statement.where(Price.time <= end)
        count_statement = count_statement.where(Price.time <= end)

    total = db.scalar(count_statement) or 0
    rows = list(
        db.scalars(
            statement.order_by(Price.time.asc()).offset((page - 1) * page_size).limit(page_size)
        )
    )

    data_source = rows[0].source if rows else "none"
    meta = pagination_meta(page, page_size, total)
    return rows, total, meta, data_source