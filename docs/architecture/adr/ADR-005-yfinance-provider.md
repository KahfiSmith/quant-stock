# ADR-005: yfinance as the Production Market Data Provider

- **Status:** Accepted
- **Date:** 2026-08-27
- **Supersedes:** None
- **Related:** Phase 2 of `docs/product/quantlens-spec.md`; `docs/features/market-data.md`

## Context

The market data ingestion pipeline (`apps/quant-api/app/ingestion/`) was scaffolded
with a `MarketDataCollector` Protocol, a strict validation layer
(`validate_price_batch` / `validate_fundamental`), and an idempotent UPSERT
(`ingest_prices` / `ingest_fundamentals`). The persistence path was production-ready.
However, the only way to populate the database was a synthetic 15-day seeder
(`scripts/seed_market_data.py`) that hardcoded 3 IDX symbols (BBCA, TLKM, ASII)
with a `source="sample"` watermark.

This made the product's headline features (technical analysis with MA200,
quant scoring, backtest with at least 1-year lookback, AI Analyst citing
fundamentals) **impossible to validate end-to-end** — the data simply did not
exist. The `docs/features/market-data.md` doc explicitly marked
"Real provider activation: BLOCKED" and the spec called out
"Resolve data-provider decision" as a Phase 2 prerequisite.

A decision was needed: which data source should feed the system, and how
should the team deal with licensing, rate limits, and staleness?

## Decision

**Use `yfinance` (the unofficial Python wrapper around Yahoo Finance) as the
default market data source** for IDX-listed stocks, via a new
`YFinanceCollector` class that implements the existing `MarketDataCollector`
Protocol. Initial backfill covers 20 IDX liquid stocks across 5 sectors over
the past 2 years (~500 daily bars each). Ingestion is triggered by a new CLI
script, `scripts/backfill_market_data.py`, run manually during development.
A future scheduler (cron) can call the same script for daily refresh.

### Why yfinance

| Criterion | yfinance | Alpha Vantage (free) | IDX direct feed |
|---|---|---|---|
| Cost | Free | Free (25 req/day cap) | Paid |
| API key required | No | Yes | Yes + contract |
| IDX coverage | ✅ via `.JK` suffix | ⚠️ limited for IDX | ✅ official |
| Historical depth | 10+ years | ~5 years (free tier) | Configurable |
| Real-time | ❌ EOD with 1-day lag | ❌ delayed | ✅ |
| Rate limit | ~2000 req/h (unofficial) | 25 req/day, 5 req/min | Per contract |
| Maintenance risk | Yahoo can break the API | Stable, official | Stable |

For the project's current goals (development, validation of quant engine,
backtest, AI analyst) the trade-off is favorable: free, no API key, sufficient
history. The 1-day EOD lag is acceptable — the screener, technical
indicators, and backtest all operate on daily bars.

### Why a CLI script instead of an admin endpoint

The `backtest_jobs` table added in migration `0010_backtest_jobs.py` is the
infrastructure for long-running async work, but no scheduler, admin route,
or job runner exists yet. Building those pieces for ingestion alone would
add auth, rate limiting, and observability work that the spec defers to
Phase 8/9. A CLI mirrors the existing `seed_market_data.py` pattern and
is the smallest correct change.

### Configuration

- `MARKET_DATA_PROVIDER=yfinance` (default) — selects the provider.
- `MARKET_DATA_PROVIDER=sample` — falls back to the synthetic seeder
  for offline development without network access.
- `YFINANCE_SYMBOLS` — comma-separated symbol list (20 by default).
- `YFINANCE_DEFAULT_PERIOD` — history depth (default `2y`).
- `YFINANCE_SYMBOL_SUFFIX` — exchange suffix (default `.JK` for IDX).
- `YFINANCE_ENABLED` — kill switch; if `false`, the script aborts fast.
- `YFINANCE_PROXY` — optional HTTP proxy for restricted networks.

### Data shape

- Prices: `interval="1d"`, `source="yfinance"`, `auto_adjust=True` (split
  and dividend adjusted). The OHLCV values are stored as received; the
  `auto_adjust=True` choice means backtest PnL is on a logical
  (not raw) series. Documented in the market-data feature doc.
