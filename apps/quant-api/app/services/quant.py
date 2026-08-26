from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fundamental import Fundamental
from app.models.market_data import Price, Stock
from app.quant.scoring import calculate_quant_score
from app.schemas.quant import QuantFactors, QuantScoreResponse
from app.services.technical import calculate_technical_analysis


def compute_stock_quant_score(db: Session, stock: Stock) -> QuantScoreResponse:
    tech = calculate_technical_analysis(db, stock, interval="1d")

    # Get latest candle for ATR ratio
    latest_candle = db.scalar(
        select(Price)
        .where(Price.stock_id == stock.id, Price.interval == "1d")
        .order_by(Price.time.desc())
        .limit(1)
    )

    atr_ratio = None
    if latest_candle and tech.indicators.atr14 and latest_candle.close > 0:
        atr_ratio = tech.indicators.atr14 / float(latest_candle.close)

    # Get latest fundamental data
    fund = db.scalar(
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.period_end.desc())
        .limit(1)
    )

    roe = float(fund.roe) if fund and fund.roe is not None else None
    roa = float(fund.roa) if fund and fund.roa is not None else None
    de = float(fund.debt_to_equity) if fund and fund.debt_to_equity is not None else None
    pe = float(fund.pe_ratio) if fund and fund.pe_ratio is not None else None
    pb = float(fund.pb_ratio) if fund and fund.pb_ratio is not None else None
    rev_g = float(fund.revenue_growth) if fund and fund.revenue_growth is not None else None
    eps_g = float(fund.eps_growth) if fund and fund.eps_growth is not None else None

    factors = calculate_quant_score(
        rsi_val=tech.rsi,
        trend=tech.trend,
        roe=roe,
        roa=roa,
        debt_to_equity=de,
        pe_ratio=pe,
        pb_ratio=pb,
        atr_ratio=atr_ratio,
        revenue_growth=rev_g,
        eps_growth=eps_g,
    )

    return QuantScoreResponse(
        symbol=stock.symbol,
        as_of=datetime.now(UTC),
        score_version="v1",
        total_score=factors.total_score,
        factors=QuantFactors(
            momentum=factors.momentum,
            quality=factors.quality,
            value=factors.value,
            risk=factors.risk,
            growth=factors.growth,
        ),
        data_quality=factors.data_quality,
    )
