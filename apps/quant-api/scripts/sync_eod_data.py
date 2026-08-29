"""CLI command script to synchronize and ingest live market data into QuantLens database.

Usage:
    python -m scripts.sync_eod_data --symbols BBCA.JK,TLKM.JK,ASII.JK,AAPL,NVDA
"""

from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import Database
from app.ingestion.collector import LiveEodCollector
from app.ingestion.persistence import ingest_fundamentals, ingest_prices
from app.models.market_data import Stock

DEFAULT_UNIVERSE = [
    # Top IDX Bluechips
    ("BBCA", "Bank Central Asia Tbk", "Financials", "IDR"),
    ("BBRI", "Bank Rakyat Indonesia Tbk", "Financials", "IDR"),
    ("BMRI", "Bank Mandiri Tbk", "Financials", "IDR"),
    ("BBNI", "Bank Negara Indonesia Tbk", "Financials", "IDR"),
    ("TLKM", "Telkom Indonesia Tbk", "Infrastructure", "IDR"),
    ("ASII", "Astra International Tbk", "Industrials", "IDR"),
    ("UNVR", "Unilever Indonesia Tbk", "Consumer Non-Cyclicals", "IDR"),
    ("ICBP", "Indofood CBP Sukses Makmur Tbk", "Consumer Non-Cyclicals", "IDR"),
    # Global Giants
    ("AAPL", "Apple Inc.", "Technology", "USD"),
    ("NVDA", "NVIDIA Corporation", "Technology", "USD"),
    ("MSFT", "Microsoft Corporation", "Technology", "USD"),
]


def sync_market_data(symbols: list[str] | None = None, range_str: str = "1y") -> None:
    settings = get_settings()
    database = Database(settings)
    session = database.session()
    collector = LiveEodCollector()

    universe = DEFAULT_UNIVERSE
    if symbols:
        universe = [(s, f"{s} Equity", "General", "IDR" if s.endswith(".JK") else "USD") for s in symbols]

    print(f"Starting LIVE Market Data & Fundamentals Sync for {len(universe)} stocks (range={range_str})...")

    try:
        for sym, name, sector, currency in universe:
            clean_sym = sym.strip().upper()

            # 1. Upsert Stock Metadata
            stock = session.scalar(select(Stock).where(Stock.symbol == clean_sym))
            if not stock:
                stock = Stock(
                    symbol=clean_sym,
                    name=name,
                    currency=currency,
                    sector=sector,
                )
                session.add(stock)
                session.commit()
                print(f"Created stock entry: {clean_sym} ({name})")
            else:
                stock.name = name
                stock.sector = sector
                session.commit()

            # 2. Ingest Live Historical Prices
            try:
                records = collector.fetch_stock_prices(clean_sym, range_str=range_str)
                if records:
                    persisted = ingest_prices(session, records)
                    print(f"✓ {clean_sym}: Ingested {persisted} real historical candles")
                else:
                    print(f"⚠ {clean_sym}: No price candles returned")
            except Exception as err:
                print(f"✗ {clean_sym} Price sync failed: {err}")

            # 3. Ingest Live Fundamental Ratios
            try:
                fund_record = collector.fetch_fundamental_data(clean_sym)
                if fund_record:
                    ingest_fundamentals(session, [fund_record])
                    print(f"✓ {clean_sym}: Updated real financial fundamentals & valuation ratios")
            except Exception as err:
                print(f"✗ {clean_sym} Fundamental sync failed: {err}")

    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QuantLens Live Market Data Synchronizer")
    parser.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Optional comma-separated symbols. If empty, syncs default bluechip universe.",
    )
    parser.add_argument("--range", type=str, default="1y", help="Historical range (e.g. 6mo, 1y, 2y)")
    args = parser.parse_args()

    sym_list = [s.strip() for s in args.symbols.split(",") if s.strip()] or None
    sync_market_data(sym_list, range_str=args.range)
