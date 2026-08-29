"""Composite Quantitative Signal Generation Engine.

Classifies assets into actionable quantitative decisions:
- STRONG BUY: High composite score (>80), positive trend momentum, robust financial health.
- BUY: Constructive score (65-80) with favorable risk/reward.
- HOLD: Neutral characteristics (45-64) or balanced opposing factors.
- SELL: Deteriorating score (30-44) or elevated valuation/momentum risks.
- STRONG SELL: Low score (<30) with severe fundamental and trend deterioration.
"""

from __future__ import annotations

from typing import Literal, NamedTuple

QuantSignalType = Literal["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
RiskLevelType = Literal["LOW", "MEDIUM", "HIGH"]


class QuantDecision(NamedTuple):
    signal: QuantSignalType
    risk_level: RiskLevelType
    confidence_pct: float
    reasons: list[str]


def generate_quant_signal(
    *,
    total_score: float,
    momentum_score: float,
    quality_score: float,
    value_score: float,
    growth_score: float,
    risk_score: float,
    trend: str,
    pe_ratio: float | None = None,
    roe: float | None = None,
    debt_to_equity: float | None = None,
) -> QuantDecision:
    reasons: list[str] = []

    # 1. Evaluate Quality
    if quality_score >= 80 or (roe is not None and roe >= 0.18):
        reasons.append("High capital efficiency & profitability (High Quality)")
    elif quality_score < 45 or (roe is not None and roe < 0.08):
        reasons.append("Subdued operational profitability")

    # 2. Evaluate Momentum
    if momentum_score >= 75 or trend == "bullish":
        reasons.append("Constructive price momentum & bullish technical posture")
    elif momentum_score < 40 or trend == "bearish":
        reasons.append("Downward price momentum & bearish trend pressure")

    # 3. Evaluate Valuation
    if value_score >= 75 or (pe_ratio is not None and 0 < pe_ratio <= 15):
        reasons.append("Conservative valuation multiple trading at attractive discount")
    elif value_score < 40 or (pe_ratio is not None and pe_ratio > 35):
        reasons.append("Elevated valuation multiple requiring sustained high earnings growth")

    # 4. Evaluate Financial Health / Debt
    if debt_to_equity is not None and debt_to_equity > 1.5:
        reasons.append("Elevated debt leverage structure")
    elif debt_to_equity is not None and debt_to_equity <= 0.6:
        reasons.append("Robust balance sheet with conservative leverage")

    # 5. Risk Assessment
    if risk_score >= 70:
        risk_level: RiskLevelType = "LOW"
    elif risk_score >= 45:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
        reasons.append("Elevated historical price volatility")

    # 6. Synthesize Signal Decision
    if total_score >= 82 and momentum_score >= 60 and quality_score >= 70:
        signal: QuantSignalType = "STRONG_BUY"
        confidence = min(98.0, 75.0 + (total_score - 80) * 1.1)
    elif total_score >= 68 and momentum_score >= 50:
        signal = "BUY"
        confidence = min(88.0, 65.0 + (total_score - 65) * 1.0)
    elif total_score <= 32 or (momentum_score < 35 and quality_score < 40):
        signal = "STRONG_SELL"
        confidence = min(95.0, 70.0 + (35 - total_score) * 1.2)
    elif total_score < 48:
        signal = "SELL"
        confidence = min(85.0, 60.0 + (50 - total_score) * 1.0)
    else:
        signal = "HOLD"
        confidence = 60.0

    if not reasons:
        reasons.append("Balanced quantitative profile without extreme outliers")

    return QuantDecision(
        signal=signal,
        risk_level=risk_level,
        confidence_pct=round(confidence, 1),
        reasons=reasons,
    )
