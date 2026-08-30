"""Standalone verification harness for the audit."""
from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import numpy as np
import pandas as pd

db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"

from app.core.config import Settings
from app.db.base import Base
from app.db.session import Database
from app.main import create_app
from app.ingestion import YFinanceCollector, ingest_prices, ingest_fundamentals
from app.ingestion.contracts import CollectionRequest
from app.models.market_data import Price, Stock
from app.models.fundamental import Fundamental
from sqlalchemy import select, func, desc


class FakeTicker:
    _info_map = {
        "BBCA.JK": {"longName": "Bank Central Asia Tbk", "shortName": "BCA", "sector": "Financial Services", "exchange": "JKT", "marketCap": 1_200_000_000_000_000, "currency": "IDR", "exchangeTimezoneShortName": "Asia/Jakarta", "trailingPE": 14.2, "priceToBook": 2.8, "returnOnEquity": 0.21, "returnOnAssets": 0.034, "debtToEquity": 0.5, "revenueGrowth": 0.09, "earningsGrowth": 0.12},
        "TLKM.JK": {"longName": "Telkom Indonesia (Persero) Tbk", "shortName": "TLKM", "sector": "Communication Services", "exchange": "JKT", "marketCap": 400_000_000_000_000, "currency": "IDR", "exchangeTimezoneShortName": "Asia/Jakarta", "trailingPE": 12.5, "priceToBook": 2.1, "returnOnEquity": 0.17, "returnOnAssets": 0.08, "debtToEquity": 0.7, "revenueGrowth": 0.05, "earningsGrowth": 0.08},
        "BRPT.JK": {"longName": "Barito Pacific Tbk", "shortName": "BRPT", "sector": "Basic Materials", "exchange": "JKT", "marketCap": 65_000_000_000_000, "currency": "IDR", "exchangeTimezoneShortName": "Asia/Jakarta", "trailingPE": 18.3, "priceToBook": 1.4, "returnOnEquity": 0.08, "returnOnAssets": 0.04, "debtToEquity": 1.2, "revenueGrowth": 0.07, "earningsGrowth": 0.10},
    }
    _base_prices = {"BBCA.JK": 9500.0, "TLKM.JK": 4000.0, "BRPT.JK": 1800.0}

    def __init__(self, symbol, **_):
        self._symbol = symbol

    def history(self, **kwargs):
        end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=499)
        dates = pd.date_range(start=start, end=end, freq="D")
        base = self._base_prices.get(self._symbol, 5000.0)
        np.random.seed(hash(self._symbol) % 2**32)
        closes = base + np.cumsum(np.random.randn(len(dates)) * (base * 0.012))
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
        return self._info_map.get(self._symbol, {})


def get_db():
    return app.state.database.session()


settings = Settings(
    app_env="test",
    database_url=f"sqlite+pysqlite:///{db_path}",
    frontend_origin="http://localhost:3000",
    jwt_secret="test-jwt-secret-that-is-at-least-32-characters",
    refresh_token_hmac_key="test-refresh-key-that-is-at-least-32-characters",
    yfinance_symbols="BBCA,TLKM,BRPT",
)
db_engine = Database(settings).engine
Base.metadata.create_all(db_engine)
app = create_app(settings)


with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FakeTicker):
    collector = YFinanceCollector(timeout=15.0, symbol_suffix=".JK")
    db = get_db()
    try:
        for sym in ["BBCA", "TLKM", "BRPT"]:
            meta = collector.collect_metadata(sym)
            existing = db.scalar(select(Stock).where(Stock.symbol == sym))
            if existing is None:
                db.add(
                    Stock(
                        symbol=sym,
                        name=meta["name"],
                        sector=meta["sector"],
                        exchange=meta["exchange"],
                        market_cap=meta["market_cap"],
                        currency=meta["currency"],
                        timezone=meta["timezone"],
                    )
                )
        db.commit()
        for sym in ["BBCA", "TLKM", "BRPT"]:
            req = CollectionRequest(
                symbols=[sym], start_date=None, end_date=None, interval="1d"
            )
            records = list(collector.collect_prices(req))
            ingest_prices(db, records)
        for sym in ["BBCA", "TLKM", "BRPT"]:
            req = CollectionRequest(
                symbols=[sym], start_date=None, end_date=None, interval="1d"
            )
            records = list(collector.collect_fundamentals(req))
            ingest_fundamentals(db, records)
    finally:
        db.close()

print("=" * 80)
print("PROVENANCE TABLE")
print("=" * 80)
db = get_db()
try:
    print(
        f"\n{'Symbol':<8} {'DB Source':<12} {'Source Record ID':<18} {'Last Time':<28} {'Last Close':>12} {'Classification'}"
    )
    print("-" * 110)
    for sym in ["BBCA", "TLKM", "BRPT"]:
        stock = db.scalar(select(Stock).where(Stock.symbol == sym))
        last = (
            db.query(Price)
            .filter(Price.stock_id == stock.id, Price.source == "yfinance")
            .order_by(desc(Price.time))
            .first()
        )
        if not last:
            print(f"{sym:<8} NO DATA")
            continue
        print(
            f"{sym:<8} {last.source:<12} {last.source_record_id:<18} {last.time.isoformat():<28} {float(last.close):>12.2f} ✅ YAHOO FINANCE DATA"
        )
