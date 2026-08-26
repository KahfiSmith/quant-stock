from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RatiosSummary(BaseModel):
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    roa: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    eps_growth: float | None = None


class FundamentalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_end: date
    published_at: datetime | None = None
    period_type: str
    score: float | None = None
    ratios: RatiosSummary
    source: str
    as_of: datetime
