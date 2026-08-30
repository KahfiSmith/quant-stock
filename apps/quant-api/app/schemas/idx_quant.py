"""Pydantic schemas for IDX Quant Platform & Factor Rotation Engine."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class IDXStockUniverseItem(BaseModel):
    id: int
    symbol: str
    name: str
    sector: str | None = None
    sub_sector: str | None = None
    listing_date: date | None = None
    market_cap: float | None = None
    liquidity_status: str = "liquid"
    is_active: bool = True
    board: str | None = "MAIN"
    avg_daily_turnover_20d: float | None = None
    avg_daily_frequency_20d: float | None = None
    exchange: str = "IDX"
    currency: str = "IDR"
    close_price: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    roa: float | None = None
    quant_score: float | None = None
    composite_rank: int | None = None
    percentile: float | None = None


class IDXMarketFlowItem(BaseModel):
    date: date
    foreign_buy_value: float
    foreign_sell_value: float
    net_foreign_value: float
    foreign_buy_volume: float
    foreign_sell_volume: float
    top3_buyer_broker_val: float | None = None
    top3_seller_broker_val: float | None = None


class IDXCorporateActionItem(BaseModel):
    action_type: str
    cum_date: date | None = None
    ex_date: date
    recording_date: date | None = None
    payment_date: date | None = None
    ratio_from: float | None = None
    ratio_to: float | None = None
    cash_amount: float | None = None
    exercise_price: float | None = None


class IDXStockDetailResponse(BaseModel):
    stock: IDXStockUniverseItem
    market_flows: list[IDXMarketFlowItem]
    corporate_actions: list[IDXCorporateActionItem]
    as_of: datetime


class IDXFactorRotationRequest(BaseModel):
    strategy_name: str = Field(default="IDX Top 10 Multi-Factor Rotation", min_length=2, max_length=128)
    initial_capital: float = Field(default=500_000_000.0, gt=1_000_000.0)
    top_n: int = Field(default=10, ge=1, le=50)
    rebalance_frequency: Literal["monthly", "quarterly"] = "monthly"
    start_date: date | None = None
    end_date: date | None = None
    min_market_cap: float = Field(default=1_000_000_000_000.0, ge=0.0)
    min_adv_turnover: float = Field(default=5_000_000_000.0, ge=0.0)
    min_frequency: float = Field(default=1_000.0, ge=0.0)
    sector_filter: str | None = None
    factor_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "momentum": 0.30,
            "quality": 0.25,
            "value": 0.20,
            "risk": 0.15,
            "growth": 0.10,
        }
    )
    fee_percent: float = Field(default=0.0015, ge=0.0, le=0.05)
    slippage_percent: float = Field(default=0.001, ge=0.0, le=0.05)


class IDXRotationEquityPoint(BaseModel):
    date: str
    equity: float
    benchmark: float
    drawdown: float


class IDXRotationRebalanceEvent(BaseModel):
    date: str
    selected_symbols: list[str]
    portfolio_value: float
    cash_reserve: float


class IDXRotationSummary(BaseModel):
    total_return_pct: float
    cagr_pct: float
    benchmark_return_pct: float
    alpha_pct: float
    beta: float
    sharpe_ratio: float
    max_drawdown_pct: float
    annualized_volatility_pct: float
    final_equity: float
    rebalance_count: int


class IDXFactorRotationResponse(BaseModel):
    run_id: str
    strategy_name: str
    initial_capital: float
    start_date: date
    end_date: date
    summary: IDXRotationSummary
    equity_curve: list[IDXRotationEquityPoint]
    rebalance_history: list[IDXRotationRebalanceEvent]
    benchmark_name: str = "IHSG (^JKSE)"
    as_of: datetime