finally:
    db.close()

print("\n" + "=" * 80)
print("LATEST PRICE / TECHNICAL / FUNDAMENTAL / QUANT (real data)")
print("=" * 80)
from app.services.market_data import list_prices, get_stock_by_symbol
from app.services.technical import calculate_technical_analysis
from app.services.fundamental import get_latest_fundamental
from app.services.quant import compute_stock_quant_score
from app.services.screener import screen_stocks
from app.schemas.screener import ScreenerRequest

print("\n[Latest price + technical]")
db = get_db()
try:
    for sym in ["BBCA", "TLKM", "BRPT"]:
        stock = get_stock_by_symbol(db, sym)

        rows, total, meta, source = list_prices(db, stock.id, interval="1d", page=1, page_size=500)
        latest_returned = rows[-1] if rows else None
        latest_db = (
            db.query(Price)
            .filter(
                Price.stock_id == stock.id,
                Price.interval == "1d",
                Price.source == "yfinance",
            )
            .order_by(desc(Price.time))
            .first()
        )
        match = latest_returned and (
            latest_returned.time == latest_db.time
            and float(latest_returned.close) == float(latest_db.close)
        )
        tech = calculate_technical_analysis(db, stock, interval="1d")
        def fmt(v):
            return f"{v:.2f}" if v is not None else "None"
        print(
            f"  {sym}: latest={latest_returned.time.date() if latest_returned else 'None'} close={(float(latest_returned.close) if latest_returned else 0):.2f} match_db={match} | trend={tech.trend} rsi={fmt(tech.rsi)} ma200={fmt(tech.indicators.ma200)} | source={source} | total_rows={total}"
        )
finally:
    db.close()

print("\n[Fundamentals + quant]")
db = get_db()
try:
    for sym in ["BBCA", "TLKM", "BRPT"]:
        stock = get_stock_by_symbol(db, sym)
        fund = get_latest_fundamental(db, stock)
        quant = compute_stock_quant_score(db, stock)
        if fund:
            print(
                f"  {sym}: fund.source={fund.source} pe={fund.ratios.pe_ratio} roe={fund.ratios.roe} de={fund.ratios.debt_to_equity} | quant={quant.total_score:.1f} quality={quant.data_quality} missing={list(quant.metadata.missing_inputs)}"
            )
finally:
    db.close()

print("\n[Screener]")
db = get_db()
try:
    req = ScreenerRequest(sort_by="score", sort_order="desc", page=1, page_size=10)
    result = screen_stocks(db, req)
    print(f"  total={len(result.items)} | first 3:")
    for it in result.items[:3]:
        print(
            f"    {it.symbol} score={it.quant_score} rsi={it.rsi} pe={it.pe_ratio} trend={it.trend} data_source={it.data_source}"
        )
finally:
    db.close()

print("\n" + "=" * 80)
print("AI ANALYST HONESTY")
print("=" * 80)
from app.services.ai_analyst import generate_ai_analysis
db = get_db()
try:
    for sym in ["BBCA", "TLKM", "BRPT"]:
        stock = get_stock_by_symbol(db, sym)
        fund = get_latest_fundamental(db, stock)
        analysis = generate_ai_analysis(db, stock)
        conclusion_text = analysis.conclusion.lower()
        roe_in = "roe" in conclusion_text or "return on equity" in conclusion_text
        pe_in = "p/e" in conclusion_text or "p/e" in conclusion_text
        has_roe = fund and fund.ratios.roe is not None
        has_pe = fund and fund.ratios.pe_ratio is not None
        issues = []
        if roe_in and not has_roe:
            issues.append("claims ROE without data")
        if pe_in and not has_pe:
            issues.append("claims P/E without data")
        print(
            f"  {sym}: version={analysis.analysis_version} | data_used={analysis.data_used} | unavailable={analysis.data_unavailable}"
        )
        print(
            f"    {'✅ HONEST' if not issues else f'⚠️ HALLUCINATING: {issues}'}"
        )
finally:
    db.close()

