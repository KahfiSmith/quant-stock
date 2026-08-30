# Feature: Market Data

**Feature ID:** market-data
**Status:** COMPLETE — yfinance collector live (see ADR-005)
**Owner:** engineer
**Risk:** medium
**Routes:** `(dashboard)/stocks`, `(dashboard)/stocks/[symbol]`
**Related docs:** [API overview](../api/overview.md), [Database schema](../database/schema.md), [ADR-005](../architecture/adr/ADR-005-yfinance-provider.md)

Date: 2026-08-27
Related issue/PR: N/A

## Objective

Provide a read-only view of a stock universe and per-symbol price history, so an
authenticated user can browse stocks and inspect a candlestick chart. The
ingestion pipeline is wired to **yfinance** (see ADR-005), which provides
real 2-year daily OHLCV history and TTM fundamentals for 20 IDX liquid stocks.

## Overview

Users reach a protected stock list (`/stocks`) and a symbol detail page
(`/stocks/[symbol]`) that renders historical candles with TradingView Lightweight
Charts. The backend exposes `GET /api/v1/stocks` and
`GET /api/v1/stocks/{symbol}/prices` backed by the new `stocks` and `prices`
tables. The `prices.source` column carries `"yfinance"` for real data and
`"sample"` for the development seeder (legacy, queryable but unused by default).

## Constraints

- Architecture constraints: fence market-data access behind `src/lib/api` and
  feature hooks; pages reuse the shared `RequireAuth` guard.
- Product/runtime constraints: prices carry an explicit `data_source` and `as_of`.
  yfinance data is end-of-day with a 1-trading-day lag; not suitable for
  intraday or tick-level strategies.
- Price and fundamental responses expose source-record, retrieval, checksum/version,
  and validation metadata.
- Provider-neutral ingestion contracts, OHLCV validation, provenance, and idempotent
  persistence are implemented; `YFinanceCollector` is the production collector.
- The screener, quant score, fundamentals, backtest, and AI summary now operate
  on real IDX market data.
- Real-time streaming is OUT OF SCOPE.

## Impact Areas

- API/endpoints: yes (six endpoints under `/api/v1/stocks`)
- Auth/session/RBAC: yes (protected pages and most market-data endpoints)
- State/store: no
- Env/config/secrets: yes (new `YFINANCE_*` env vars; see ADR-005)
- Observability/logging: yes (per-symbol ingestion log lines in the backfill script)
- External integrations: yes (TradingView Lightweight Charts, yfinance)
- CI/release/harness: yes (added unit + integration tests for the collector)

## Core flow

```text
user -> /stocks or /stocks/[symbol] -> RequireAuth (client guard)
     -> market hook (useStocks / useStockPrices)
        -> apiClient (Bearer token)
           -> FastAPI /api/v1/stocks[/{symbol}/prices]
              -> envelope -> React Query cache -> StockList / StockChart

ingestion (off-request, manual / scheduled):
  python -m scripts.backfill_market_data
    -> YFinanceCollector.collect_metadata / collect_prices / collect_fundamentals
       -> ingest_prices / ingest_fundamentals (idempotent UPSERT)
          -> PostgreSQL/TimescaleDB
```

## Flow states

1. `checking` session -> loading state inside the guard.
2. Data `isPending` -> spinner.
3. Data error -> inline error state.
4. Empty universe / no candles -> empty state.
5. Success -> table or candlestick chart.

## Implementation map

