# Feature: Market Data

**Feature ID:** market-data
**Status:** in-progress
**Owner:** engineer
**Risk:** medium
**Routes:** `(dashboard)/stocks`, `(dashboard)/stocks/[symbol]`
**Related docs:** [API overview](../api/overview.md), [Database schema](../database/schema.md)

Date: 2026-08-25
Related issue/PR: N/A

## Objective

Provide a read-only view of a stock universe and per-symbol price history, so an
authenticated user can browse stocks and inspect a candlestick chart. This is
the schema-first slice of the Phase 2 Market Data system; real ingestion is
deferred pending a data-provider/licensing decision.

## Overview

Users reach a protected stock list (`/stocks`) and a symbol detail page
(`/stocks/[symbol]`) that renders historical candles with TradingView Lightweight
Charts. The backend exposes `GET /api/v1/stocks` and
`GET /api/v1/stocks/{symbol}/prices` backed by the new `stocks` and `prices`
tables.

## Constraints

- Architecture constraints: fence market-data access behind `src/lib/api` and
  feature hooks; pages reuse the shared `RequireAuth` guard.
- Product/runtime constraints: prices carry an explicit `data_source` and `as_of`
  (`source="sample"` is placeholder data, never real market data).
- Out of scope: real ingestion/collectors, provider selection, the `/stocks`
  screener (Phase 6), and quant scoring (Phase 5).

## Impact Areas

- API/endpoints: yes (two new endpoints)
- Auth/session/RBAC: yes (protected pages and prices endpoint)
- State/store: no
- Env/config/secrets: no
- Observability/logging: no
- External integrations: yes (TradingView Lightweight Charts)
- CI/release/harness: no

## Core flow

```text
user -> /stocks or /stocks/[symbol] -> RequireAuth (client guard)
     -> market hook (useStocks / useStockPrices)
        -> apiClient (Bearer token)
           -> FastAPI /api/v1/stocks[/{symbol}/prices]
              -> envelope -> React Query cache -> StockList / StockChart
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

## Endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `GET` | `/api/v1/stocks` | List/search the stock universe | Optional (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/prices` | Historical OHLCV candles | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/technical` | Calculated technical indicators (MA, RSI, MACD, BB, ATR) | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/fundamental` | Fundamental ratios and financial metrics | Required (Bearer) |
| `GET` | `/api/v1/stocks/{symbol}/score` | Multi-factor composite score and factor breakdown | Required (Bearer) |
| `POST` | `/api/v1/screener` | Multi-parameter stock screening and ranking | Required (Bearer) |
| `GET` | `/api/v1/portfolios` | List user portfolios | Required (Bearer) |
| `POST` | `/api/v1/portfolios` | Create a new portfolio | Required (Bearer) |
| `GET` | `/api/v1/portfolios/{id}` | Portfolio detail and computed holdings PnL | Required (Bearer) |
| `POST` | `/api/v1/portfolios/{id}/transactions` | Add BUY/SELL transaction | Required (Bearer) |

Responses use the standard `ApiResponse` envelope. Prices include `as_of` and
`data_source` provenance.

## Acceptance Criteria

1. An authenticated user can list stocks and open a symbol detail page.
2. Prices render as a candlestick chart with loading/error/empty states.
3. Unknown symbols return a `404 SYMBOL_NOT_FOUND` envelope.
4. The prices endpoint rejects unauthenticated requests.

## Implementation Checklist

- [x] Backend `stocks`/`prices` models + migration 0002
- [x] Backend service, routes, and FastAPI wiring
- [x] Backend tests
- [x] Frontend types, endpoints, query keys, hooks
- [x] `StockList`, `StockChart`, `StockDetail` components
- [x] `/stocks` and `/stocks/[symbol]` pages

## Decision Log

- 2026-08-25: Reuse the `(dashboard)` route group -> avoids a new route-group
  gate and reuses `RequireAuth`.
- 2026-08-25: Schema-first slice with labeled `source="sample"` seed -> proves
  the full stack without waiting on a provider, and never presents placeholder
  data as real.
- 2026-08-26: Pure indicator calculations in `app/technical/indicators.py` -> no
  unmaintained pandas-ta dependency, returns `None` when lookback history is insufficient.

## Verification

```bash
cd apps/quant-api && .venv/bin/pytest -q   # 16 tests incl. technical indicators & routes
cd apps/quant-api && .venv/bin/ruff check .
pnpm lint && pnpm type-check && pnpm docs:check && pnpm test && pnpm build
```

## Runtime Evidence

- Environment: local Docker Compose (Next.js, FastAPI, PostgreSQL/TimescaleDB).
- Dependencies/services: seeded sample rows via `python -m scripts.seed_market_data`.
- Executed request/flow: `GET /api/v1/stocks`, `GET /api/v1/stocks/BBCA/prices`.
- Relevant logs/request IDs: N/A.
- Notes: chart rendering verified in the browser after manual seed.

## Risks And Mitigations

- Risk: `prices` is a hypertable only on Postgres; SQLite tests use a plain table.
  - Mitigation: dialect-guarded `create_hypertable` in migration 0002.
- Risk: placeholder `source="sample"` data could be mistaken for real data.
  - Mitigation: explicit `data_source`/`as_of` on responses; seed is dev-only.

## Completion Notes

Shipped the Phase 2 schema-first foundation: models, migration, read endpoints,
backend tests, and a minimal authenticated browsing + chart UI. Real ingestion
remains `BLOCKED` until the data-provider/licensing decision.

## Follow-Ups

- [ ] Resolve data-provider decision, then replace the sample seed with real ingestion.
- [ ] Add pagination/date-range controls to the chart page.
- [ ] Deduplicate the loading/error/empty UI into a shared component.