from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    sector: str | None = None
    exchange: str | None = None
    currency: str
    timezone: str | None = None
    market_cap: float | None = None
    updated_at: datetime | None = None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str
    source: str
    source_record_id: str | None = None
    retrieved_at: datetime | None = None
    payload_checksum: str | None = None
    validation_state: str


class StocksResponse(BaseModel):
    items: list[StockResponse]
    pagination: PaginationMeta = Field(...)
    as_of: datetime = Field(
        description="Wall-clock time of the response. NOT the freshness of the underlying data.",
    )


class PricesResponse(BaseModel):
    symbol: str
    data_source: str
    items: list[PriceResponse]
    pagination: PaginationMeta
    as_of: datetime = Field(
        description="Wall-clock time of the response. NOT the freshness of the underlying data.",
    )
    price_as_of: datetime | None = Field(
        default=None,
        description=(
            "Market observation time of the latest price in `items`. "
            "This is the actual freshness of the data (EOD, with 1-day lag for yfinance EOD). "
            "Distinct from `as_of` which is the request time."
        ),
    )
    data_lag: str | None = Field(
        default=None,
        description=(
            "Semantic description of the data staleness, e.g. 'eod_1d' (end-of-day, 1-day lag). "
            "Use this instead of 'live' / 'real-time' which are not guaranteed."
        ),
    )