"""Backfill IDX market data from yfinance into the local database.

This is the production data ingestion path (replaces the sample seeder for
non-development usage). Run from ``apps/quant-api`` with the virtualenv
activated::

    python -m scripts.backfill_market_data

The default symbol list is read from ``YFINANCE_SYMBOLS`` in
``apps/quant-api/.env``. Pass ``--symbols`` to override, e.g.::

    python -m scripts.backfill_market_data --symbols BBCA,BMRI --period 5y
    python -m scripts.backfill_market_data --skip-fundamentals

Per-symbol failures (e.g. ticker delisted, no fundamentals on yfinance) are
logged and the run continues for the remaining symbols.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import Database
from app.ingestion import (
    YFinanceCollector,
    ingest_fundamentals,
    ingest_prices,
)
from app.ingestion.contracts import CollectionRequest
from app.models.market_data import Stock

logger = logging.getLogger("scripts.backfill_market_data")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Backfill IDX market data from yfinance",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=",".join(settings.yfinance_symbols_list),
        help="Comma-separated symbol list. Defaults to YFINANCE_SYMBOLS env.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default=settings.yfinance_default_period,
        help="yfinance history period (e.g. 1y, 2y, 5y, max).",
    )
    parser.add_argument(
        "--skip-fundamentals",
        action="store_true",
        help="Only ingest OHLCV prices, skip fundamental ratios.",
    )
    parser.add_argument(
        "--skip-prices",
        action="store_true",
        help="Only ingest fundamentals and stock metadata, skip OHLCV.",
    )
    parser.add_argument(
        "--rate-limit-seconds",
        type=float,
        default=1.0,
        help="Sleep between symbols (seconds). Default 1.0; set 0 to disable.",
    )
    return parser.parse_args(argv)


def _ensure_stocks(db, collector: YFinanceCollector, symbols: list[str]) -> dict[str, int]:
    """Upsert Stock rows. Returns {symbol: stock_id} for symbols that were
    successfully resolved (metadata fetched and row committed)."""
    resolved: dict[str, int] = {}
    for symbol in symbols:
        existing = db.scalar(select(Stock).where(Stock.symbol == symbol))
        meta = collector.collect_metadata(symbol)
        name = meta.get("name") or symbol
        sector = meta.get("sector")
        exchange = "IDX"
        market_cap = meta.get("market_cap")
        currency = str(meta.get("currency") or "IDR")
        timezone = str(meta.get("timezone") or "Asia/Jakarta")

        if existing is None:
            stock = Stock(
                symbol=symbol,
                name=str(name),
                sector=str(sector) if sector else None,
                exchange=str(exchange) if exchange else None,
                market_cap=market_cap,
                currency=currency,
                timezone=timezone,
            )
            db.add(stock)
            db.flush()
            logger.info("Created stock %s (%s)", symbol, name)
        else:
            existing.name = str(name)
            if sector:
                existing.sector = str(sector)
            if exchange:
                existing.exchange = str(exchange)
            if market_cap is not None:
                existing.market_cap = market_cap
            if currency:
                existing.currency = currency
            if timezone:
                existing.timezone = timezone
            db.flush()
            logger.info("Updated stock %s (%s)", symbol, name)
        resolved[symbol] = int(existing.id if existing else stock.id)
    db.commit()
    return resolved


def run(argv: Sequence[str] | None = None, settings=None, db=None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if settings is None:
        settings = get_settings()

    if not settings.yfinance_enabled:
        logger.error("yfinance is disabled via YFINANCE_ENABLED=false; aborting.")
        return 2

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        logger.error("No symbols to ingest; pass --symbols or set YFINANCE_SYMBOLS.")
        return 2

    logger.info(
        "Backfilling %d symbols (period=%s, prices=%s, fundamentals=%s)",
        len(symbols),
        args.period,
        not args.skip_prices,
        not args.skip_fundamentals,
    )

    collector = YFinanceCollector(
        timeout=settings.yfinance_request_timeout_seconds,
        symbol_suffix=settings.yfinance_symbol_suffix,
        proxy=settings.yfinance_proxy,
    )
    if db is None:
        db = Database(settings).session()
    try:


        start_date = None
        if args.period.endswith("y") and args.period[:-1].isdigit():
            years = int(args.period[:-1])
            start_date = (datetime.now(UTC) - timedelta(days=365 * years)).date()
        elif args.period.endswith("mo") and args.period[:-2].isdigit():
            months = int(args.period[:-2])
            start_date = (
                datetime.now(UTC) - timedelta(days=30 * months)
            ).date()


        _ensure_stocks(db, collector, symbols)


        price_count = 0
        if not args.skip_prices:
            for i, symbol in enumerate(symbols):
                if i > 0 and args.rate_limit_seconds > 0:
                    time.sleep(args.rate_limit_seconds)
                request = CollectionRequest(
                    symbols=[symbol],
                    start_date=start_date,
                    end_date=None,
                    interval="1d",
                )
                try:
                    records = list(collector.collect_prices(request))
                    if not records:
                        logger.warning("No price rows for %s; skipping.", symbol)
                        continue
                    persisted = ingest_prices(db, records)
                    price_count += persisted
                    logger.info("%s: %d price rows ingested.", symbol, persisted)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Price ingestion failed for %s: %s", symbol, exc)


        fund_count = 0
        if not args.skip_fundamentals:
            for i, symbol in enumerate(symbols):
                if i > 0 and args.rate_limit_seconds > 0:
                    time.sleep(args.rate_limit_seconds)
                request = CollectionRequest(
                    symbols=[symbol],
                    start_date=None,
                    end_date=None,
                    interval="1d",
                )
                try:
                    records = list(collector.collect_fundamentals(request))
                    if not records:
                        logger.warning("No fundamental rows for %s; skipping.", symbol)
                        continue
                    persisted = ingest_fundamentals(db, records)
                    fund_count += persisted
                    logger.info("%s: %d fundamental rows ingested.", symbol, persisted)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Fundamental ingestion failed for %s: %s", symbol, exc)

        logger.info(
            "Backfill complete. %d price rows, %d fundamental rows across %d symbols.",
            price_count,
            fund_count,
            len(symbols),
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
