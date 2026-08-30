from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.ingestion.collector import LiveEodCollector
from app.quant.scoring import calculate_momentum_score, calculate_quality_score, calculate_quant_score


def test_calculate_momentum_score_with_12m_return() -> None:

    score = calculate_momentum_score(rsi_val=60.0, trend="bullish", momentum_12m=0.25)
    assert score > 70.0


def test_calculate_quality_score_with_piotroski() -> None:

    score = calculate_quality_score(roe=0.22, roa=0.08, debt_to_equity=0.3, piotroski_estimate=8)
    assert score > 85.0


def test_calculate_quant_score_comprehensive() -> None:
    factors = calculate_quant_score(
        rsi_val=55.0,
        trend="bullish",
        roe=0.18,
        roa=0.05,
        debt_to_equity=0.5,
        pe_ratio=14.0,
        pb_ratio=1.8,
        atr_ratio=0.015,
        revenue_growth=0.15,
        eps_growth=0.12,
        momentum_12m=0.20,
        piotroski_estimate=7,
    )
    assert 0 <= factors.total_score <= 100
    assert factors.data_quality == "complete"


def test_live_eod_collector_parses_response() -> None:
    collector = LiveEodCollector()
    mock_payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1704067200],
                    "indicators": {
                        "quote": [
                            {
                                "open": [9100.0],
                                "high": [9200.0],
                                "low": [9000.0],
                                "close": [9150.0],
                                "volume": [5000000.0],
                            }
                        ]
                    },
                }
            ]
        }
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        json_bytes = str(mock_payload).replace("'", '"').encode("utf-8")
        mock_response.read.return_value = json_bytes
        mock_urlopen.return_value.__enter__.return_value = mock_response

        candles = collector.fetch_stock_prices("BBCA.JK")
        assert len(candles) == 1
        assert candles[0].symbol == "BBCA.JK"
        assert candles[0].close == Decimal("9150")
        assert candles[0].source == "live_market_data"
