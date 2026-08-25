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


class StocksResponse(BaseModel):
    items: list[StockResponse]
    pagination: PaginationMeta = Field(...)
    as_of: datetime


class PricesResponse(BaseModel):
    symbol: str
    data_source: str
    items: list[PriceResponse]
    pagination: PaginationMeta
    as_of: datetime