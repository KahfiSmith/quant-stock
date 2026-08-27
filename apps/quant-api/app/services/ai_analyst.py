"""AI analyst engine for synthesizing quantitative and fundamental facts into structured insights.

Follows strict guardrails:
1. No personal investment advice or guarantee of return.
2. Facts derived directly from calculated scores, technical indicators, and fundamental ratios.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.market_data import Stock
from app.schemas.ai_analyst import AiAnalystResponse
from app.services.fundamental import get_latest_fundamental
from app.services.quant import compute_stock_quant_score
from app.services.technical import calculate_technical_analysis

DISCLAIMER = (
    "QuantLens AI Analyst provides educational and analytical summaries derived from quantitative models "
    "and financial data. This does not constitute financial, investment, or trading advice."
)


def generate_ai_analysis(db: Session, stock: Stock) -> AiAnalystResponse:
    tech = calculate_technical_analysis(db, stock, interval="1d")
    fund = get_latest_fundamental(db, stock)
    quant = compute_stock_quant_score(db, stock)

    strengths: list[str] = []
    risks: list[str] = []
    unknowns: list[str] = []

    # 1. Evaluate Technical Insights
    has_long_term_trend = (
        tech.indicators.ma50 is not None and tech.indicators.ma200 is not None
    )
    if tech.trend == "bullish":
        if has_long_term_trend:
            strengths.append("Price action exhibits a bullish trend with MA50 positioned above MA200.")
        elif tech.indicators.ma20 is not None:
            strengths.append("Price action is above its MA20, indicating short-term bullish momentum.")
        else:
            strengths.append("Price action is classified as bullish by the available technical data.")
    elif tech.trend == "bearish":
        if has_long_term_trend:
            risks.append("Underlying trend is bearish with primary moving averages showing downward pressure.")
        elif tech.indicators.ma20 is not None:
            risks.append("Price action is below its MA20, indicating short-term bearish momentum.")
        else:
            risks.append("Price action is classified as bearish by the available technical data.")

    if tech.rsi is not None:
        if tech.rsi < 35:
            strengths.append(
                f"RSI(14) indicates oversold conditions at {tech.rsi}, suggesting potential mean reversion."
            )
        elif tech.rsi > 70:
            risks.append(
                f"RSI(14) is elevated at {tech.rsi}, indicating overbought momentum and short-term pullback risk."
            )

    # 2. Evaluate Fundamental Insights
    if fund:
        r = fund.ratios
        if r.roe is not None:
            if r.roe >= 0.15:
                strengths.append(f"High capital efficiency with Return on Equity (ROE) at {(r.roe * 100):.1f}%.")
            elif r.roe < 0.08:
                risks.append(f"Subdued profitability with ROE at {(r.roe * 100):.1f}%.")

        if r.pe_ratio is not None:
            if r.pe_ratio < 15:
                strengths.append(
                    f"Valuation is conservative relative to broad market benchmarks (P/E {r.pe_ratio:.1f})."
                )
            elif r.pe_ratio > 30:
                risks.append(
                    f"Rich valuation multiple trading at P/E {r.pe_ratio:.1f}, requiring sustained high growth."
                )

        if r.debt_to_equity is not None and r.debt_to_equity > 1.5:
            risks.append(f"Elevated financial leverage with Debt-to-Equity at {r.debt_to_equity:.2f}.")
    else:
        unknowns.append("Financial statement filings and balance sheet fundamentals are currently unrecorded.")

    # 3. Quant Score Synthesis
    if quant.total_score >= 75:
        strengths.append(f"Strong overall quantitative profile with a composite score of {quant.total_score}/100.")
    elif quant.total_score < 45:
        risks.append(
            f"Weak composite quantitative score of {quant.total_score}/100 across momentum and quality factors."
        )

    if not strengths:
        strengths.append("Asset exhibits neutral multi-factor characteristics without extreme outliers.")
    if not risks:
        risks.append("No immediate quantitative red flags identified under current baseline criteria.")

    unknowns.append("Future regulatory shifts, macroeconomic interest rate adjustments, and management changes.")

    # 4. Formulate Conclusion
    if quant.total_score >= 70 and tech.trend == "bullish":
        support = "constructive price momentum"
        if fund:
            support += " and the available fundamental data"
        conclusion = (
            f"{stock.symbol} displays a robust quantitative profile supported by {support}. "
            f"Suitable for further disciplined quantitative evaluation."
        )
    elif quant.total_score < 50 or tech.trend == "bearish":
        conclusion = (
            f"{stock.symbol} exhibits mixed or defensive characteristics with notable risk factors in trend "
            f"or valuation. Prudent risk management and close monitoring of upcoming filings are warranted."
        )
    else:
        conclusion = (
            f"{stock.symbol} reflects a balanced, neutral quantitative stance with balanced strengths and risks. "
            f"Look for catalyst developments in quarterly earnings or trend continuation."
        )

    return AiAnalystResponse(
        symbol=stock.symbol,
        strengths=strengths,
        risks=risks,
        unknowns=unknowns,
        conclusion=conclusion,
        disclaimer=DISCLAIMER,
        as_of=datetime.now(UTC),
    )
