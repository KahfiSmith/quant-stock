from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import Price, Stock
from app.schemas.technical import (
    BollingerResponse,
    IndicatorsSummary,
    MacdResponse,
    TechnicalAnalysisResponse,
)
from app.technical.indicators import atr, bollinger, macd, rsi, sma


def calculate_technical_analysis(
    db: Session,
    stock: Stock,
    interval: str = "1d",
    limit: int = 250,
) -> TechnicalAnalysisResponse:
    # Fetch price history ordered by time ASC
    prices = list(
        db.scalars(
            select(Price)
            .where(
                Price.stock_id == stock.id,
                Price.interval == interval,
            )
            .order_by(Price.time.desc())
            .limit(limit)
        )
    )
    prices.reverse()

    if not prices:
        return TechnicalAnalysisResponse(
            symbol=stock.symbol,
            interval=interval,
            as_of=datetime.now(UTC),
            trend="neutral",
            rsi=None,
            ma_signal="neutral",
            indicators=IndicatorsSummary(
                macd=MacdResponse(),
                bollinger=BollingerResponse(),
            ),
        )

    closes = [float(p.close) for p in prices]
    highs = [float(p.high) for p in prices]
    lows = [float(p.low) for p in prices]

    ma20_series = sma(closes, 20)
    ma50_series = sma(closes, 50)
    ma200_series = sma(closes, 200)
    rsi_series = rsi(closes, 14)
    atr_series = atr(highs, lows, closes, 14)
    macd_line, macd_signal, macd_hist = macd(closes)
    bb_mid, bb_upper, bb_lower = bollinger(closes, 20, 2)

    latest_close = closes[-1]
    latest_ma20 = ma20_series[-1]
    latest_ma50 = ma50_series[-1]
    latest_ma200 = ma200_series[-1]
    latest_rsi = rsi_series[-1]
    latest_atr = atr_series[-1]

    latest_macd_line = macd_line[-1]
    latest_macd_sig = macd_signal[-1]
    latest_macd_hist = macd_hist[-1]

    latest_bb_mid = bb_mid[-1]
    latest_bb_upper = bb_upper[-1]
    latest_bb_lower = bb_lower[-1]

    # Trend logic
    if latest_ma50 is not None and latest_ma200 is not None:
        trend = "bullish" if latest_ma50 > latest_ma200 else "bearish"
    elif latest_ma20 is not None and latest_close is not None:
        trend = "bullish" if latest_close > latest_ma20 else "bearish"
    else:
        trend = "neutral"

    # MA Signal logic
    if latest_ma20 is not None and latest_close > latest_ma20:
        ma_signal = "positive"
    elif latest_ma20 is not None and latest_close < latest_ma20:
        ma_signal = "negative"
    else:
        ma_signal = "neutral"

    return TechnicalAnalysisResponse(
        symbol=stock.symbol,
        interval=interval,
        as_of=prices[-1].time if prices else datetime.now(UTC),
        trend=trend,
        rsi=round(latest_rsi, 2) if latest_rsi is not None else None,
        ma_signal=ma_signal,
        indicators=IndicatorsSummary(
            ma20=round(latest_ma20, 2) if latest_ma20 is not None else None,
            ma50=round(latest_ma50, 2) if latest_ma50 is not None else None,
            ma200=round(latest_ma200, 2) if latest_ma200 is not None else None,
            rsi14=round(latest_rsi, 2) if latest_rsi is not None else None,
            atr14=round(latest_atr, 2) if latest_atr is not None else None,
            macd=MacdResponse(
                line=round(latest_macd_line, 2) if latest_macd_line is not None else None,
                signal=round(latest_macd_sig, 2) if latest_macd_sig is not None else None,
                histogram=round(latest_macd_hist, 2) if latest_macd_hist is not None else None,
            ),
            bollinger=BollingerResponse(
                middle=round(latest_bb_mid, 2) if latest_bb_mid is not None else None,
                upper=round(latest_bb_upper, 2) if latest_bb_upper is not None else None,
                lower=round(latest_bb_lower, 2) if latest_bb_lower is not None else None,
            ),
        ),
    )
