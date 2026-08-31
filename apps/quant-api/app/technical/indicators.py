"""Pure technical indicator calculations.

Formulas follow the standard conventions used by pandas-ta, but are implemented
here without the pandas-ta dependency (which is unmaintained and incompatible
with modern pandas/numpy versions). Values that lack enough lookback history are
reported as ``None`` and never faked as zero.
"""

from __future__ import annotations

Number = float | None


def sma(values: list[float], period: int) -> list[Number]:
    """Simple moving average; ``None`` until ``period`` values are available."""
    out: list[Number] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    window_sum = sum(values[:period])
    out[period - 1] = window_sum / period
    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        out[i] = window_sum / period
    return out


def ema(values: list[float], period: int) -> list[Number]:
    """Exponential moving average seeded with the first period's SMA."""
    out: list[Number] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    alpha = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(values)):
        out[i] = values[i] * alpha + out[i - 1] * (1 - alpha)  # type: ignore[operator]
    return out


def rsi(closes: list[float], period: int = 14) -> list[Number]:
    """Relative Strength Index with Wilder smoothing. Needs ``period + 1`` closes."""
    out: list[Number] = [None] * len(closes)
    if len(closes) < period + 1:
        return out

    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    if avg_loss == 0:
        out[period] = 100.0
    else:
        out[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            out[i + 1] = 100.0
        else:
            out[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


def true_range(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    trs: list[float] = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        trs.append(
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        )
    return trs


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[Number]:
    """Average True Range with Wilder smoothing. First value sits at index ``period - 1``."""
    out: list[Number] = [None] * len(closes)
    if len(closes) < period:
        return out
    trs = true_range(highs, lows, closes)
    seed = sum(trs[:period]) / period
    out[period - 1] = seed
    for i in range(period, len(closes)):
        out[i] = (out[i - 1] * (period - 1) + trs[i]) / period  # type: ignore[operator]
    return out


def macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[Number], list[Number], list[Number]]:
    """MACD line, signal line, and histogram. Values ``None`` before warm-up."""
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    line: list[Number] = [
        a - b if a is not None and b is not None else None
        for a, b in zip(fast_ema, slow_ema)
    ]

    start = slow - 1
    line_ready = [v for v in line[start:] if v is not None]
    smoothed = ema(line_ready, signal) if len(line_ready) >= signal else [None] * len(line_ready)

    signal_line: list[Number] = [None] * len(closes)
    cursor = 0
    for v in line[start:]:
        if v is not None:
            if cursor < len(smoothed):
                signal_line[start + cursor] = smoothed[cursor]
            cursor += 1

    histogram: list[Number] = [
        a - b if a is not None and b is not None else None
        for a, b in zip(line, signal_line)
    ]
    return line, signal_line, histogram


def bollinger(
    closes: list[float],
    period: int = 20,
    num_std: int = 2,
) -> tuple[list[Number], list[Number], list[Number]]:
    """Bollinger bands: SMA middle band plus/minus ``num_std`` standard deviations."""
    middle = sma(closes, period)
    upper: list[Number] = [None] * len(closes)
    lower: list[Number] = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1 : i + 1]
        mean = middle[i]
        variance = sum((x - mean) ** 2 for x in window) / period
        deviation = variance**0.5
        upper[i] = mean + num_std * deviation
        lower[i] = mean - num_std * deviation
    return middle, upper, lower


VolatilityRegimeType = str  # "LOW" | "NORMAL" | "HIGH" | "EXTREME"


def volume_zscore(volumes: list[float], period: int = 20) -> list[Number]:
    """Z-score of latest volume vs rolling mean/stddev over ``period`` bars."""
    out: list[Number] = [None] * len(volumes)
    if period <= 1 or len(volumes) < period:
        return out
    for i in range(period - 1, len(volumes)):
        window = volumes[i - period + 1 : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = variance**0.5
        out[i] = (volumes[i] - mean) / std if std > 0 else 0.0
    return out


def volume_sma_ratio(volumes: list[float], period: int = 20) -> list[Number]:
    """Ratio of current volume to its SMA — 1.0 means average, 2.0 means 2× average."""
    sma_series = sma(volumes, period)
    out: list[Number] = [None] * len(volumes)
    for i in range(len(volumes)):
        if sma_series[i] is not None and sma_series[i] > 0:
            out[i] = volumes[i] / sma_series[i]
    return out


def atr_percent(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[Number]:
    """ATR as a percentage of the close price — normalised volatility measure."""
    atr_series = atr(highs, lows, closes, period)
    out: list[Number] = [None] * len(closes)
    for i in range(len(closes)):
        if atr_series[i] is not None and closes[i] > 0:
            out[i] = (atr_series[i] / closes[i]) * 100.0
    return out


def volatility_regime(atr_pct_value: float | None) -> VolatilityRegimeType | None:
    """Classify volatility into a regime based on ATR% thresholds for IDX equities."""
    if atr_pct_value is None:
        return None
    if atr_pct_value < 1.5:
        return "LOW"
    if atr_pct_value < 3.0:
        return "NORMAL"
    if atr_pct_value < 5.0:
        return "HIGH"
    return "EXTREME"


def price_momentum(closes: list[float], period: int) -> Number:
    """Simple price return over ``period`` bars as a percentage."""
    if len(closes) < period + 1:
        return None
    old = closes[-(period + 1)]
    if old <= 0:
        return None
    return ((closes[-1] - old) / old) * 100.0


def multi_timeframe_momentum(
    closes: list[float],
) -> dict[str, Number]:
    """Returns 1M/3M/6M/12M price momentum (approx trading days)."""
    return {
        "mom_1m": price_momentum(closes, 21),
        "mom_3m": price_momentum(closes, 63),
        "mom_6m": price_momentum(closes, 126),
        "mom_12m": price_momentum(closes, 252),
    }


def bollinger_zscore(closes: list[float], period: int = 20) -> Number:
    """Z-score of latest close vs Bollinger mid — positive = above band center."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    mean = sum(window) / period
    variance = sum((x - mean) ** 2 for x in window) / period
    std = variance**0.5
    if std == 0:
        return 0.0
    return (closes[-1] - mean) / std


def max_drawdown(closes: list[float]) -> tuple[Number, Number]:
    """Returns (max_drawdown_pct, current_drawdown_pct) from the full series.

    Drawdown values are negative percentages (e.g. -15.3 means a 15.3% decline
    from peak). Returns (None, None) when the series is empty.
    """
    if not closes:
        return None, None
    peak = closes[0]
    worst = 0.0
    for price in closes:
        if price > peak:
            peak = price
        dd = ((price - peak) / peak) * 100.0 if peak > 0 else 0.0
        if dd < worst:
            worst = dd

    current_peak = max(closes)
    current_dd = ((closes[-1] - current_peak) / current_peak) * 100.0 if current_peak > 0 else 0.0
    return round(worst, 2), round(current_dd, 2)


def _daily_returns(closes: list[float]) -> list[float]:
    return [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] > 0
    ]


def sharpe_ratio(closes: list[float], risk_free_annual: float = 0.06) -> Number:
    """Annualised Sharpe ratio. ``risk_free_annual`` defaults to 6% (Indonesian SBI rate)."""
    rets = _daily_returns(closes)
    if len(rets) < 20:
        return None
    daily_rf = risk_free_annual / 252.0
    excess = [r - daily_rf for r in rets]
    mean_excess = sum(excess) / len(excess)
    variance = sum((r - mean_excess) ** 2 for r in excess) / len(excess)
    std = variance**0.5
    if std == 0:
        return None
    return (mean_excess / std) * (252**0.5)


def sortino_ratio(closes: list[float], risk_free_annual: float = 0.06) -> Number:
    """Annualised Sortino ratio — penalises downside volatility only."""
    rets = _daily_returns(closes)
    if len(rets) < 20:
        return None
    daily_rf = risk_free_annual / 252.0
    excess = [r - daily_rf for r in rets]
    mean_excess = sum(excess) / len(excess)
    downside = [r for r in excess if r < 0]
    if not downside:
        return None
    down_var = sum(r**2 for r in downside) / len(downside)
    down_std = down_var**0.5
    if down_std == 0:
        return None
    return (mean_excess / down_std) * (252**0.5)


def calmar_ratio(closes: list[float]) -> Number:
    """Calmar ratio: annualised return / abs(max drawdown)."""
    if len(closes) < 63:
        return None
    total_return = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0.0
    years = len(closes) / 252.0
    annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0
    mdd, _ = max_drawdown(closes)
    if mdd is None or mdd >= 0:
        return None
    return annual_return / (abs(mdd) / 100.0)


def adx(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[Number]:
    """Average Directional Index — measures trend strength regardless of direction.

    ADX > 25 = trending, > 50 = strong trend, < 20 = sideways/no trend.
    """
    n = len(closes)
    out: list[Number] = [None] * n
    if n < period * 2:
        return out

    plus_dm: list[float] = [0.0]
    minus_dm: list[float] = [0.0]
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)

    trs = true_range(highs, lows, closes)

    atr_s = sum(trs[:period]) / period
    plus_s = sum(plus_dm[:period]) / period
    minus_s = sum(minus_dm[:period]) / period

    dx_values: list[float] = []
    for i in range(period, n):
        atr_s = (atr_s * (period - 1) + trs[i]) / period
        plus_s = (plus_s * (period - 1) + plus_dm[i]) / period
        minus_s = (minus_s * (period - 1) + minus_dm[i]) / period

        plus_di = (plus_s / atr_s * 100.0) if atr_s > 0 else 0.0
        minus_di = (minus_s / atr_s * 100.0) if atr_s > 0 else 0.0
        di_sum = plus_di + minus_di
        dx = (abs(plus_di - minus_di) / di_sum * 100.0) if di_sum > 0 else 0.0
        dx_values.append(dx)

    if len(dx_values) < period:
        return out
    adx_val = sum(dx_values[:period]) / period
    out[period * 2 - 1] = adx_val
    for i in range(period, len(dx_values)):
        adx_val = (adx_val * (period - 1) + dx_values[i]) / period
        out[period + i] = adx_val
    return out


def obv(closes: list[float], volumes: list[float]) -> list[float]:
    """On-Balance Volume — cumulative volume weighted by price direction.

    Rising OBV with flat price = accumulation (smart money buying).
    Falling OBV with flat price = distribution (smart money selling).
    """
    if not closes or len(closes) != len(volumes):
        return []
    result = [volumes[0]]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            result.append(result[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            result.append(result[-1] - volumes[i])
        else:
            result.append(result[-1])
    return result


def obv_trend(closes: list[float], volumes: list[float], period: int = 20) -> Number:
    """OBV slope normalized: positive = accumulation, negative = distribution."""
    obv_series = obv(closes, volumes)
    if len(obv_series) < period:
        return None
    obv_now = obv_series[-1]
    obv_prev = obv_series[-period]
    if obv_prev == 0:
        return None
    return ((obv_now - obv_prev) / abs(obv_prev)) * 100.0


def mfi(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
    period: int = 14,
) -> list[Number]:
    """Money Flow Index — volume-weighted RSI. Overbought > 80, oversold < 20."""
    n = len(closes)
    out: list[Number] = [None] * n
    if n < period + 1 or len(volumes) != n:
        return out

    typical = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    raw_flow = [t * v for t, v in zip(typical, volumes)]

    for i in range(period, n):
        pos_flow = 0.0
        neg_flow = 0.0
        for j in range(i - period + 1, i + 1):
            if typical[j] > typical[j - 1]:
                pos_flow += raw_flow[j]
            elif typical[j] < typical[j - 1]:
                neg_flow += raw_flow[j]
        if neg_flow == 0:
            out[i] = 100.0
        else:
            ratio = pos_flow / neg_flow
            out[i] = 100.0 - (100.0 / (1.0 + ratio))
    return out


def stochastic_rsi(
    closes: list[float],
    rsi_period: int = 14,
    stoch_period: int = 14,
) -> list[Number]:
    """Stochastic RSI — RSI of RSI, normalized 0-100.

    < 20 = deeply oversold (buy zone), > 80 = deeply overbought (sell zone).
    More sensitive than regular RSI for timing entries.
    """
    rsi_values = rsi(closes, rsi_period)
    out: list[Number] = [None] * len(closes)

    valid_rsi = [(i, v) for i, v in enumerate(rsi_values) if v is not None]
    if len(valid_rsi) < stoch_period:
        return out

    for idx in range(stoch_period - 1, len(valid_rsi)):
        window = [valid_rsi[j][1] for j in range(idx - stoch_period + 1, idx + 1)]
        rsi_min = min(window)
        rsi_max = max(window)
        original_idx = valid_rsi[idx][0]
        if rsi_max == rsi_min:
            out[original_idx] = 50.0
        else:
            out[original_idx] = ((valid_rsi[idx][1] - rsi_min) / (rsi_max - rsi_min)) * 100.0
    return out


def support_resistance_proximity(
    closes: list[float],
    lows: list[float],
    highs: list[float],
    period: int = 20,
) -> tuple[Number, Number]:
    """Returns (support_distance_pct, resistance_distance_pct).

    Support = lowest low over period. Resistance = highest high over period.
    Distance as percentage from current close. Negative support_distance = below support.
    Small positive support_distance (0-3%) = near support = good entry point.
    """
    if len(closes) < period:
        return None, None
    recent_lows = lows[-period:]
    recent_highs = highs[-period:]
    support = min(recent_lows)
    resistance = max(recent_highs)
    current = closes[-1]
    if current <= 0:
        return None, None
    support_dist = ((current - support) / current) * 100.0
    resistance_dist = ((resistance - current) / current) * 100.0
    return round(support_dist, 2), round(resistance_dist, 2)


def earnings_yield(pe_ratio: float | None) -> Number:
    """Earnings yield = 1/PE × 100%. Higher = cheaper. Compare with bond yields."""
    if pe_ratio is None or pe_ratio <= 0:
        return None
    return round((1.0 / pe_ratio) * 100.0, 2)
