from datetime import datetime

from pydantic import BaseModel


class BollingerResponse(BaseModel):
    middle: float | None = None
    upper: float | None = None
    lower: float | None = None


class MacdResponse(BaseModel):
    line: float | None = None
    signal: float | None = None
    histogram: float | None = None


class IndicatorsSummary(BaseModel):
    ma20: float | None = None
    ma50: float | None = None
    ma200: float | None = None
    rsi14: float | None = None
    atr14: float | None = None
    macd: MacdResponse
    bollinger: BollingerResponse


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    interval: str
    data_source: str | None = None
    as_of: datetime
    trend: str
    rsi: float | None
    ma_signal: str
    indicators: IndicatorsSummary
