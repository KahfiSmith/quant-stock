from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import Price, Stock
from app.schemas.technical import (
    BollingerResponse,
    DrawdownProfile,
    IndicatorsSummary,
    MacdResponse,
    MomentumProfile,
    RiskMetrics,
    TechnicalAnalysisResponse,
)
from app.technical.indicators import (
    atr,
    atr_percent,
    bollinger,
    bollinger_zscore,
    calmar_ratio,
    macd,
    max_drawdown,
    multi_timeframe_momentum,
    rsi,
    sharpe_ratio,
    sma,
    sortino_ratio,
    volatility_regime,
    volume_sma_ratio,
    volume_zscore,
)


def calculate_technical_analysis(
    db: Session,
    stock: Stock,
    interval: str = "1d",
    limit: int = 250,
) -> TechnicalAnalysisResponse:

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
            data_source=None,
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
    volumes = [float(p.volume) for p in prices if p.volume is not None]

    ma20_series = sma(closes, 20)
    ma50_series = sma(closes, 50)
    ma200_series = sma(closes, 200)
    rsi_series = rsi(closes, 14)
    atr_series = atr(highs, lows, closes, 14)
    macd_line, macd_signal, macd_hist = macd(closes)
    bb_mid, bb_upper, bb_lower = bollinger(closes, 20, 2)

    has_volume = len(volumes) == len(closes) and any(v > 0 for v in volumes)
    vol_zscore_series = volume_zscore(volumes, 20) if has_volume else [None] * len(closes)
    vol_sma_ratio_series = volume_sma_ratio(volumes, 20) if has_volume else [None] * len(closes)
    atr_pct_series = atr_percent(highs, lows, closes, 14)

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

    latest_vol_zscore = vol_zscore_series[-1]
    latest_vol_sma_ratio = vol_sma_ratio_series[-1]
    latest_atr_pct = atr_pct_series[-1]
    latest_vol_regime = volatility_regime(latest_atr_pct)

    mom = multi_timeframe_momentum(closes)
    bb_z = bollinger_zscore(closes, 20)
    mdd, current_dd = max_drawdown(closes)
    sr = sharpe_ratio(closes)
    so = sortino_ratio(closes)
    cr = calmar_ratio(closes)


    if latest_ma50 is not None and latest_ma200 is not None:
        trend = "bullish" if latest_ma50 > latest_ma200 else "bearish"
    elif latest_ma20 is not None and latest_close is not None:
        trend = "bullish" if latest_close > latest_ma20 else "bearish"
    else:
        trend = "neutral"


    if latest_ma20 is not None and latest_close > latest_ma20:
        ma_signal = "positive"
    elif latest_ma20 is not None and latest_close < latest_ma20:
        ma_signal = "negative"
    else:
        ma_signal = "neutral"

    return TechnicalAnalysisResponse(
        symbol=stock.symbol,
        interval=interval,
        data_source=prices[-1].source,
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
            atr_percent=round(latest_atr_pct, 2) if latest_atr_pct is not None else None,
            volatility_regime=latest_vol_regime,
            volume_zscore=round(latest_vol_zscore, 2) if latest_vol_zscore is not None else None,
            volume_sma_ratio=round(latest_vol_sma_ratio, 2) if latest_vol_sma_ratio is not None else None,
            bollinger_zscore=round(bb_z, 2) if bb_z is not None else None,
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
            momentum=MomentumProfile(
                mom_1m=round(mom["mom_1m"], 2) if mom["mom_1m"] is not None else None,
                mom_3m=round(mom["mom_3m"], 2) if mom["mom_3m"] is not None else None,
                mom_6m=round(mom["mom_6m"], 2) if mom["mom_6m"] is not None else None,
                mom_12m=round(mom["mom_12m"], 2) if mom["mom_12m"] is not None else None,
            ),
            drawdown=DrawdownProfile(
                max_drawdown_pct=mdd,
                current_drawdown_pct=current_dd,
            ),
            risk_metrics=RiskMetrics(
                sharpe_ratio=round(sr, 2) if sr is not None else None,
                sortino_ratio=round(so, 2) if so is not None else None,
                calmar_ratio=round(cr, 2) if cr is not None else None,
            ),
        ),
    )
