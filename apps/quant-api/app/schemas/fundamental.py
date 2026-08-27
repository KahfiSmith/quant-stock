from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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
    currency: str | None = None
    period_type: str
    score: float | None = None
    ratios: RatiosSummary
    source: str
    source_record_id: str | None = None
    retrieved_at: datetime | None = None
    payload_checksum: str | None = None
    validation_state: str
    units: dict[str, str] = Field(default_factory=dict)
    as_of: datetime
