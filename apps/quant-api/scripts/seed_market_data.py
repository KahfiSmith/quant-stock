"""Seed clearly-labeled SAMPLE market data for local development.

This is a developer-only helper. The rows use ``source="sample"`` and are
placeholder values pending a real data-provider/licensing decision. They are
never real market data and must never be presented as such in the product.

Run from the ``apps/quant-api`` directory with an activated virtualenv::

    python -m scripts.seed_market_data
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.core.config import get_settings
from app.db.session import Database
from app.models.market_data import Price, Stock

# name, symbol, sector — clearly sample universe for chart development.
SAMPLE_STOCKS: list[dict[str, str]] = [
    {"symbol": "BBCA", "name": "Sample Bank Central Asia", "sector": "Financials"},
    {"symbol": "TLKM", "name": "Sample Telkom Indonesia", "sector": "Telecom"},
    {"symbol": "ASII", "name": "Sample Astra International", "sector": "Industrials"},
]

BASE_PRICE: dict[str, float] = {"BBCA": 9200.0, "TLKM": 4200.0, "ASII": 6100.0}
DAYS = 15


def _candles_for(symbol: str) -> list[Price]:
    base = BASE_PRICE.get(symbol, 5000.0)
    today = date.today()
    candles: list[Price] = []
    for offset in range(DAYS - 1, -1, -1):
        day = today - timedelta(days=offset)
        drift = (offset - (DAYS - 1) / 2) * 35.0
        close = base + drift + ((offset % 3) * 14.0)
        low = close - 60.0
        high = close + 70.0
        candles.append(
            Price(
                time=datetime.combine(day, datetime.min.time(), tzinfo=UTC),
                open=close - 20.0,
                high=high,
                low=low,
                close=close,
                volume=1_200_000.0 + offset * 20_000.0,
                interval="1d",
                source="sample",
            )
        )
    return candles


def seed() -> None:
    settings = get_settings()
    db = Database(settings).session()
    try:
        for spec in SAMPLE_STOCKS:
            if db.query(Stock).filter(Stock.symbol == spec["symbol"]).first():
                continue
            stock = Stock(
                symbol=spec["symbol"],
                name=spec["name"],
                sector=spec["sector"],
                exchange="IDX",
                currency="IDR",
                timezone="Asia/Jakarta",
                market_cap=300_000_000_000.0,
            )
            stock.prices.extend(_candles_for(spec["symbol"]))
            db.add(stock)
        db.commit()
        print(f"Seeded {len(SAMPLE_STOCKS)} sample stocks (source='sample').")
    finally:
        db.close()


if __name__ == "__main__":
    seed()