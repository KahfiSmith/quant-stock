"""Scanner endpoints: pre-configured screener filters for swing/scalping strategies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import success
from app.schemas.screener import ScreenerRequest, ScreenerResponse
from app.services.screener import screen_stocks

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])


@router.get("/swing", response_model=None)
def scan_swing_breakout(
    sector: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Swing breakout scanner: volume spike + price breakout + momentum signals."""
    req = ScreenerRequest(
        exchange="IDX",
        sector=sector,
        strategy_preset="swing_breakout",
        min_volume_zscore=1.5,
        sort_by="volume_zscore",
        sort_order="desc",
        page=page,
        page_size=page_size,
    )
    result: ScreenerResponse = screen_stocks(db, req)
    return success(result.model_dump(mode="json"), "Swing breakout scan complete")


@router.get("/scalping", response_model=None)
def scan_scalping_goreng(
    sector: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Scalping/gorengan scanner: extreme volume + oversold bounce + accumulation."""
    req = ScreenerRequest(
        exchange="IDX",
        sector=sector,
        strategy_preset="scalping_goreng",
        min_volume_zscore=2.0,
        sort_by="volume_zscore",
        sort_order="desc",
        page=page,
        page_size=page_size,
    )
    result: ScreenerResponse = screen_stocks(db, req)
    return success(result.model_dump(mode="json"), "Scalping scan complete")


@router.get("/accumulation", response_model=None)
def scan_foreign_accumulation(
    sector: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Foreign accumulation scanner: foreigners buying while price is flat/down."""
    req = ScreenerRequest(
        exchange="IDX",
        sector=sector,
        strategy_preset="none",
        sort_by="conviction_score",
        sort_order="desc",
        page=page,
        page_size=page_size,
    )
    result: ScreenerResponse = screen_stocks(db, req)

    filtered_items = [
        item for item in result.items
        if item.flow_signal in ("STRONG_ACCUMULATION", "ACCUMULATION")
    ]
    result.items = filtered_items
    result.pagination.total = len(filtered_items)
    result.pagination.total_pages = max(1, -(-len(filtered_items) // page_size))

    return success(result.model_dump(mode="json"), "Foreign accumulation scan complete")


@router.get("/oversold-bounce", response_model=None)
def scan_oversold_bounce(
    sector: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Oversold bounce scanner: MFI/RSI oversold + volume starting to enter."""
    req = ScreenerRequest(
        exchange="IDX",
        sector=sector,
        strategy_preset="mean_reversion",
        max_rsi=35.0,
        sort_by="momentum_1m",
        sort_order="asc",
        page=page,
        page_size=page_size,
    )
    result: ScreenerResponse = screen_stocks(db, req)
    return success(result.model_dump(mode="json"), "Oversold bounce scan complete")
