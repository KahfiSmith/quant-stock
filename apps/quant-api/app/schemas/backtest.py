from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

StrategyType = Literal["SMA_CROSSOVER", "RSI_MOMENTUM", "BUY_AND_HOLD"]


class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    strategy: StrategyType = "SMA_CROSSOVER"
    initial_capital: float = Field(default=100_000_000.0, gt=0)
    fast_period: int = Field(default=20, ge=2, le=200)
    slow_period: int = Field(default=50, ge=5, le=500)
    rsi_oversold: float = Field(default=30.0, ge=0, le=100)
    rsi_overbought: float = Field(default=70.0, ge=0, le=100)
    start_date: date | None = None
    end_date: date | None = None
    fee_percent: float = Field(default=0.0015, ge=0, le=0.05)
    slippage_percent: float = Field(default=0.0, ge=0, le=0.05)

    @model_validator(mode="after")
    def validate_ranges(self) -> "BacktestRequest":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if self.rsi_oversold >= self.rsi_overbought:
            raise ValueError("rsi_oversold must be less than rsi_overbought")
        return self


class EquityPoint(BaseModel):
    time: str
    equity: float
    benchmark: float
    drawdown: float


class BacktestSummary(BaseModel):
    total_return_pct: float
    cagr_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    total_trades: int
    win_rate_pct: float
    final_equity: float


class BacktestMetadata(BaseModel):
    run_id: str
    status: Literal["succeeded"]
    status_history: list[Literal["queued", "running", "succeeded", "failed"]]
    retry_policy: str
    dataset_id: str
    dataset_version: str
    strategy_id: str
    strategy_version: str
    requested_start_date: date | None
    requested_end_date: date | None
    effective_start_date: date
    effective_end_date: date
    warmup_bars: int
    evaluation_bars: int
    universe: list[str]
    execution_price: str
    fee_percent: float
    slippage_percent: float
    initial_cash: float
    cash_policy: str
    lot_rounding: str
    corporate_action_policy: str
    benchmark: str
    risk_free_rate: float
    last_data_timestamp: datetime


class BacktestResponse(BaseModel):
    symbol: str
    strategy: str
    initial_capital: float
    summary: BacktestSummary
    equity_curve: list[EquityPoint]
    metadata: BacktestMetadata
    as_of: datetime
