from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import Price, Stock
from app.quant.scoring import calculate_quant_score
from app.quant.signals import generate_quant_signal
from app.schemas.screener import ScreenerItem, ScreenerRequest, ScreenerResponse
from app.services.fundamental import get_latest_fundamental
from app.services.market_data import pagination_meta
from app.services.technical import calculate_technical_analysis


def screen_stocks(db: Session, req: ScreenerRequest) -> ScreenerResponse:

    stmt = select(Stock)
    if req.search:
        pattern = f"%{req.search.strip()}%"
        stmt = stmt.where(Stock.symbol.ilike(pattern) | Stock.name.ilike(pattern))
    if req.exchange:
        stmt = stmt.where(Stock.exchange == req.exchange.strip().upper())
    if req.sector:
        stmt = stmt.where(Stock.sector.ilike(f"%{req.sector.strip()}%"))
    if req.min_market_cap is not None:
        stmt = stmt.where(Stock.market_cap >= req.min_market_cap)
    if req.max_market_cap is not None:
        stmt = stmt.where(Stock.market_cap <= req.max_market_cap)

    stocks = list(db.scalars(stmt))


    min_roe = req.min_roe
    min_score = req.min_score
    min_rsi = req.min_rsi
    max_rsi = req.max_rsi
    max_pe = req.max_pe
    max_pb = req.max_pb

    custom_weights = req.custom_weights.model_dump() if req.custom_weights else None

    if req.strategy_preset == "quality_momentum":
        min_roe = min_roe or 0.15
        custom_weights = {"momentum": 0.40, "quality": 0.40, "value": 0.10, "risk": 0.05, "growth": 0.05}
    elif req.strategy_preset == "deep_value":
        max_pe = max_pe or 15.0
        max_pb = max_pb or 2.0
        custom_weights = {"value": 0.50, "quality": 0.25, "momentum": 0.10, "risk": 0.10, "growth": 0.05}
    elif req.strategy_preset == "garp":
        min_roe = min_roe or 0.12
        custom_weights = {"growth": 0.35, "quality": 0.25, "value": 0.25, "momentum": 0.10, "risk": 0.05}
    elif req.strategy_preset == "defensive_income":
        max_pe = max_pe or 16.0
        custom_weights = {"quality": 0.35, "risk": 0.35, "value": 0.20, "growth": 0.05, "momentum": 0.05}


    enriched: list[ScreenerItem] = []
    for stock in stocks:
        tech = calculate_technical_analysis(db, stock, interval="1d")
        fund = get_latest_fundamental(db, stock)


        latest_price = db.scalar(
            select(Price)
            .where(Price.stock_id == stock.id, Price.interval == "1d")
            .order_by(Price.time.desc())
            .limit(1)
        )

        atr_ratio = None
        if latest_price and tech.indicators.atr14 and latest_price.close > 0:
            atr_ratio = tech.indicators.atr14 / float(latest_price.close)

        pe = fund.ratios.pe_ratio if fund else None
        pb = fund.ratios.pb_ratio if fund else None
        roe = fund.ratios.roe if fund else None
        roa = fund.ratios.roa if fund else None
        de = fund.ratios.debt_to_equity if fund else None
        rev_g = fund.ratios.revenue_growth if fund else None
        eps_g = fund.ratios.eps_growth if fund else None

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
            custom_weights=custom_weights,
        )


        if min_score is not None and factors.total_score < min_score:
            continue
        if req.max_score is not None and factors.total_score > req.max_score:
            continue
        if req.min_pe is not None and (pe is None or pe < req.min_pe):
            continue
        if max_pe is not None and (pe is None or pe > max_pe):
            continue
        if req.min_pb is not None and (pb is None or pb < req.min_pb):
            continue
        if max_pb is not None and (pb is None or pb > max_pb):
            continue
        if min_roe is not None and (roe is None or roe < min_roe):
            continue

        rsi_val = tech.rsi
        if min_rsi is not None and (rsi_val is None or rsi_val < min_rsi):
            continue
        if max_rsi is not None and (rsi_val is None or rsi_val > max_rsi):
            continue


        decision = generate_quant_signal(
            total_score=factors.total_score,
            momentum_score=factors.momentum,
            quality_score=factors.quality,
            value_score=factors.value,
            growth_score=factors.growth,
            risk_score=factors.risk,
            trend=tech.trend,
            pe_ratio=pe,
            roe=roe,
            debt_to_equity=de,
        )

        enriched.append(
            ScreenerItem(
                id=stock.id,
                symbol=stock.symbol,
                name=stock.name,
                sector=stock.sector,
                market_cap=float(stock.market_cap) if stock.market_cap is not None else None,
                currency=stock.currency,
                close_price=float(latest_price.close) if latest_price is not None else None,
                quant_score=factors.total_score,
                score_version="v1",
                data_source=latest_price.source if latest_price is not None else None,
                price_as_of=latest_price.time if latest_price is not None else None,
                as_of=latest_price.time if latest_price is not None else datetime.now(UTC),
                pe_ratio=pe,
                pb_ratio=pb,
                roe=roe,
                rsi=rsi_val,
                trend=tech.trend,
                signal=decision.signal,
                risk_level=decision.risk_level,
                signal_confidence_pct=decision.confidence_pct,
                signal_reasons=decision.reasons,
                value_score=factors.value,
                quality_score=factors.quality,
                momentum_score=factors.momentum,
                growth_score=factors.growth,
                risk_score=factors.risk,
            )
        )


    enriched.sort(key=lambda x: x.quant_score or 0.0, reverse=True)
    total_universe = len(enriched)
    for rank_idx, item in enumerate(enriched, start=1):
        item.composite_rank = rank_idx
        item.percentile = (
            round(((total_universe - rank_idx + 1) / total_universe) * 100.0, 1) if total_universe > 0 else 100.0
        )


    reverse = req.sort_order == "desc"

    def sort_key(item: ScreenerItem):
        field = req.sort_by
        if field == "score":
            val = item.quant_score
        else:
            val = getattr(item, field, None)
        if val is None:
            return float("-inf") if reverse else float("inf")
        return val

    if req.sort_by != "score" or req.sort_order != "desc":
        enriched.sort(key=sort_key, reverse=reverse)

    total = len(enriched)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size
    page_items = enriched[start:end]

    meta = pagination_meta(req.page, req.page_size, total)

    data_lag: str | None = None
    if any(item.data_source == "yfinance" for item in page_items):
        data_lag = "eod_1d"

    return ScreenerResponse(
        items=page_items,
        pagination=meta,
        as_of=datetime.now(UTC),
        data_lag=data_lag,
    )