- Fundamentals: `period_type="TTM"`, `period_end=today()` for the snapshot.
  Only the 7 ratio fields consumed by the quant engine are extracted
  (`pe_ratio`, `pb_ratio`, `roe`, `roa`, `debt_to_equity`, `revenue_growth`,
  `eps_growth`). All other `info` keys are discarded.
- The `debtToEquity` field is normalized: if the value > 5, it's divided
  by 100 (yfinance occasionally returns a percentage for some exchanges).
- Stock metadata (`name`, `sector`, `exchange`, `market_cap`, `currency`,
  `timezone`) is fetched from `ticker.info` and upserted into the `stocks`
  table on every backfill.

### Idempotency

The script can be run multiple times safely:
- `ingest_prices` UPSERTs on `(stock_id, time, interval, source)`. Existing
  rows get updated provenance (`retrieved_at`, `payload_checksum`) but
  the OHLCV values are preserved (audit integrity). A new
  `source="yfinance_v2"` could be introduced later if revisions need to
  overwrite existing bars.
- `ingest_fundamentals` UPSERTs on `(stock_id, period_end, period_type)`
  and updates the metrics in place.

## Consequences

### Positive

- All headline features (chart, technical, quant, backtest, AI analyst)
  now have real data to work against. No code changes to the frontend
  or service layer were required.
- Free, no API key, no signup. Lowers the barrier for new contributors.
- The `MarketDataCollector` Protocol proved its value: a new collector
  was added with zero changes to the persistence/validation/route layers.
- Idempotent re-runs make daily refresh trivial: cron + the same script.

### Negative / Risks

- **Yahoo can break yfinance at any time.** It is an unofficial
  reverse-engineered client. A future yfinance version, a Yahoo
  endpoint change, or a rate-limit escalation could break ingestion.
  Mitigated by: pinning yfinance version (`==0.2.40`), unit tests
  with mocked yfinance, and the easy rollback to `MARKET_DATA_PROVIDER=sample`.
- **No real-time data.** EOD with 1 trading day lag. The screener and
  backtest are unaffected (daily bars), but intraday charting and
  tick-level backtesting are not possible. Out of scope for the current
  product phase.
- **`debtToEquity` unit ambiguity.** yfinance returns the field
  inconsistently across exchanges. Auto-detected (value > 5 → divide
  by 100) and tested, but a future yfinance version could shift the
  threshold. ADR-006 will revisit if this drifts.
- **Front-end "All" range silently truncates to 200 rows.** The chart
  route's `page_size` cap (`market_data.py:54`) means the "All" button
  only shows the oldest 200 bars even when ~500 are available. Not
  fixed by this ADR — out of scope; the "1Y" range button works
  correctly.
- **Hardcoded annualization constants in backtest** (`252` trading days,
  `0.05` risk-free rate) are USD-oriented. With IDR data the Sharpe/Sortino
  values will be slightly off. Out of scope; flagged in
  `docs/product/quantlens-spec.md`.
- **20-stock universe is a curated subset.** True IDX has ~800 listed
  stocks. The screener will work for the 20 we backfill; the rest will
  appear as "unknown symbol" until they are added to `YFINANCE_SYMBOLS`
  and the script is re-run. Expanding the universe is a one-line env
  change with no code change.

## Rollback

To revert to the synthetic seeder:

1. Set `MARKET_DATA_PROVIDER=sample` in `apps/quant-api/.env`.
2. Run `python -m scripts.seed_market_data` to repopulate.
3. The `source="yfinance"` rows are not deleted; they coexist in the
   database and are simply not the active source.

No code changes are required for rollback.

## Future work

- **Scheduler** (cron, systemd timer, or APScheduler) to run
  `backfill_market_data` daily after IDX close (16:00 WIB / 09:00 UTC).
- **Admin POST endpoint** (`POST /api/v1/admin/ingest`) behind auth,
  likely piggybacking on the backtest_jobs infrastructure.
- **Adjusted-close column** on `Price` if raw prices are ever needed
  alongside adjusted.
- **Expansion** to all IDX liquid stocks (top 50 by market cap) once
  the rate limit and operational overhead are validated.
- **ADR-006** if the data provider or staleness policy needs to change
  (e.g. paid real-time feed).
