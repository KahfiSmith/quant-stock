"""IDX data collector: ingests stock summary (foreign flow) and broker summary
from the idx.co.id public API into the local database.

Usage is through the ``collect_stock_summary`` and ``collect_broker_summary``
functions, which accept a SQLAlchemy Session and an ``IDXClient`` instance.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.idx_client import IDXClient, checksum_for_record
from app.models.idx_models import BrokerSummaryIDX, MarketFlowIDX
from app.models.market_data import Stock

logger = logging.getLogger(__name__)


def collect_stock_summary(
    db: Session,
    client: IDXClient,
    trade_date: date,
) -> int:
    """Fetch daily stock summary from idx.co.id and upsert foreign flow data.

    Returns the number of records persisted.
    """
    rows = client.get_stock_summary(trade_date)
    if not rows:
        logger.warning("IDX stock summary: no data for %s", trade_date)
        return 0

    persisted = 0
    for row in rows:
        symbol = (row.get("StockCode") or "").strip().upper()
        if not symbol:
            continue

        stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
        if stock is None:
            continue

        foreign_buy = float(row.get("ForeignBuy") or 0)
        foreign_sell = float(row.get("ForeignSell") or 0)
        volume = float(row.get("Volume") or 0)

        existing = db.scalar(
            select(MarketFlowIDX).where(
                MarketFlowIDX.stock_id == stock.id,
                MarketFlowIDX.date == trade_date,
            )
        )

        data = {
            "foreign_buy_value": foreign_buy,
            "foreign_sell_value": foreign_sell,
            "net_foreign_value": foreign_buy - foreign_sell,
            "foreign_buy_volume": volume if foreign_buy > 0 else 0,
            "foreign_sell_volume": volume if foreign_sell > 0 else 0,
        }

        if existing is None:
            db.add(
                MarketFlowIDX(
                    stock_id=stock.id,
                    date=trade_date,
                    **data,
                )
            )
        else:
            for key, value in data.items():
                setattr(existing, key, value)
        persisted += 1

    db.commit()
    logger.info("IDX stock summary: persisted %d records for %s", persisted, trade_date)
    return persisted


def collect_broker_summary(
    db: Session,
    client: IDXClient,
    trade_date: date,
) -> int:
    """Fetch broker-level trading summary from idx.co.id and upsert.

    Returns the number of records persisted.
    """
    rows = client.get_broker_summary(trade_date)
    if not rows:
        logger.warning("IDX broker summary: no data for %s", trade_date)
        return 0

    persisted = 0
    for row in rows:
        broker_code = (row.get("IDFirm") or "").strip().upper()
        broker_name = (row.get("FirmName") or "").strip()
        if not broker_code:
            continue

        existing = db.scalar(
            select(BrokerSummaryIDX).where(
                BrokerSummaryIDX.broker_code == broker_code,
                BrokerSummaryIDX.date == trade_date,
            )
        )

        data = {
            "broker_name": broker_name,
            "total_value": float(row.get("Value") or 0),
            "volume": float(row.get("Volume") or 0),
            "frequency": int(row.get("Frequency") or 0),
            "source": "idx_web",
        }

        if existing is None:
            db.add(
                BrokerSummaryIDX(
                    broker_code=broker_code,
                    date=trade_date,
                    **data,
                )
            )
        else:
            for key, value in data.items():
                setattr(existing, key, value)
        persisted += 1

    db.commit()
    logger.info("IDX broker summary: persisted %d records for %s", persisted, trade_date)
    return persisted
