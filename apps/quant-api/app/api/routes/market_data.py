from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.errors import ApiError, success
from app.models.user import User
from app.schemas.market_data import (
    PriceResponse,
    PricesResponse,
    StockResponse,
    StocksResponse,
)
from app.services.market_data import get_stock_by_symbol, list_prices, list_stocks

router = APIRouter(prefix="/api/v1/stocks", tags=["market-data"])


def utc_now() -> datetime:
    return datetime.now(UTC)


@router.get("", include_in_schema=True)
def get_stocks(
    search: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rows, _total, meta = list_stocks(db, search=search, page=page, page_size=page_size)
    return success(
        StocksResponse(
            items=[StockResponse.model_validate(stock) for stock in rows],
            pagination=meta,
            as_of=utc_now(),
        ).model_dump(mode="json"),
        "Stocks retrieved",
    )


@router.get("/{symbol}/prices")
def get_stock_prices(
    symbol: str,
    interval: str = Query(default="1d", pattern="^(1d|1w|1mo)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, object]:
    stock = get_stock_by_symbol(db, symbol)
    if stock is None:
        raise ApiError(404, "SYMBOL_NOT_FOUND", f"Unknown symbol: {symbol.upper()}")

    rows, _total, meta, data_source = list_prices(
        db,
        stock.id,
        interval=interval,
        page=page,
        page_size=page_size,
    )
    return success(
        PricesResponse(
            symbol=stock.symbol,
            data_source=data_source,
            items=[PriceResponse.model_validate(price) for price in rows],
            pagination=meta,
            as_of=utc_now(),
        ).model_dump(mode="json"),
        "Prices retrieved",
    )