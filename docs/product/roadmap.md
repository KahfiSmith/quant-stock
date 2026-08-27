# Roadmap — QuantLens AI Development

- Status: Current implementation status (based on [QuantLens PRD](./quantlens-spec.md))
- Date: 2026-08-27
- Purpose: Single source of truth for build order across all QuantLens development phases.

## Conventions

- Status legend: **COMPLETE** = implemented and verified; **PARTIAL** = implemented
  only in part of the requirement; **BLOCKED** = dependency decision required;
  **DEFERRED** = intentionally postponed; **OUT OF SCOPE** = not required.
- A feature is **COMPLETE** only when its documented acceptance and exit criteria
  are verified; keep dependency-blocked work explicitly marked **BLOCKED**.

## Implemented

- [x] FastAPI service foundation in `apps/quant-api`, with Alembic and Docker Compose TimescaleDB/PostgreSQL.
- [x] Authentication & user sessions: numeric IDs, registration, login, logout, refresh rotation/reuse detection, session bootstrap, protected profile, and account deletion — see `docs/features/authentication.md`.
- [x] Landing page (`/`)
- [x] Protected profile surface (`/profile`)

Deferred: Google OAuth/OIDC, password reset, email verification, and settings/profile preferences.

## QuantLens Phased Roadmap

### Phase 0 — Project Initialization (Done)
- [x] Establish the active FastAPI service under `apps/quant-api`; the root Next.js app remains in place temporarily.
- [x] Connect the Next.js frontend with the FastAPI backend.
- [x] Configure Docker Compose with PostgreSQL + TimescaleDB.
- [x] Configure environment variables and Alembic migrations.

### Phase 1 — Authentication & User System (PARTIAL / DEFERRED OPTIONAL FLOWS)
- [x] Integrate frontend auth forms with FastAPI JWT + HttpOnly refresh-cookie endpoints.
- [x] Create numeric-ID `users`, `sessions`, and refresh-token history tables.
- [x] Settings and profile preferences via protected `PATCH /api/v1/auth/me` and `/settings`.
- [ ] Google OAuth/OIDC, password reset, and email verification (DEFERRED).

### Phase 2 — Market Data System (PARTIAL / BLOCKED)
- [ ] Activate real stock metadata and historical OHLCV provider ingestion (BLOCKED on provider and licensing decision).
- [x] Provider-neutral ingestion contracts, validation, provenance, and idempotent persistence boundary.
- [x] Setup `stocks` table and `prices` TimescaleDB hypertable (migration `0002_market_data`).
- [x] Build endpoints: `GET /api/v1/stocks`, `GET /api/v1/stocks/{symbol}/prices`.
- [x] Integrate TradingView Lightweight Charts in frontend (`/stocks`, `/stocks/[symbol]`).

### Phase 3 — Technical Analysis Engine (Done)
- [x] Implement `apps/quant-api/app/technical` calculation module without unmaintained pandas-ta.
- [x] Support indicators: MA20/50/200, RSI, MACD, ATR, Bollinger Bands.
- [x] Build endpoint: `GET /api/v1/stocks/{symbol}/technical`.

### Phase 4 — Fundamental Analysis Engine (Done)
- [x] Implement `apps/quant-api/app/fundamental` evaluation module and `fundamentals` table.
- [x] Process ratios: PER, PBV, ROE, ROA, DER, Revenue Growth, EPS Growth.
- [x] Build endpoint: `GET /api/v1/stocks/{symbol}/fundamental`.

### Phase 5 — Quant Scoring Engine (Done)
- [x] Implement multi-factor scoring module in `apps/quant-api/app/quant/scoring.py`.
- [x] Apply formula: `30% Momentum + 25% Quality + 20% Value + 15% Risk + 10% Growth`.
- [x] Build endpoint: `GET /api/v1/stocks/{symbol}/score`.

### Phase 6 — Stock Screener (Done)
- [x] Build interactive screener table on `/stocks`.
- [x] Multi-parameter filters: Sector, Market Cap, Quant Score, ROE, PER, PBV, RSI.
- [x] Dynamic ranking and pagination via `POST /api/v1/screener`.

### Phase 7 — Stock Detail Page (Done)
- [x] Build comprehensive stock view on `/stocks/[symbol]`.
- [x] Sections: Overview, Candlestick Chart, Financial Ratios, Quant Score Breakdown with tab navigation.

### Phase 8 — Portfolio System (COMPLETE)
- [x] Setup `portfolios`, `transactions` database tables and migrations 0004–0005.
- [x] Portfolio editing with ownership and validation via `PATCH /api/v1/portfolios/{id}`.
- [x] Weighted-average realized/unrealized PnL, holdings, allocation, and deterministic risk summary.
- [x] Portfolio tracking page `/portfolio` with edit feedback and risk metrics.

### Phase 9 — Backtesting Engine (COMPLETE)
- [x] Implement backtest simulation in `apps/quant-api/app/quant/backtest.py`.
- [x] Strategy rules execution with CAGR, Sharpe, Sortino, Max Drawdown, Annual Volatility, and Win Rate metrics.
- [x] Reproducibility metadata, execution costs/slippage, explicit policies, and anti-bias regression coverage.
- [x] Build endpoint `POST /api/v1/backtest` and `/backtest` simulation UI in frontend.

### Phase 10 — AI Analyst (COMPLETE for current approved deterministic policy)
- [x] Implement deterministic structured facts synthesis module in `apps/quant-api/app/services/ai_analyst.py`.
- [x] Build endpoint `GET /api/v1/stocks/{symbol}/ai-summary` with strengths, risks, unknowns, conclusion, evidence, provenance, and data-quality metadata.
- [x] Add interactive AI Analyst tab on `/stocks/[symbol]`.
- [x] Add offline structured-output, factuality, safety, and untrusted-text evaluation tests.
- [ ] Licensed-news/LLM provider integration (BLOCKED until approved provider and policy).

---

## Follow-ups

- After each phase ships: update this file's status, add/update relevant documentation under `docs/`, and run `pnpm verify:all`.
