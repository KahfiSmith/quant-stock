# Product Overview

## Product vision

This repository forms the frontend layer of **QuantLens**, a quantitative finance stock analysis platform.
QuantLens provides objective market insights through automated data ingestion, multi-factor quant scoring, interactive technical and fundamental analysis, strategy backtesting, and AI-driven analyst summaries.

For the full product specification and architecture phases, see the [QuantLens PRD Specification](./quantlens-spec.md) and the [Roadmap](./roadmap.md).

## Product status

This repository currently serves as the **frontend foundation** with completed authentication and user session flows. The quantitative engines, market data pipelines, and stock analysis features are planned for subsequent phases.

## Implemented product surface

- Generic public landing page (`/`).
- Authentication flows: `/login`, `/register`.
- Authenticated proof surface: `/profile` (shows the current user).

## Target product surface (QuantLens Roadmap)

- **Stock Screener (`/stocks`)**: Multi-factor filtering (Momentum, Quality, Value, Risk, Growth, Sector, PER, ROE).
- **Stock Detail (`/stocks/[symbol]`)**: Interactive TradingView charts, technical indicators, fundamental breakdown, quant score decomposition.
- **Portfolio Management (`/portfolio`)**: Multi-asset tracking, PnL analysis, risk metrics.
- **Strategy Backtesting (`/backtest`)**: Rule-based strategy simulation with CAGR, Sharpe Ratio, and Maximum Drawdown analysis.
- **AI Analyst**: Automated strengths, risks, and synthesis generated from quant and fundamental signals.

## Business rules and enforcement

| Rule | Enforcement |
|---|---|
| Unauthenticated users are redirected to login from protected pages | Client-side guard in `(dashboard)/profile/page.tsx` |
| Authenticated users are redirected away from `/login` | `(auth)/login/page.tsx` checks `useAuthStore` status |
| Access token expiry triggers refresh without user intervention | Single-flight refresh in `src/lib/api/client.ts` |
| Terminal auth errors force logout + redirect | `handleQueryError` in `src/lib/api/queries.ts` |

All rules are client-side; the backend independently enforces its own security
boundary.

## Terminology

| Term | Definition |
|---|---|
| **Access Token** | Short-lived credential stored in-memory in `useAuthStore` |
| **Refresh Token** | Persistent credential in an HttpOnly cookie, managed by the backend |
| **Session Bootstrap** | Process of restoring user state on app mount via `/api/v1/auth/refresh` |
| **ApiResponse envelope** | Standard response shape `{ success, message, data, code?, error? }` |
| **Single-flight refresh** | Merging concurrent refresh requests into one shared promise |
| **authClient** | Credentialed Axios client (`withCredentials: true`) for auth endpoints |
| **apiClient** | Bearer token Axios client with unwrap and single-flight refresh |
| **Query defaults** | Per-domain TanStack Query defaults in `src/lib/api/queries.ts` |
