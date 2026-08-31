"""Composite Conviction Score and Buy Recommendation system.

Blends quant factor score, foreign flow signal, risk-adjusted returns,
and divergence detection into a single conviction score (0-100) with
a human-readable recommendation.
"""

from __future__ import annotations

from typing import Literal, NamedTuple

BuyRecommendation = Literal[
    "STRONG_BUY_HIGH_CONVICTION",
    "BUY_ACCUMULATE",
    "BUY_WATCHLIST",
    "HOLD_NEUTRAL",
    "REDUCE_POSITION",
    "SELL_EXIT",
]

_SIGNAL_SCORE = {
    "STRONG_BUY": 95,
    "BUY": 75,
    "HOLD": 50,
    "SELL": 25,
    "STRONG_SELL": 5,
}

_FLOW_SCORE = {
    "STRONG_ACCUMULATION": 95,
    "ACCUMULATION": 75,
    "NEUTRAL": 50,
    "DISTRIBUTION": 25,
    "STRONG_DISTRIBUTION": 5,
}

_DIVERGENCE_MULTIPLIER = {
    "BULLISH_DIVERGENCE": 1.10,
    "BEARISH_DIVERGENCE": 0.90,
    "CONFIRMING": 1.0,
    "NEUTRAL": 1.0,
}


class ConvictionResult(NamedTuple):
    conviction_score: float
    recommendation: BuyRecommendation
    recommendation_reasons: list[str]


def calculate_conviction(
    *,
    quant_signal: str,
    quant_confidence: float,
    flow_signal: str | None = None,
    flow_divergence: str | None = None,
    sharpe: float | None = None,
    sortino: float | None = None,
    bollinger_zscore: float | None = None,
    streak_days: int = 0,
    momentum_1m: float | None = None,
) -> ConvictionResult:

    quant_base = _SIGNAL_SCORE.get(quant_signal, 50) * (quant_confidence / 100.0)

    flow_base = _FLOW_SCORE.get(flow_signal or "NEUTRAL", 50)

    risk_adj_components: list[float] = []
    if sharpe is not None:
        risk_adj_components.append(min(100, max(0, 50 + sharpe * 25)))
    if sortino is not None:
        risk_adj_components.append(min(100, max(0, 50 + sortino * 20)))
    risk_adj = sum(risk_adj_components) / len(risk_adj_components) if risk_adj_components else 50.0

    raw = 0.50 * quant_base + 0.30 * flow_base + 0.20 * risk_adj

    divergence_mult = _DIVERGENCE_MULTIPLIER.get(flow_divergence or "NEUTRAL", 1.0)
    raw *= divergence_mult

    if bollinger_zscore is not None and bollinger_zscore < -2.0:
        raw = min(100, raw + 5.0)
    elif bollinger_zscore is not None and bollinger_zscore > 2.0:
        raw = max(0, raw - 5.0)

    if abs(streak_days) >= 5:
        if streak_days > 0:
            raw = min(100, raw + 3.0)
        else:
            raw = max(0, raw - 3.0)

    score = round(min(100, max(0, raw)), 1)

    reasons: list[str] = []

    if score >= 80:
        rec: BuyRecommendation = "STRONG_BUY_HIGH_CONVICTION"
        reasons.append(f"Conviction {score}/100 — strong multi-signal alignment")
    elif score >= 65:
        rec = "BUY_ACCUMULATE"
        reasons.append(f"Conviction {score}/100 — favorable risk/reward")
    elif score >= 55:
        rec = "BUY_WATCHLIST"
        reasons.append(f"Conviction {score}/100 — constructive but awaiting confirmation")
    elif score >= 40:
        rec = "HOLD_NEUTRAL"
        reasons.append(f"Conviction {score}/100 — balanced factors, no clear edge")
    elif score >= 25:
        rec = "REDUCE_POSITION"
        reasons.append(f"Conviction {score}/100 — deteriorating conditions")
    else:
        rec = "SELL_EXIT"
        reasons.append(f"Conviction {score}/100 — multiple negative signals aligned")

    if flow_divergence == "BULLISH_DIVERGENCE":
        reasons.append("Institutional accumulation under price weakness (bullish divergence)")
    if flow_signal in ("STRONG_ACCUMULATION", "ACCUMULATION"):
        reasons.append("Foreign institutional buying pressure supports upside")
    if flow_signal in ("STRONG_DISTRIBUTION", "DISTRIBUTION"):
        reasons.append("Foreign institutional selling pressure — watch for further weakness")
    if momentum_1m is not None and momentum_1m > 10:
        reasons.append(f"Strong short-term momentum (+{momentum_1m:.1f}%)")
    if sharpe is not None and sharpe > 1.5:
        reasons.append(f"Excellent risk-adjusted returns (Sharpe {sharpe:.2f})")

    return ConvictionResult(
        conviction_score=score,
        recommendation=rec,
        recommendation_reasons=reasons,
    )