| Concern | Files |
|---|---|
| Route / Page | `src/app/(dashboard)/stocks/page.tsx`, `src/app/(dashboard)/stocks/[symbol]/page.tsx` |
| UI components | `src/components/features/market/` |
| Hooks | `src/hooks/market/` |
| API client / Endpoints | `src/lib/api/endpoints.ts`, `src/lib/api/query-keys.ts` |
| Types | `src/types/market.types.ts` |
| Backend routes | `apps/quant-api/app/api/routes/market_data.py` |
| Backend service | `apps/quant-api/app/services/market_data.py` |
| Backend models / migration | `apps/quant-api/app/models/market_data.py`, `apps/quant-api/alembic/versions/0002_market_data.py` |
| Ingestion protocol | `apps/quant-api/app/ingestion/contracts.py` |
| Ingestion collector | `apps/quant-api/app/ingestion/yfinance_collector.py` |
| Ingestion validation | `apps/quant-api/app/ingestion/validation.py` |
| Ingestion persistence | `apps/quant-api/app/ingestion/persistence.py` |
| Backfill CLI | `apps/quant-api/scripts/backfill_market_data.py` |
| Settings | `apps/quant-api/app/core/config.py` |
| Tests | `apps/quant-api/tests/test_yfinance_collector.py`, `apps/quant-api/tests/test_backfill_script.py` |

## Endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `GET` | `/api/v1/stocks` | List/search the stock universe | Optional (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/prices` | Historical OHLCV candles | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/technical` | Technical indicators (MA, RSI, MACD, BB, ATR) plus volume analysis (Z-Score, SMA ratio) and volatility regime (ATR%, classification) | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/fundamental` | Fundamental ratios and financial metrics | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/score` | Multi-factor composite score and factor breakdown | Required (Bearer) |
| `POST` | `/api/v1/screener` | Multi-parameter stock screening and ranking; includes `volume_momentum` preset and volume/volatility filter dimensions | Required (Bearer) |
| `GET` | `/api/v1/portfolios` | List user portfolios | Required (Bearer) |
| `POST` | `/api/v1/portfolios` | Create a new portfolio | Required (Bearer) |
| `GET` | `/api/v1/portfolios/{id}` | Portfolio detail and computed holdings PnL | Required (Bearer) |
| `POST` | `/api/v1/portfolios/{id}/transactions` | Add BUY/SELL transaction | Required (Bearer) |
| `POST` | `/api/v1/backtest` | Run historical quantitative strategy backtest | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/ai-summary` | Automated structured AI analyst synthesis (real data, deterministic rule-based) | Required (Bearer) |

Responses use the standard `ApiResponse` envelope. Prices include `as_of`,
`data_source` (`"yfinance"` or `"sample"`), and ingestion provenance fields.
Fundamental responses include reporting period, currency, units, source,
retrieval, checksum, and validation fields. Quant scores include
model/weight/normalization/input metadata; AI summaries include supporting
evidence and data availability metadata.

## Acceptance Criteria

1. An authenticated user can list the real IDX universe (20 stocks) and
   open a symbol detail page.
2. Prices render as a candlestick chart with ~500 daily bars (2 years),
   loading/error/empty states.
3. Unknown symbols return a `404 SYMBOL_NOT_FOUND` envelope.
4. The prices endpoint rejects unauthenticated requests.
5. The technical endpoint returns non-`None` MA20, MA50, MA200, RSI(14),
   MACD, ATR, Bollinger, volume Z-Score, volume SMA ratio, ATR%, and
   volatility regime values for symbols with ≥ 200 bars.
6. The backtest endpoint produces a non-trivial Sharpe/Sortino ratio for
   a 1-year window on real data.
7. The AI Analyst tab cites real ROE / P/E / trend values for any symbol
   with both prices and fundamentals ingested.

## Implementation Checklist

- [x] Backend `stocks`/`prices` models + migration 0002
- [x] Backend service, routes, and FastAPI wiring
- [x] Backend tests
- [x] Frontend types, endpoints, query keys, hooks
- [x] `StockList`, `StockChart`, `StockDetail` components
- [x] `/stocks` and `/stocks/[symbol]` pages
- [x] `MarketDataCollector` Protocol extended with `collect_fundamentals`
- [x] `YFinanceCollector` implementing the Protocol
- [x] `scripts/backfill_market_data.py` CLI for 2y backfill of 20 IDX stocks
- [x] `YFINANCE_*` env config in `app/core/config.py`
- [x] `yfinance==0.2.40` pinned in `apps/quant-api/requirements.txt`
- [x] Unit + integration tests for the collector and backfill script
- [x] ADR-005 documenting provider choice

## Decision Log

- 2026-08-25: Reuse the `(dashboard)` route group -> avoids a new route-group
  gate and reuses `RequireAuth`.
- 2026-08-25: Schema-first slice with labeled `source="sample"` seed -> proves
  the full stack without waiting on a provider, and never presents placeholder
  data as real.
- 2026-08-26: Pure indicator calculations in `app/technical/indicators.py` -> no
  unmaintained pandas-ta dependency, returns `None` when lookback history is insufficient.
- 2026-08-27: Provider-neutral ingestion contract and persistence boundary added.
- 2026-08-27: **ADR-005: yfinance chosen as production data source.** 2-year
  backfill of 20 IDX liquid stocks; CLI-driven ingestion; idempotent re-runs.
- 2026-08-30: **Tier 1 Quant Engine**: Volume Anomaly Z-Score, Volatility Regime
  Detection, and enhanced screener added to technical/screener endpoints. Computed
  from existing OHLCV data — no new dependencies or migrations required.

## Verification

```bash
cd apps/quant-api && .venv/bin/pytest -q   # 68 tests incl. ingestion, technical, yfinance collector
cd apps/quant-api && .venv/bin/ruff check .
# Backfill (real network; ~2 minutes for 20 stocks):
cd apps/quant-api && python -m scripts.backfill_market_data
# Sanity check rows in the DB:
psql -h localhost -U quantlens -d quantlens -c \
  "SELECT symbol, COUNT(*) FROM stocks JOIN prices ON prices.stock_id=stocks.id WHERE prices.source='yfinance' GROUP BY symbol;"
