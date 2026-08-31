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


def calculate_momentum_score(
    rsi_val: float | None,
    trend: str,
    momentum_12m: float | None = None,
    adx_val: float | None = None,
) -> float:
    if rsi_val is None:
        base = 50.0
    else:
        base = min(max(rsi_val, 0.0), 100.0)

    if trend == "bullish":
        base = min(100.0, base + 10.0)
    elif trend == "bearish":
        base = max(0.0, base - 10.0)

    if momentum_12m is not None:
        m12_score = min(100.0, max(0.0, 50.0 + (momentum_12m * 100.0)))
        base = 0.6 * base + 0.4 * m12_score

    if adx_val is not None:
        if adx_val >= 40 and trend == "bullish":
            base = min(100.0, base + 8.0)
        elif adx_val >= 25 and trend == "bullish":
            base = min(100.0, base + 4.0)
        elif adx_val < 20:
            base = base * 0.9

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

        de_score = max(0.0, 100.0 - (debt_to_equity * 50.0))
        scores.append(de_score)
    if piotroski_estimate is not None:

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


def calculate_risk_score(
    atr_ratio: float | None,
    sharpe: float | None = None,
    sortino: float | None = None,
    max_drawdown_pct: float | None = None,
    current_drawdown_pct: float | None = None,
    volatility_regime: str | None = None,
) -> float:
    components: list[float] = []

    if atr_ratio is not None:
        components.append(min(100.0, max(0.0, 100.0 - atr_ratio * 2000.0)))

    if sharpe is not None:
        if sharpe >= 1.5:
            components.append(95.0)
        elif sharpe >= 0.5:
            components.append(60.0 + (sharpe - 0.5) * 35.0)
        elif sharpe >= 0:
            components.append(40.0 + sharpe * 40.0)
        else:
            components.append(max(0.0, 40.0 + sharpe * 20.0))

    if sortino is not None:
        if sortino >= 2.0:
            components.append(95.0)
        elif sortino >= 1.0:
            components.append(65.0 + (sortino - 1.0) * 30.0)
        elif sortino >= 0:
            components.append(40.0 + sortino * 25.0)
        else:
            components.append(max(0.0, 40.0 + sortino * 15.0))

    if max_drawdown_pct is not None:
        dd = abs(max_drawdown_pct)
        if dd < 10:
            components.append(90.0)
        elif dd < 20:
            components.append(70.0)
        elif dd < 30:
            components.append(50.0)
        elif dd < 50:
            components.append(30.0)
        else:
            components.append(10.0)

    if current_drawdown_pct is not None:
        cdd = abs(current_drawdown_pct)
        if cdd < 5:
            components.append(90.0)
        elif cdd < 15:
            components.append(65.0)
        elif cdd < 25:
            components.append(40.0)
        else:
            components.append(15.0)

    if volatility_regime is not None:
        regime_map = {"LOW": 90.0, "NORMAL": 65.0, "HIGH": 35.0, "EXTREME": 10.0}
        components.append(regime_map.get(volatility_regime, 50.0))

    if not components:
        return 50.0
    return round(sum(components) / len(components), 2)


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
    adx_val: float | None = None,
    sharpe: float | None = None,
    sortino: float | None = None,
    max_drawdown_pct: float | None = None,
    current_drawdown_pct: float | None = None,
    volatility_regime: str | None = None,
    custom_weights: dict[str, float] | None = None,
) -> FactorScores:
    m_score = calculate_momentum_score(rsi_val, trend, momentum_12m, adx_val)
    q_score = calculate_quality_score(roe, roa, debt_to_equity, piotroski_estimate)
    v_score = calculate_value_score(pe_ratio, pb_ratio)
    r_score = calculate_risk_score(
        atr_ratio,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown_pct=max_drawdown_pct,
        current_drawdown_pct=current_drawdown_pct,
        volatility_regime=volatility_regime,
    )
    g_score = calculate_growth_score(revenue_growth, eps_growth)


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
