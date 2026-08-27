from datetime import date, datetime

from pydantic import BaseModel


class QuantFactors(BaseModel):
    momentum: float
    quality: float
    value: float
    risk: float
    growth: float


class QuantUniverse(BaseModel):
    identifier: str
    size: int


class QuantMetadata(BaseModel):
    model_version: str
    methodology_version: str
    raw_inputs: dict[str, float | None]
    missing_inputs: list[str]
    weights: dict[str, float]
    normalization: dict[str, str]
    reason_codes: list[str]
    comparison_universe: QuantUniverse
    technical_as_of: datetime | None = None
    fundamental_period_end: date | None = None
    fundamental_published_at: datetime | None = None
    price_as_of: datetime | None = None


class QuantScoreResponse(BaseModel):
    symbol: str
    as_of: datetime
    score_version: str = "v1"
    total_score: float
    factors: QuantFactors
    data_quality: str
    metadata: QuantMetadata