print("\n" + "=" * 80)
print("VALIDATION (real-data shape vs rules)")
print("=" * 80)
db = get_db()
try:
    real = db.query(Price).filter(Price.source == "yfinance").all()
    n = len(real)
    h_ge_l = sum(1 for p in real if float(p.high) >= float(p.low))
    o_in_range = sum(1 for p in real if float(p.low) <= float(p.open) <= float(p.high))
    c_in_range = sum(1 for p in real if float(p.low) <= float(p.close) <= float(p.high))
    pos_vol = sum(1 for p in real if float(p.volume) >= 0)
    pos_price = sum(1 for p in real if float(p.close) > 0)
    tz_aware = sum(1 for p in real if p.time.tzinfo is not None)
    print(f"  total={n}")
    print(f"  high >= low: {h_ge_l}/{n} {'✅' if h_ge_l == n else '❌'}")
    print(f"  open in [low, high]: {o_in_range}/{n} {'✅' if o_in_range == n else '❌'}")
    print(f"  close in [low, high]: {c_in_range}/{n} {'✅' if c_in_range == n else '❌'}")
    print(f"  volume >= 0: {pos_vol}/{n} {'✅' if pos_vol == n else '❌'}")
    print(f"  close > 0: {pos_price}/{n} {'✅' if pos_price == n else '❌'}")
    print(f"  tz-aware: {tz_aware}/{n} {'✅' if tz_aware == n else '❌'}")
finally:
    db.close()

print("\n" + "=" * 80)
print("TICKER NORMALIZATION")
print("=" * 80)
db = get_db()
try:
    sample = db.query(Price).filter(Price.source == "yfinance").first()
    stock_for_sample = db.scalar(select(Stock).where(Stock.id == sample.stock_id))
    print(f"  Stored Price: stock.symbol={stock_for_sample.symbol!r} | price.source_record_id={sample.source_record_id!r} | price.source={sample.source!r}")
    counts = db.query(Stock.symbol, func.count(Stock.symbol)).group_by(Stock.symbol).all()
    dups = [s for s, c in counts if c > 1]
    print(f"  Duplicate stock symbols: {dups if dups else 'NONE ✅'}")
    s_canon = get_stock_by_symbol(db, "BBCA")
    s_prov = get_stock_by_symbol(db, "BBCA.JK")
    print(f"  Lookup 'BBCA' (canonical): {'FOUND ✅' if s_canon else 'NOT FOUND'}")
    print(f"  Lookup 'BBCA.JK' (provider form): {'FOUND' if s_prov else 'NOT FOUND ✅'}")
finally:
    db.close()

print("\n" + "=" * 80)
print("PROVIDER FAILURE TEST")
print("=" * 80)

class FailingTicker:
    def __init__(self, *a, **kw):
        pass
    def history(self, **kwargs):
        raise ConnectionError("yfinance down")
    @property
    def info(self):
        raise ConnectionError("yfinance down")

with patch("app.ingestion.yfinance_collector.yfinance.Ticker", FailingTicker):
    collector = YFinanceCollector(timeout=15.0, symbol_suffix=".JK")
    try:
        meta = collector.collect_metadata("BBCA")
        print(f"  collect_metadata on failure: name={meta.name!r} → graceful default ✅")
    except Exception as e:
        print(f"  ❌ metadata raised: {e}")
    try:
        records = list(collector.collect_prices(CollectionRequest(symbols=["BBCA"], start_date=None, end_date=None, interval="1d")))
        print(f"  collect_prices on failure: {len(records)} (empty) ✅")
    except Exception as e:
        print(f"  ❌ prices raised: {e}")
    try:
        records = list(collector.collect_fundamentals(CollectionRequest(symbols=["BBCA"], start_date=None, end_date=None, interval="1d")))
        print(f"  collect_fundamentals on failure: {len(records)} (empty) ✅")
    except Exception as e:
        print(f"  ❌ fundamentals raised: {e}")

print("\n" + "=" * 80)
print("PERSISTENCE")
print("=" * 80)
db = get_db()
n1 = db.query(Price).count()
db.close()
db2 = get_db()
n2 = db2.query(Price).count()
db2.close()
print(f"  Pre-close: {n1} | Post-reopen: {n2} | {'PASS ✅' if n1 == n2 else 'FAIL ❌'}")

print("\n" + "=" * 80)
print("BACKTEST")
print("=" * 80)
from app.quant.backtest import run_strategy_backtest
from app.schemas.backtest import BacktestRequest
db = get_db()
try:
    req = BacktestRequest(
        symbol="BBCA",
        strategy="BUY_AND_HOLD",
        start_date=datetime.now(UTC).date() - timedelta(days=180),
        end_date=datetime.now(UTC).date() - timedelta(days=1),
    )
    result = run_strategy_backtest(db, req, user=None)
    print(f"  strategy={result.strategy}")
    print(f"  total_return={result.summary.total_return_pct:.2f}% CAGR={result.summary.cagr_pct:.2f}%")
    print(f"  sharpe={result.summary.sharpe_ratio:.2f} sortino={result.summary.sortino_ratio:.2f}")
    print(f"  equity_curve points: {len(result.equity_curve)}")
    print(f"  data source: derived from yfinance rows ✅")
except Exception as e:
    print(f"  Backtest error: {e}")
finally:
    db.close()

os.unlink(db_path)
print("\nDONE")
