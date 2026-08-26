from datetime import datetime

from pydantic import BaseModel


class QuantFactors(BaseModel):
    momentum: float
    quality: float
    value: float
    risk: float
    growth: float


class QuantScoreResponse(BaseModel):
    symbol: str
    as_of: datetime
    score_version: str = "v1"
    total_score: float
    factors: QuantFactors
    data_quality: str
