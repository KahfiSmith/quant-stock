# Roadmap — QuantLens AI Development

- Status: Working draft (planning artifact based on [QuantLens PRD](docs/product/quantlens-spec.md))
- Date: 2026-08-22
- Purpose: Single source of truth for build order across all QuantLens development phases.

## Conventions

- Status legend: **done** = implemented; **in-progress** = actively being built;
  **planned** = to build; **candidate** = considered, not committed.
- When a feature ships, mark it **done** and make sure it has a
  `docs/features/<feature>.md` (the `docs:check` gate requires it).

## Implemented (Boilerplate Baseline)

- [x] Authentication & user session (login, register, logout, refresh, session bootstrap, protected profile, delete account) — see `docs/features/authentication.md`
- [x] Google SSO (OIDC) — frontend button and session wiring
- [x] Landing page (`/`)
- [x] Protected profile surface (`/profile`)

## QuantLens Phased Roadmap

### Phase 0 — Project Initialization (Planned)
- [ ] Setup monorepo structure (`apps/web`, `apps/quant-api`, `packages/database`, `packages/ui`, `packages/config`).
- [ ] Connect Next.js frontend with FastAPI backend.
- [ ] Configure Docker & Docker Compose with PostgreSQL + TimescaleDB.
- [ ] Setup unified environment configuration.

### Phase 1 — Authentication & User System (Planned / In Integration)
- [ ] Integrate frontend auth forms with FastAPI JWT + HttpOnly refresh cookie endpoints.
- [ ] Setup `users` and `sessions` database tables.
- [ ] Settings and profile preferences.

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
