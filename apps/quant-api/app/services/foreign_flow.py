from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.idx_models import MarketFlowIDX
from app.models.market_data import Price, Stock
from app.quant.foreign_flow import (
    classify_flow_signal,
    flow_divergence,
    flow_intensity,
    flow_momentum,
    flow_streak,
    net_flow_rolling_sum,
)
from app.schemas.idx_quant import ForeignFlowAnalysis


def compute_foreign_flow_analysis(
    db: Session,
    stock: Stock,
    limit: int = 60,
) -> ForeignFlowAnalysis:

    flows = list(
        db.scalars(
            select(MarketFlowIDX)
            .where(MarketFlowIDX.stock_id == stock.id)
            .order_by(MarketFlowIDX.date.desc())
            .limit(limit)
        )
    )
    flows.reverse()

    if not flows:
        return ForeignFlowAnalysis(
            symbol=stock.symbol,
            signal="NEUTRAL",
            data_days=0,
            as_of=datetime.now(UTC),
        )

    net_values = [float(f.net_foreign_value) for f in flows]
    buy_values = [float(f.foreign_buy_value) for f in flows]
    sell_values = [float(f.foreign_sell_value) for f in flows]

    prices = list(
        db.scalars(
            select(Price)
            .where(Price.stock_id == stock.id, Price.interval == "1d")
            .order_by(Price.time.desc())
            .limit(limit)
        )
    )
    prices.reverse()
    closes = [float(p.close) for p in prices]
    volumes = [float(p.volume) for p in prices if p.volume is not None]

    rolling_5d = net_flow_rolling_sum(net_values, 5)
    rolling_10d = net_flow_rolling_sum(net_values, 10)
    rolling_20d = net_flow_rolling_sum(net_values, 20)

    streak = flow_streak(net_values)
    momentum = flow_momentum(net_values, short=5, long=20)
    intensity = flow_intensity(net_values, volumes, period=20) if len(volumes) >= 20 else None
    divergence = flow_divergence(net_values, closes, period=10) if len(closes) >= 10 else None

    signal = classify_flow_signal(
        net_5d=rolling_5d[-1] if rolling_5d[-1] is not None else None,
        net_20d=rolling_20d[-1] if rolling_20d[-1] is not None else None,
        streak=streak,
        momentum=momentum,
    )

    latest = flows[-1]
    return ForeignFlowAnalysis(
        symbol=stock.symbol,
        signal=signal,
        net_flow_5d=_r(rolling_5d[-1]),
        net_flow_10d=_r(rolling_10d[-1]),
        net_flow_20d=_r(rolling_20d[-1]),
        streak_days=streak,
        flow_momentum=round(momentum, 2) if momentum is not None else None,
        flow_intensity_pct=round(intensity, 2) if intensity is not None else None,
        divergence=divergence,
        latest_net_foreign=float(latest.net_foreign_value),
        latest_foreign_buy=float(latest.foreign_buy_value),
        latest_foreign_sell=float(latest.foreign_sell_value),
        data_days=len(flows),
        as_of=datetime.now(UTC),
    )


def _r(val: float | None) -> float | None:
    return round(val, 2) if val is not None else None
