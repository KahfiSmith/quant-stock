"""Regression tests for AI Analyst engine/provider labeling.

The current implementation uses rule-based (deterministic) synthesis.
These tests pin the contract:
1. analysis_engine must be 'deterministic' (NOT 'llm' until a real call is wired).
2. provider and model must be None when engine is deterministic.
3. analysis_version must NOT claim a model prefix when no LLM was called.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import numpy as np
import pandas as pd


class FakeTicker:
    _info = {
        "BBCA.JK": {
            "longName": "Bank Central Asia",
            "sector": "Financial Services",
            "exchange": "JKT",
            "marketCap": 1_200_000_000_000_000,
            "currency": "IDR",
            "trailingPE": 14.2,
            "priceToBook": 2.8,
            "returnOnEquity": 0.21,
            "returnOnAssets": 0.034,
            "debtToEquity": 0.5,
            "revenueGrowth": 0.09,
            "earningsGrowth": 0.12,
        }
    }

    def __init__(self, symbol, **_):
        self._symbol = symbol

    def history(self, **kwargs):
        end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        dates = pd.date_range(end=end, periods=300, freq="D")
        base = 9500.0
        np.random.seed(42)
        closes = base + np.cumsum(np.random.randn(len(dates)) * (base * 0.01))
        opens = closes + np.random.randn(len(dates)) * (base * 0.005)
        highs = np.maximum(opens, closes) + np.abs(np.random.randn(len(dates))) * (base * 0.008)
        lows = np.minimum(opens, closes) - np.abs(np.random.randn(len(dates))) * (base * 0.008)
        vols = np.random.randint(5_000_000, 20_000_000, len(dates))
        return pd.DataFrame(
            {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
            index=dates,
        )

    @property
    def info(self):
        return self._info.get(self._symbol, {})


def test_ai_engine_label_is_deterministic_no_llm_claim(client) -> None:
    """Even when env points to Gemini, analysis_engine must be 'deterministic'."""
    from sqlalchemy import select

    from app.ingestion import YFinanceCollector, ingest_fundamentals, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Stock
    from app.services.ai_analyst import generate_ai_analysis

    with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
        collector = YFinanceCollector()
        db = client.app.state.database.session()
        try:
            stock = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
            if stock is None:
                meta = collector.collect_metadata("BBCA")
                db.add(
                    Stock(
                        symbol="BBCA",
                        name=meta["name"],
                        sector=meta["sector"],
                        exchange=meta["exchange"],
                        market_cap=meta["market_cap"],
                        currency=meta["currency"],
                        timezone=meta["timezone"],
                    )
                )
                db.commit()
                stock = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
            req = CollectionRequest(
                symbols=["BBCA"], start_date=None, end_date=None, interval="1d"
            )
            ingest_prices(db, list(collector.collect_prices(req)))
            ingest_fundamentals(db, list(collector.collect_fundamentals(req)))

            analysis = generate_ai_analysis(db, stock)

            # Engine must be deterministic (no LLM was called)
            assert analysis.analysis_engine == "deterministic"
            # Provider/model must be None
            assert analysis.provider is None
            assert analysis.model is None
            # Version must not claim an LLM model
            assert not analysis.analysis_version.startswith("llm-")
            assert analysis.analysis_version == "deterministic-v1"
        finally:
            db.close()


def test_ai_engine_label_persistent_across_env_configs(client) -> None:
    """Switching the configured provider to 'openai_compatible' must NOT
    change the analysis_engine to 'llm' until a real call is wired."""
    from sqlalchemy import select

    from app.ingestion import YFinanceCollector, ingest_fundamentals, ingest_prices
    from app.ingestion.contracts import CollectionRequest
    from app.models.market_data import Stock
    from app.services.ai_analyst import generate_ai_analysis

    settings = client.app.state.settings
    original_provider = settings.ai_analyst_provider
    original_key = settings.ai_analyst_api_key
    try:
        # Simulate env that points to Gemini
        settings.ai_analyst_provider = "openai_compatible"
        settings.ai_analyst_api_key = "test-key"

        with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
            collector = YFinanceCollector()
            db = client.app.state.database.session()
            try:
                # Ensure stock exists and is populated
                stock = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
                if stock is None:
                    meta = collector.collect_metadata("BBCA")
                    db.add(
                        Stock(
                            symbol="BBCA",
                            name=meta["name"],
                            sector=meta["sector"],
                            exchange=meta["exchange"],
                            market_cap=meta["market_cap"],
                            currency=meta["currency"],
                            timezone=meta["timezone"],
                        )
                    )
                    db.commit()
                    stock = db.scalar(select(Stock).where(Stock.symbol == "BBCA"))
                req = CollectionRequest(
                    symbols=["BBCA"], start_date=None, end_date=None, interval="1d"
                )
                price_records = list(collector.collect_prices(req))
                if price_records:
                    ingest_prices(db, price_records)
                fund_records = list(collector.collect_fundamentals(req))
                if fund_records:
                    ingest_fundamentals(db, fund_records)

                # Call the function directly
                analysis = generate_ai_analysis(db, stock)
                # Engine must STILL be deterministic — provider config doesn't
                # change engine semantics.
                assert analysis.analysis_engine == "deterministic", (
                    f"Engine should be deterministic regardless of provider config, "
                    f"got {analysis.analysis_engine}"
                )
                assert analysis.provider is None
                assert analysis.model is None
                assert not analysis.analysis_version.startswith("llm-")
            finally:
                db.close()
    finally:
        settings.ai_analyst_provider = original_provider
        settings.ai_analyst_api_key = original_key
