"""Fundamental scoring and ratio evaluation logic."""

from __future__ import annotations


def calculate_fundamental_score(
    pe_ratio: float | None,
    pb_ratio: float | None,
    roe: float | None,
    roa: float | None,
    debt_to_equity: float | None,
    revenue_growth: float | None,
    eps_growth: float | None,
) -> float | None:
    """Calculates a normalized 0-100 fundamental score based on valuation, profitability, and growth.

    Returns None if all key ratios are missing.
    """
    scores: list[float] = []

    # 1. Valuation: P/E ratio (ideal < 15, reasonable < 25)
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio <= 15:
            scores.append(100.0)
        elif pe_ratio <= 25:
            scores.append(max(0.0, 100.0 - (pe_ratio - 15) * 5))
        else:
            scores.append(max(0.0, 50.0 - (pe_ratio - 25) * 2))

    # 2. Valuation: P/B ratio (ideal < 1.5, reasonable < 3.0)
    if pb_ratio is not None and pb_ratio > 0:
        if pb_ratio <= 1.5:
            scores.append(100.0)
        elif pb_ratio <= 3.0:
            scores.append(max(0.0, 100.0 - (pb_ratio - 1.5) * 33.3))
        else:
            scores.append(max(0.0, 50.0 - (pb_ratio - 3.0) * 10))

    # 3. Profitability: ROE (ideal > 15%, good > 10%)
    if roe is not None:
        if roe >= 0.15:
            scores.append(100.0)
        elif roe > 0:
            scores.append(roe / 0.15 * 100.0)
        else:
            scores.append(0.0)

    # 4. Solvency / Health: Debt to Equity (ideal < 0.5, acceptable < 1.5)
    if debt_to_equity is not None and debt_to_equity >= 0:
        if debt_to_equity <= 0.5:
            scores.append(100.0)
        elif debt_to_equity <= 1.5:
            scores.append(max(0.0, 100.0 - (debt_to_equity - 0.5) * 50))
        else:
            scores.append(max(0.0, 50.0 - (debt_to_equity - 1.5) * 20))

    # 5. Growth: Revenue growth (ideal > 10%)
    if revenue_growth is not None:
        if revenue_growth >= 0.10:
            scores.append(100.0)
        elif revenue_growth > 0:
            scores.append(revenue_growth / 0.10 * 100.0)
        else:
            scores.append(0.0)

    if not scores:
        return None

    return round(sum(scores) / len(scores), 2)
