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