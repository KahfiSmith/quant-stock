from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreatePortfolioRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    currency: str = Field(default="IDR", max_length=8)


class CreateTransactionRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    transaction_type: Literal["BUY", "SELL"]
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    fee: float = Field(default=0.0, ge=0)
    transacted_at: datetime | None = None


class UpdatePortfolioRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=255)
    currency: str | None = Field(default=None, min_length=1, max_length=8)


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    portfolio_id: int
    stock_id: int
    symbol: str
    transaction_type: str
    quantity: float
    price: float
    fee: float
    transacted_at: datetime


class HoldingResponse(BaseModel):
    stock_id: int
    symbol: str
    name: str
    quantity: float
    avg_buy_price: float
    current_price: float | None = None
    current_value: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_percent: float | None = None

    price_as_of: datetime | None = None
    data_source: str | None = None
    data_lag: str | None = None


class PortfolioRiskResponse(BaseModel):
    annualized_volatility_percent: float
    max_holding_concentration_percent: float
    observations: int


class PortfolioDetailResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    currency: str
    total_cost: float
    current_value: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    holdings: list[HoldingResponse]
    transactions: list[TransactionResponse] = Field(default_factory=list)
    risk: PortfolioRiskResponse

    as_of: datetime = Field(
        description="Wall-clock time of the response. NOT data freshness.",
    )


    price_as_of: datetime | None = None
    data_lag: str | None = None
    created_at: datetime
    updated_at: datetime


class PortfolioSummaryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    currency: str
    created_at: datetime
    updated_at: datetime
