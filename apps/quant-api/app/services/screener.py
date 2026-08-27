from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import Price, Stock
from app.schemas.screener import ScreenerItem, ScreenerRequest, ScreenerResponse
from app.services.fundamental import get_latest_fundamental
from app.services.market_data import pagination_meta
from app.services.quant import compute_stock_quant_score
from app.services.technical import calculate_technical_analysis


def screen_stocks(db: Session, req: ScreenerRequest) -> ScreenerResponse:
    # 1. Fetch eligible stocks base query
    stmt = select(Stock)
    if req.search:
        pattern = f"%{req.search.strip()}%"
        stmt = stmt.where(Stock.symbol.ilike(pattern) | Stock.name.ilike(pattern))
    if req.sector:
        stmt = stmt.where(Stock.sector.ilike(f"%{req.sector.strip()}%"))
    if req.min_market_cap is not None:
        stmt = stmt.where(Stock.market_cap >= req.min_market_cap)
    if req.max_market_cap is not None:
        stmt = stmt.where(Stock.market_cap <= req.max_market_cap)

    stocks = list(db.scalars(stmt))

    # 2. Enrich with technical, fundamental, quant scores
    enriched: list[ScreenerItem] = []
    for stock in stocks:
        tech = calculate_technical_analysis(db, stock, interval="1d")
        fund = get_latest_fundamental(db, stock)
        quant = compute_stock_quant_score(db, stock, technical=tech)

        # Filter criteria
        if req.min_score is not None and quant.total_score < req.min_score:
            continue
        if req.max_score is not None and quant.total_score > req.max_score:
            continue

        pe = fund.ratios.pe_ratio if fund else None
        if req.min_pe is not None and (pe is None or pe < req.min_pe):
            continue
        if req.max_pe is not None and (pe is None or pe > req.max_pe):
            continue

        pb = fund.ratios.pb_ratio if fund else None
        if req.min_pb is not None and (pb is None or pb < req.min_pb):
            continue
        if req.max_pb is not None and (pb is None or pb > req.max_pb):
            continue

        roe = fund.ratios.roe if fund else None
        if req.min_roe is not None and (roe is None or roe < req.min_roe):
            continue

        rsi_val = tech.rsi
        if req.min_rsi is not None and (rsi_val is None or rsi_val < req.min_rsi):
            continue
        if req.max_rsi is not None and (rsi_val is None or rsi_val > req.max_rsi):
            continue

        latest_price = db.scalar(
            select(Price)
            .where(Price.stock_id == stock.id, Price.interval == "1d")
            .order_by(Price.time.desc())
            .limit(1)
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
                quant_score=quant.total_score,
                score_version=quant.score_version,
                data_source=latest_price.source if latest_price is not None else None,
                # price_as_of = market observation time of THIS item's latest close.
                price_as_of=latest_price.time if latest_price is not None else None,
                # as_of kept for backward compat. Will be deprecated.
                as_of=latest_price.time if latest_price is not None else quant.as_of,
                pe_ratio=pe,
                pb_ratio=pb,
                roe=roe,
                rsi=rsi_val,
                trend=tech.trend,
            )
        )

    # 3. Sort
    reverse = req.sort_order == "desc"

    def sort_key(item: ScreenerItem):
        val = getattr(item, req.sort_by if req.sort_by != "score" else "quant_score")
        if val is None:
            return float("-inf") if reverse else float("inf")
        return val

    enriched.sort(key=sort_key, reverse=reverse)

    total = len(enriched)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size
    page_items = enriched[start:end]

    meta = pagination_meta(req.page, req.page_size, total)

    # Determine data_lag: if any item is backed by yfinance, declare eod_1d.
    data_lag: str | None = None
    if any(item.data_source == "yfinance" for item in page_items):
        data_lag = "eod_1d"

    return ScreenerResponse(
        items=page_items,
        pagination=meta,
        as_of=datetime.now(UTC),
        data_lag=data_lag,
    )
