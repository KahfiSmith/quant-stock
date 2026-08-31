"""Backfill stock summary (foreign flow) and broker summary from idx.co.id.

Usage::

    cd apps/quant-api
    python -m scripts.backfill_idx_data                        # yesterday only
    python -m scripts.backfill_idx_data --date 20260828        # specific date
    python -m scripts.backfill_idx_data --range 30             # last 30 trading days
    python -m scripts.backfill_idx_data --skip-broker          # stock summary only
    python -m scripts.backfill_idx_data --rate-limit 2.0       # slower requests
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from app.core.config import get_settings
from app.db.session import Database
from app.ingestion.idx_client import IDXClient
from app.ingestion.idx_collector import collect_broker_summary, collect_stock_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backfill_idx_data")


def _parse_date(value: str) -> date:
    return date(int(value[:4]), int(value[4:6]), int(value[6:8]))


def _trading_dates(start: date, end: date) -> list[date]:
    """Return weekdays between start and end (inclusive)."""
    dates: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Backfill IDX data from idx.co.id")
    parser.add_argument("--date", type=str, default=None, help="Single date YYYYMMDD")
    parser.add_argument("--range", type=int, default=None, help="Number of trading days to backfill (counting back from today)")
    parser.add_argument("--skip-broker", action="store_true", help="Skip broker summary collection")
    parser.add_argument("--skip-stock", action="store_true", help="Skip stock summary (foreign flow) collection")
    parser.add_argument("--rate-limit", type=float, default=1.5, help="Seconds between requests (default 1.5)")
    args = parser.parse_args(argv)

    settings = get_settings()
    database = Database(settings)

    if args.date:
        dates = [_parse_date(args.date)]
    elif args.range:
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=int(args.range * 1.5))
        dates = _trading_dates(start, end)[-args.range:]
    else:
        yesterday = date.today() - timedelta(days=1)
        dates = [yesterday] if yesterday.weekday() < 5 else []

    if not dates:
        logger.info("No trading dates to process.")
        return

    logger.info("IDX backfill: %d dates from %s to %s", len(dates), dates[0], dates[-1])

    client = IDXClient(rate_limit_seconds=args.rate_limit)
    total_stock = 0
    total_broker = 0

    for trade_date in dates:
        logger.info("--- Processing %s ---", trade_date)

        if not args.skip_stock:
            try:
                n = collect_stock_summary(database.session(), client, trade_date)
                total_stock += n
            except Exception:
                logger.exception("Failed stock summary for %s", trade_date)

        if not args.skip_broker:
            try:
                n = collect_broker_summary(database.session(), client, trade_date)
                total_broker += n
            except Exception:
                logger.exception("Failed broker summary for %s", trade_date)

    logger.info(
        "IDX backfill complete: %d stock summaries, %d broker summaries across %d dates",
        total_stock, total_broker, len(dates),
    )


if __name__ == "__main__":
    run()
