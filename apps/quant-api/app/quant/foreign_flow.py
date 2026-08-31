"""Foreign Flow Analysis Engine.

Computes rolling accumulation/distribution signals, divergence detection,
and flow momentum from daily net foreign buy/sell data. Designed for IDX
equities where foreign institutional flow is a leading indicator.
"""

from __future__ import annotations

from typing import Literal

Number = float | None
FlowSignal = Literal["STRONG_ACCUMULATION", "ACCUMULATION", "NEUTRAL", "DISTRIBUTION", "STRONG_DISTRIBUTION"]


def net_flow_rolling_sum(
    net_values: list[float], period: int
) -> list[Number]:
    """Rolling sum of net foreign value over ``period`` days."""
    out: list[Number] = [None] * len(net_values)
    if period <= 0 or len(net_values) < period:
        return out
    window_sum = sum(net_values[:period])
    out[period - 1] = window_sum
    for i in range(period, len(net_values)):
        window_sum += net_values[i] - net_values[i - period]
        out[i] = window_sum
    return out


def flow_streak(net_values: list[float]) -> int:
    """Count consecutive days of same-direction flow from the latest day.

    Positive return = consecutive net buy days, negative = consecutive net sell days.
    """
    if not net_values:
        return 0
    latest = net_values[-1]
    if latest == 0:
        return 0
    direction = 1 if latest > 0 else -1
    count = 0
    for val in reversed(net_values):
        if (direction > 0 and val > 0) or (direction < 0 and val < 0):
            count += 1
        else:
            break
    return count * direction


def flow_momentum(net_values: list[float], short: int = 5, long: int = 20) -> Number:
    """Flow momentum: ratio of short-term rolling sum to long-term rolling sum.

    > 1.0 = accelerating accumulation, < 1.0 = decelerating, negative = reversal.
    """
    if len(net_values) < long:
        return None
    short_sum = sum(net_values[-short:])
    long_sum = sum(net_values[-long:])
    if long_sum == 0:
        return None
    return short_sum / (long_sum / (long / short))


def flow_intensity(
    net_values: list[float], volumes: list[float], period: int = 20
) -> Number:
    """Net foreign flow as percentage of average daily volume over ``period`` days.

    High intensity (>5%) = strong conviction, low (<1%) = noise.
    """
    if len(net_values) < 1 or len(volumes) < period:
        return None
    avg_vol = sum(volumes[-period:]) / period
    if avg_vol <= 0:
        return None
    return (net_values[-1] / avg_vol) * 100.0


def flow_divergence(
    net_values: list[float],
    closes: list[float],
    period: int = 10,
) -> Literal["BULLISH_DIVERGENCE", "BEARISH_DIVERGENCE", "CONFIRMING", "NEUTRAL"] | None:
    """Detect price-flow divergence over ``period`` days.

    - BULLISH_DIVERGENCE: price falling but foreigners buying (accumulation under weakness).
    - BEARISH_DIVERGENCE: price rising but foreigners selling (distribution into strength).
    - CONFIRMING: price and flow moving in same direction.
    """
    if len(net_values) < period or len(closes) < period:
        return None

    flow_sum = sum(net_values[-period:])
    price_change = closes[-1] - closes[-period]

    if abs(flow_sum) < 1e-6 and abs(price_change) < 1e-6:
        return "NEUTRAL"

    flow_positive = flow_sum > 0
    price_positive = price_change > 0

    if flow_positive and not price_positive:
        return "BULLISH_DIVERGENCE"
    if not flow_positive and price_positive:
        return "BEARISH_DIVERGENCE"
    return "CONFIRMING"


def classify_flow_signal(
    *,
    net_5d: Number,
    net_20d: Number,
    streak: int,
    momentum: Number,
) -> FlowSignal:
    """Classify overall foreign flow into an actionable signal."""
    if net_5d is None or net_20d is None:
        return "NEUTRAL"

    score = 0.0

    if net_5d > 0:
        score += 1.0
    elif net_5d < 0:
        score -= 1.0

    if net_20d > 0:
        score += 1.0
    elif net_20d < 0:
        score -= 1.0

    if streak >= 5:
        score += 1.0
    elif streak >= 3:
        score += 0.5
    elif streak <= -5:
        score -= 1.0
    elif streak <= -3:
        score -= 0.5

    if momentum is not None:
        if momentum > 1.5:
            score += 1.0
        elif momentum > 1.0:
            score += 0.5
        elif momentum < -1.5:
            score -= 1.0
        elif momentum < -1.0:
            score -= 0.5

    if score >= 3.0:
        return "STRONG_ACCUMULATION"
    if score >= 1.5:
        return "ACCUMULATION"
    if score <= -3.0:
        return "STRONG_DISTRIBUTION"
    if score <= -1.5:
        return "DISTRIBUTION"
    return "NEUTRAL"