pnpm lint && pnpm type-check && pnpm docs:check && pnpm test && pnpm build
```

## Runtime Evidence

- Environment: local Docker Compose (Next.js, FastAPI, PostgreSQL/TimescaleDB).
- Dependencies/services: real yfinance data via `python -m scripts.backfill_market_data`.
  Falls back to `python -m scripts.seed_market_data` if `MARKET_DATA_PROVIDER=sample`.
- Executed request/flow: `GET /api/v1/stocks`, `GET /api/v1/stocks/BBCA/prices`.
- Relevant logs/request IDs: per-symbol ingestion lines in the backfill output
  (e.g., `BBCA: 487 price rows ingested.`, `TLKM: 1 fundamental rows ingested.`).
- Notes: chart, technical, fundamental, quant, screener, backtest, and AI
  Analyst tabs all render real data after a backfill.

## Risks And Mitigations

- Risk: `prices` is a hypertable only on Postgres; SQLite tests use a plain table.
  - Mitigation: dialect-guarded `create_hypertable` in migration 0002.
- Risk: yfinance is an unofficial Yahoo scraper and can break.
  - Mitigation: pinned `yfinance==0.2.40`; unit tests with mocked yfinance;
    set `MARKET_DATA_PROVIDER=sample` to roll back.
- Risk: 1-day EOD lag could surprise users expecting intraday data.
  - Mitigation: documented in this file and in ADR-005; the price response
    carries `as_of` so the UI can surface staleness.
- Risk: 20-stock curated universe is a subset of the full IDX (~800 stocks).
  - Mitigation: adding more symbols is a one-line change to `YFINANCE_SYMBOLS`
    followed by a re-run of the backfill script.

## Completion Notes

Shipped the full Phase 2 Market Data system: schema, migrations, ingestion
contracts, real-data collector (yfinance), persistence, validation, CLI
backfill, and full test coverage. The product's downstream features
(technical analysis with MA200, multi-factor quant scoring, 1Y backtest,
AI Analyst) are now backed by real IDX market data and produce
meaningful output for the 20-stock universe.

## Follow-Ups

- [ ] Cron / scheduler for daily EOD refresh after IDX close.
- [ ] Admin POST endpoint to trigger backfill from the UI
      (likely piggybacks on the `backtest_jobs` table).
- [ ] Add pagination/date-range controls to the chart page.
- [ ] Deduplicate the loading/error/empty UI into a shared component.
- [ ] Expand the universe beyond 20 stocks once the rate limit and
      operational overhead of the current setup are validated.