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


class MomentumProfile(BaseModel):
    mom_1m: float | None = None
    mom_3m: float | None = None
    mom_6m: float | None = None
    mom_12m: float | None = None


class DrawdownProfile(BaseModel):
    max_drawdown_pct: float | None = None
    current_drawdown_pct: float | None = None


class RiskMetrics(BaseModel):
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    calmar_ratio: float | None = None


class IndicatorsSummary(BaseModel):
    ma20: float | None = None
    ma50: float | None = None
    ma200: float | None = None
    rsi14: float | None = None
    atr14: float | None = None
    atr_percent: float | None = None
    volatility_regime: str | None = None
    volume_zscore: float | None = None
    volume_sma_ratio: float | None = None
    bollinger_zscore: float | None = None
    adx: float | None = None
    mfi: float | None = None
    stochastic_rsi: float | None = None
    obv_trend_pct: float | None = None
    support_distance_pct: float | None = None
    resistance_distance_pct: float | None = None
    earnings_yield: float | None = None
    macd: MacdResponse
    bollinger: BollingerResponse
    momentum: MomentumProfile = MomentumProfile()
    drawdown: DrawdownProfile = DrawdownProfile()
    risk_metrics: RiskMetrics = RiskMetrics()


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    interval: str
    data_source: str | None = None
    as_of: datetime
    trend: str
    rsi: float | None
    ma_signal: str
    indicators: IndicatorsSummary
