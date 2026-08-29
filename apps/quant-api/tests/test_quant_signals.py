from app.quant.signals import generate_quant_signal


def test_generate_quant_signal_strong_buy() -> None:
    decision = generate_quant_signal(
        total_score=88.5,
        momentum_score=78.0,
        quality_score=85.0,
        value_score=80.0,
        growth_score=75.0,
        risk_score=75.0,
        trend="bullish",
        pe_ratio=14.0,
        roe=0.22,
        debt_to_equity=0.5,
    )
    assert decision.signal == "STRONG_BUY"
    assert decision.risk_level == "LOW"
    assert decision.confidence_pct >= 80.0
    assert len(decision.reasons) >= 2


def test_generate_quant_signal_sell() -> None:
    decision = generate_quant_signal(
        total_score=40.0,
        momentum_score=35.0,
        quality_score=38.0,
        value_score=45.0,
        growth_score=40.0,
        risk_score=35.0,
        trend="bearish",
        pe_ratio=45.0,
        roe=0.04,
        debt_to_equity=2.1,
    )
    assert decision.signal in {"SELL", "STRONG_SELL"}
    assert decision.risk_level == "HIGH"
    assert any("leverage" in r.lower() or "profitability" in r.lower() for r in decision.reasons)
