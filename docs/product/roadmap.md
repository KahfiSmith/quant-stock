# Roadmap — QuantLens AI Development

- Status: Working draft (planning artifact based on [QuantLens PRD](docs/product/quantlens-spec.md))
- Date: 2026-08-22
- Purpose: Single source of truth for build order across all QuantLens development phases.

## Conventions

- Status legend: **done** = implemented; **in-progress** = actively being built;
  **planned** = to build; **candidate** = considered, not committed.
- When a feature ships, mark it **done** and make sure it has a
  `docs/features/<feature>.md` (the `docs:check` gate requires it).

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

### Phase 1 — Authentication & User System (In Progress)
- [x] Integrate frontend auth forms with FastAPI JWT + HttpOnly refresh-cookie endpoints.
- [x] Create numeric-ID `users`, `sessions`, and refresh-token history tables.
- [ ] Settings and profile preferences.
- [ ] Google OAuth/OIDC, password reset, and email verification.

### Phase 2 — Market Data System (Planned)
- [ ] Ingest stock metadata and historical OHLCV data.
- [ ] Setup `stocks` table and `prices` TimescaleDB hypertable.
- [ ] Build endpoints: `GET /api/v1/stocks`, `GET /api/v1/stocks/{symbol}/prices`.
- [ ] Integrate TradingView Lightweight Charts in frontend.

### Phase 3 — Technical Analysis Engine (Planned)
- [ ] Implement `apps/quant-api/app/technical` calculation module using `pandas-ta`.
- [ ] Support indicators: MA20/50/200, RSI, MACD, ATR, Bollinger Bands.
- [ ] Build endpoint: `GET /api/v1/stocks/{symbol}/technical`.

### Phase 4 — Fundamental Analysis Engine (Planned)
- [ ] Implement `apps/quant-api/app/fundamental` evaluation module.
- [ ] Process ratios: PER, PBV, ROE, ROA, DER, Revenue Growth, EPS Growth.
- [ ] Build endpoint: `GET /api/v1/stocks/{symbol}/fundamental`.

### Phase 5 — Quant Scoring Engine (Planned)
- [ ] Implement multi-factor scoring module in `apps/quant-api/app/quant/scoring.py`.
- [ ] Apply formula: `30% Momentum + 25% Quality + 20% Value + 15% Risk + 10% Growth`.
- [ ] Build endpoint: `GET /api/v1/stocks/{symbol}/score`.

### Phase 6 — Stock Screener (Planned)
- [ ] Build interactive screener table on `/stocks`.
- [ ] Multi-parameter filters: Sector, Market Cap, Quant Score, ROE, PER, PBV.
- [ ] Dynamic ranking and pagination.

### Phase 7 — Stock Detail Page (Planned)
- [ ] Build comprehensive stock view on `/stocks/[symbol]`.
- [ ] Sections: Overview, Candlestick Chart, Financial Ratios, Quant Score Breakdown.

### Phase 8 — Portfolio System (Planned)
- [ ] Setup `portfolios`, `transactions`, `holdings` database tables.
- [ ] Portfolio tracking page `/portfolio` with PnL, asset allocation, and risk metrics.

### Phase 9 — Backtesting Engine (Planned)
- [ ] Implement backtest simulation in `apps/quant-api/app/quant/backtest.py`.
- [ ] Strategy rules execution with CAGR, Sharpe Ratio, Max Drawdown metrics.
- [ ] Equity curve visualization in frontend.

### Phase 10 — AI Analyst (Future)
- [ ] LLM-assisted synthesis for stock reports (Strengths, Risks, Conclusion).

---

## Follow-ups

- After each phase ships: update this file's status, add/update relevant documentation under `docs/`, and run `pnpm verify:all`.
