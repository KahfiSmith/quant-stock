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
    volume_zscore: float | None = None,
    volatility_regime: str | None = None,
    momentum_1m: float | None = None,
    max_drawdown_pct: float | None = None,
    bollinger_zscore: float | None = None,
    flow_signal: str | None = None,
    flow_divergence: str | None = None,
    momentum_12m: float | None = None,
    adx_val: float | None = None,
    mfi_val: float | None = None,
    stochastic_rsi_val: float | None = None,
    support_distance_pct: float | None = None,
    obv_trend_pct: float | None = None,
) -> QuantDecision:
    reasons: list[str] = []


    if quality_score >= 80 or (roe is not None and roe >= 0.18):
        reasons.append("High capital efficiency & profitability (High Quality)")
    elif quality_score < 45 or (roe is not None and roe < 0.08):
        reasons.append("Subdued operational profitability")


    if momentum_score >= 75 or trend == "bullish":
        reasons.append("Constructive price momentum & bullish technical posture")
    elif momentum_score < 40 or trend == "bearish":
        reasons.append("Downward price momentum & bearish trend pressure")


    if value_score >= 75 or (pe_ratio is not None and 0 < pe_ratio <= 15):
        reasons.append("Conservative valuation multiple trading at attractive discount")
    elif value_score < 40 or (pe_ratio is not None and pe_ratio > 35):
        reasons.append("Elevated valuation multiple requiring sustained high earnings growth")


    if debt_to_equity is not None and debt_to_equity > 1.5:
        reasons.append("Elevated debt leverage structure")
    elif debt_to_equity is not None and debt_to_equity <= 0.6:
        reasons.append("Robust balance sheet with conservative leverage")


    if volume_zscore is not None and volume_zscore >= 2.0:
        reasons.append(f"Abnormal volume spike (Z={volume_zscore:.1f}) — elevated conviction")
    elif volume_zscore is not None and volume_zscore <= -1.0:
        reasons.append("Below-average volume — weak participation")


    if volatility_regime == "EXTREME":
        reasons.append("Extreme volatility regime — elevated position risk")
    elif volatility_regime == "LOW":
        reasons.append("Low-volatility regime — potential breakout setup")

    if momentum_1m is not None and momentum_1m > 10.0:
        reasons.append(f"Strong 1M price momentum (+{momentum_1m:.1f}%)")
    elif momentum_1m is not None and momentum_1m < -10.0:
        reasons.append(f"Severe 1M price decline ({momentum_1m:.1f}%)")

    if max_drawdown_pct is not None and max_drawdown_pct < -30.0:
        reasons.append(f"Deep historical drawdown ({max_drawdown_pct:.1f}%) — recovery risk")

    if bollinger_zscore is not None:
        if bollinger_zscore < -2.0:
            reasons.append(f"Price near lower Bollinger band (Z={bollinger_zscore:.1f}) — oversold / mean reversion candidate")
        elif bollinger_zscore > 2.0:
            reasons.append(f"Price near upper Bollinger band (Z={bollinger_zscore:.1f}) — overbought / potential pullback")

    if flow_signal in ("STRONG_ACCUMULATION", "ACCUMULATION"):
        reasons.append(f"Foreign institutional accumulation ({flow_signal.replace('_', ' ').lower()})")
    elif flow_signal in ("STRONG_DISTRIBUTION", "DISTRIBUTION"):
        reasons.append(f"Foreign institutional distribution ({flow_signal.replace('_', ' ').lower()})")

    if flow_divergence == "BULLISH_DIVERGENCE":
        reasons.append("Bullish divergence: price declining but foreign buying — institutional accumulation under weakness")
    elif flow_divergence == "BEARISH_DIVERGENCE":
        reasons.append("Bearish divergence: price rising but foreign selling — distribution into strength")

    if momentum_12m is not None and momentum_12m > 0.20:
        reasons.append(f"Strong 12M return (+{momentum_12m * 100:.0f}%) — long-term trend intact")
    elif momentum_12m is not None and momentum_12m < -0.20:
        reasons.append(f"Weak 12M return ({momentum_12m * 100:.0f}%) — structural decline")

    if adx_val is not None:
        if adx_val >= 40:
            reasons.append(f"Strong trend (ADX {adx_val:.0f}) — high-probability trend follow")
        elif adx_val < 20:
            reasons.append(f"No clear trend (ADX {adx_val:.0f}) — range-bound, avoid momentum entries")

    if mfi_val is not None:
        if mfi_val < 20:
            reasons.append(f"MFI oversold ({mfi_val:.0f}) — volume-confirmed buying opportunity")
        elif mfi_val > 80:
            reasons.append(f"MFI overbought ({mfi_val:.0f}) — volume-confirmed distribution zone")

    if stochastic_rsi_val is not None:
        if stochastic_rsi_val < 20:
            reasons.append("Stochastic RSI deeply oversold — timing entry zone")
        elif stochastic_rsi_val > 80:
            reasons.append("Stochastic RSI overbought — caution on new entries")

    if support_distance_pct is not None and support_distance_pct < 3.0:
        reasons.append(f"Price near support ({support_distance_pct:.1f}% above) — favorable risk/reward entry")

    if obv_trend_pct is not None:
        if obv_trend_pct > 10.0:
            reasons.append("OBV rising — smart money accumulation in progress")
        elif obv_trend_pct < -10.0:
            reasons.append("OBV declining — smart money distribution in progress")


    if risk_score >= 70:
        risk_level: RiskLevelType = "LOW"
    elif risk_score >= 45:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
        reasons.append("Elevated historical price volatility")

    if volatility_regime == "EXTREME" and risk_level != "HIGH":
        risk_level = "HIGH"


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

    if volume_zscore is not None:
        if signal in ("STRONG_BUY", "BUY") and volume_zscore >= 1.5:
            confidence = min(98.0, confidence + 4.0)
        elif signal in ("STRONG_BUY", "BUY") and volume_zscore <= -1.0:
            confidence = max(50.0, confidence - 5.0)
        elif signal in ("STRONG_SELL", "SELL") and volume_zscore >= 1.5:
            confidence = min(98.0, confidence + 3.0)

    if momentum_1m is not None:
        if signal in ("STRONG_BUY", "BUY") and momentum_1m > 5.0:
            confidence = min(98.0, confidence + 3.0)
        elif signal in ("STRONG_BUY", "BUY") and momentum_1m < -5.0:
            confidence = max(50.0, confidence - 4.0)

    if flow_signal in ("STRONG_ACCUMULATION", "ACCUMULATION") and signal in ("STRONG_BUY", "BUY"):
        confidence = min(98.0, confidence + 5.0)
    elif flow_signal in ("STRONG_DISTRIBUTION", "DISTRIBUTION") and signal in ("STRONG_BUY", "BUY"):
        confidence = max(50.0, confidence - 4.0)

    if flow_divergence == "BULLISH_DIVERGENCE" and signal in ("STRONG_BUY", "BUY", "HOLD"):
        confidence = min(98.0, confidence + 4.0)
    elif flow_divergence == "BEARISH_DIVERGENCE" and signal in ("STRONG_BUY", "BUY"):
        confidence = max(50.0, confidence - 3.0)

    if bollinger_zscore is not None:
        if bollinger_zscore < -2.0 and signal in ("BUY", "HOLD"):
            confidence = min(98.0, confidence + 3.0)
        elif bollinger_zscore > 2.0 and signal in ("STRONG_BUY", "BUY"):
            confidence = max(50.0, confidence - 3.0)

    if mfi_val is not None and mfi_val < 20 and signal in ("BUY", "HOLD"):
        confidence = min(98.0, confidence + 4.0)
    elif mfi_val is not None and mfi_val > 80 and signal in ("STRONG_BUY", "BUY"):
        confidence = max(50.0, confidence - 3.0)

    if support_distance_pct is not None and support_distance_pct < 3.0 and signal in ("STRONG_BUY", "BUY"):
        confidence = min(98.0, confidence + 3.0)

    if obv_trend_pct is not None and obv_trend_pct > 10.0 and signal in ("STRONG_BUY", "BUY"):
        confidence = min(98.0, confidence + 3.0)
    elif obv_trend_pct is not None and obv_trend_pct < -10.0 and signal in ("STRONG_BUY", "BUY"):
        confidence = max(50.0, confidence - 3.0)

    if not reasons:
        reasons.append("Balanced quantitative profile without extreme outliers")

    return QuantDecision(
        signal=signal,
        risk_level=risk_level,
        confidence_pct=round(confidence, 1),
        reasons=reasons,
    )
