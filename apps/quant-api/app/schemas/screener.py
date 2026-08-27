from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

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

    @model_validator(mode="after")
    def validate_ranges(self) -> "ScreenerRequest":
        ranges = (
            ("market_cap", self.min_market_cap, self.max_market_cap),
            ("score", self.min_score, self.max_score),
            ("pe", self.min_pe, self.max_pe),
            ("pb", self.min_pb, self.max_pb),
            ("rsi", self.min_rsi, self.max_rsi),
        )
        for name, minimum, maximum in ranges:
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"min_{name} must be less than or equal to max_{name}")
        return self


class ScreenerItem(BaseModel):
    id: int
    symbol: str
    name: str
    sector: str | None = None
    market_cap: float | None = None
    currency: str = "IDR"
    close_price: float | None = None
    quant_score: float | None = None
    score_version: str | None = None
    data_source: str | None = None
    # price_as_of: market observation time of the latest price for THIS item.
    price_as_of: datetime | None = None
    # as_of: kept for backward compat. New code should use price_as_of.
    as_of: datetime | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    rsi: float | None = None
    trend: str = "neutral"


class ScreenerResponse(BaseModel):
    items: list[ScreenerItem]
    pagination: PaginationMeta
    # as_of: response wall-clock time. NOT the freshness of underlying data.
    as_of: datetime = Field(
        description="Wall-clock time of the response. NOT data freshness.",
    )
    data_lag: str | None = Field(
        default=None,
        description="Semantic staleness label, e.g. 'eod_1d' for yfinance free-tier IDX.",
    )
