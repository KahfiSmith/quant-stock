"""Multi-factor quantitative scoring engine.

Formula:
Total Score = 0.30 * Momentum + 0.25 * Quality + 0.20 * Value + 0.15 * Risk + 0.10 * Growth
Supports both cross-sectional sector normalization and absolute bounded factors.
"""

from __future__ import annotations

from typing import NamedTuple


class FactorScores(NamedTuple):
    momentum: float
    quality: float
    value: float
    risk: float
    growth: float
    total_score: float
    data_quality: str


def calculate_momentum_score(rsi_val: float | None, trend: str, momentum_12m: float | None = None) -> float:
    if rsi_val is None:
        base = 50.0
    else:
        base = min(max(rsi_val, 0.0), 100.0)

    if trend == "bullish":
        base = min(100.0, base + 10.0)
    elif trend == "bearish":
        base = max(0.0, base - 10.0)

    # If 12-month historical price return is provided, blend into momentum factor
    if momentum_12m is not None:
        # Scale: +30% return -> 80 score, -30% return -> 20 score
        m12_score = min(100.0, max(0.0, 50.0 + (momentum_12m * 100.0)))
        base = 0.6 * base + 0.4 * m12_score

    return round(base, 2)


def calculate_quality_score(
    roe: float | None,
    roa: float | None,
    debt_to_equity: float | None,
    piotroski_estimate: int | None = None,
) -> float:
    scores: list[float] = []
    if roe is not None:
        scores.append(min(100.0, max(0.0, (roe / 0.20) * 100.0)))
    if roa is not None:
        scores.append(min(100.0, max(0.0, (roa / 0.10) * 100.0)))
    if debt_to_equity is not None:
        # Lower debt is higher quality
        de_score = max(0.0, 100.0 - (debt_to_equity * 50.0))
        scores.append(de_score)
    if piotroski_estimate is not None:
        # 0 to 9 scale -> 0 to 100
        scores.append(min(100.0, max(0.0, (piotroski_estimate / 9.0) * 100.0)))

    return round(sum(scores) / len(scores), 2) if scores else 50.0


def calculate_value_score(pe_ratio: float | None, pb_ratio: float | None) -> float:
    scores: list[float] = []
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio <= 15:
            scores.append(100.0)
        elif pe_ratio <= 30:
            scores.append(max(0.0, 100.0 - (pe_ratio - 15) * 4.0))
        else:
            scores.append(max(0.0, 40.0 - (pe_ratio - 30) * 1.5))
    if pb_ratio is not None and pb_ratio > 0:
        if pb_ratio <= 1.5:
            scores.append(100.0)
        elif pb_ratio <= 4.0:
            scores.append(max(0.0, 100.0 - (pb_ratio - 1.5) * 25.0))
        else:
            scores.append(max(0.0, 37.5 - (pb_ratio - 4.0) * 5.0))
    return round(sum(scores) / len(scores), 2) if scores else 50.0


def calculate_risk_score(atr_ratio: float | None) -> float:
    # Lower ATR/volatility gives higher safety score
    if atr_ratio is None:
        return 50.0
    # atr_ratio is ATR / Close. Ideal < 2% (0.02)
    score = max(0.0, 100.0 - (atr_ratio * 2000.0))
    return round(min(100.0, score), 2)


def calculate_growth_score(revenue_growth: float | None, eps_growth: float | None) -> float:
    scores: list[float] = []
    if revenue_growth is not None:
        scores.append(min(100.0, max(0.0, 50.0 + revenue_growth * 250.0)))
    if eps_growth is not None:
        scores.append(min(100.0, max(0.0, 50.0 + eps_growth * 250.0)))
    return round(sum(scores) / len(scores), 2) if scores else 50.0


def calculate_quant_score(
    *,
    rsi_val: float | None,
    trend: str,
    roe: float | None,
    roa: float | None,
    debt_to_equity: float | None,
    pe_ratio: float | None,
    pb_ratio: float | None,
    atr_ratio: float | None,
    revenue_growth: float | None,
    eps_growth: float | None,
    momentum_12m: float | None = None,
    piotroski_estimate: int | None = None,
    custom_weights: dict[str, float] | None = None,
) -> FactorScores:
    m_score = calculate_momentum_score(rsi_val, trend, momentum_12m)
    q_score = calculate_quality_score(roe, roa, debt_to_equity, piotroski_estimate)
    v_score = calculate_value_score(pe_ratio, pb_ratio)
    r_score = calculate_risk_score(atr_ratio)
    g_score = calculate_growth_score(revenue_growth, eps_growth)

    # Base or custom factor weights
    w_m = 0.30
    w_q = 0.25
    w_v = 0.20
    w_r = 0.15
    w_g = 0.10

    if custom_weights:
        w_m = float(custom_weights.get("momentum", w_m))
        w_q = float(custom_weights.get("quality", w_q))
        w_v = float(custom_weights.get("value", w_v))
        w_r = float(custom_weights.get("risk", w_r))
        w_g = float(custom_weights.get("growth", w_g))
        total_w = w_m + w_q + w_v + w_r + w_g
        if total_w > 0:
            w_m /= total_w
            w_q /= total_w
            w_v /= total_w
            w_r /= total_w
            w_g /= total_w

    total = w_m * m_score + w_q * q_score + w_v * v_score + w_r * r_score + w_g * g_score

    missing_count = sum(
        1
        for val in (rsi_val, roe, roa, debt_to_equity, pe_ratio, pb_ratio, atr_ratio, revenue_growth, eps_growth)
        if val is None
    )
    data_quality = "complete" if missing_count == 0 else "partial" if missing_count < 6 else "insufficient"

    return FactorScores(
        momentum=m_score,
        quality=q_score,
        value=v_score,
        risk=r_score,
        growth=g_score,
        total_score=round(total, 2),
        data_quality=data_quality,
    )
