from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.market_data import PaginationMeta

SortByField = Literal[
    "score",
    "symbol",
    "market_cap",
    "pe_ratio",
    "pb_ratio",
    "roe",
    "rsi",
    "volume_zscore",
    "atr_percent",
    "momentum_1m",
    "sharpe_ratio",
    "value_score",
    "quality_score",
    "momentum_score",
    "composite_rank",
]
SortOrder = Literal["asc", "desc"]


class CustomWeightsInput(BaseModel):
    momentum: float = 0.30
    quality: float = 0.25
    value: float = 0.20
    risk: float = 0.15
    growth: float = 0.10


class ScreenerRequest(BaseModel):
    search: str | None = Field(default=None, max_length=64)
    exchange: str = Field(default="IDX", max_length=64)
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
    min_volume_zscore: float | None = None
    max_volume_zscore: float | None = None
    volatility_regime: Literal["LOW", "NORMAL", "HIGH", "EXTREME"] | None = None
    strategy_preset: Literal["none", "quality_momentum", "deep_value", "garp", "defensive_income", "volume_momentum", "mean_reversion"] = "none"
    custom_weights: CustomWeightsInput | None = None
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
            ("volume_zscore", self.min_volume_zscore, self.max_volume_zscore),
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

    price_as_of: datetime | None = None

    as_of: datetime | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    rsi: float | None = None
    trend: str = "neutral"

    signal: Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"] = "HOLD"
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    signal_confidence_pct: float | None = None
    signal_reasons: list[str] = Field(default_factory=list)
    volume_zscore: float | None = None
    volume_sma_ratio: float | None = None
    atr_percent: float | None = None
    volatility_regime: str | None = None
    momentum_1m: float | None = None
    max_drawdown_pct: float | None = None
    sharpe_ratio: float | None = None
    value_score: float | None = None
    quality_score: float | None = None
    momentum_score: float | None = None
    growth_score: float | None = None
    risk_score: float | None = None
    composite_rank: int | None = None
    percentile: float | None = None


class ScreenerResponse(BaseModel):
    items: list[ScreenerItem]
    pagination: PaginationMeta

    as_of: datetime = Field(
        description="Wall-clock time of the response. NOT data freshness.",
    )
    data_lag: str | None = Field(
        default=None,
        description="Semantic staleness label, e.g. 'eod_1d' for yfinance free-tier IDX.",
    )
