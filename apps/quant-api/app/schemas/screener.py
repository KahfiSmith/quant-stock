from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.market_data import PaginationMeta

SortByField = Literal["score", "symbol", "market_cap", "pe_ratio", "pb_ratio", "roe", "rsi"]
SortOrder = Literal["asc", "desc"]


class ScreenerRequest(BaseModel):
    search: str | None = Field(default=None, max_length=64)
    sector: str | None = Field(default=None, max_length=64)
    min_market_cap: float | None = None
    max_market_cap: float | None = None
    min_score: float | None = Field(default=None, ge=0, le=100)
    max_score: float | None = Field(default=None, ge=0, le=100)
    min_pe: float | None = None
    max_pe: float | None = None
    min_pb: float | None = None
    max_pb: float | None = None
    min_roe: float | None = None
    min_rsi: float | None = Field(default=None, ge=0, le=100)
    max_rsi: float | None = Field(default=None, ge=0, le=100)
    sort_by: SortByField = "score"
    sort_order: SortOrder = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ScreenerItem(BaseModel):
    id: int
    symbol: str
    name: str
    sector: str | None = None
    market_cap: float | None = None
    currency: str = "IDR"
    close_price: float | None = None
    quant_score: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    rsi: float | None = None
    trend: str = "neutral"


class ScreenerResponse(BaseModel):
    items: list[ScreenerItem]
    pagination: PaginationMeta
    as_of: datetime
