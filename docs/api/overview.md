# API Overview

API integration documentation for communication between the Next.js frontend and the QuantLens backend service (FastAPI Quant Engine).

## Contract summary

- Backend base URL is configured via `NEXT_PUBLIC_BACKEND_API_URL`
  (see `.env.example`, default `http://localhost:8000` for FastAPI).
- Endpoint paths carry the `/api/v1/...` prefix (e.g. `/api/v1/auth/login`, `/api/v1/stocks`).
- Every response follows the standard `ApiResponse<T>` envelope
  (`src/types/api.types.ts`).
- Axios clients are defined in `src/lib/api/client.ts`:
  - `authClient` - credentialed (`withCredentials: true`) for auth endpoints.
  - `apiClient` - Bearer token client with single-flight refresh and
    `response.data.data` unwrap.

## Implemented QuantLens API Endpoints (`/api/v1`)

| Module | Method | Path | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/login` | User login (JWT + refresh cookie) |
| **Auth** | `POST` | `/api/v1/auth/register` | User registration |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Single-flight token refresh |
| **Auth** | `POST` | `/api/v1/auth/logout` | Session invalidation |
| **Auth** | `GET` | `/api/v1/auth/me` | Get current user profile |
| **Auth** | `PATCH` | `/api/v1/auth/me` | Update name, theme preference, timezone |
| **Auth** | `DELETE` | `/api/v1/auth/account` | Delete user account |
| **Market Data** | `GET` | `/api/v1/stocks` | List and search IDX stocks (optional Bearer auth) |
| **Market Data** | `GET` | `/api/v1/stocks/{symbol}/prices` | Historical OHLCV prices for charts |
| **AI Analyst** | `GET` | `/api/v1/stocks/{symbol}/ai-summary` | AI-generated strengths, risks, conclusion |
| **Backtest** | `POST` | `/api/v1/backtest` | Run historical strategy backtest |
| **Backtest** | `GET` | `/api/v1/backtest/jobs` | List user's persistent backtest jobs |
| **Backtest** | `GET` | `/api/v1/backtest/jobs/{id}` | Get detail of a specific persistent backtest job |
| **Fundamental**| `GET` | `/api/v1/stocks/{symbol}/fundamental` | Fundamental ratios & growth metrics |
| **Portfolio** | `GET` | `/api/v1/portfolios` | List user portfolios |
| **Portfolio** | `POST` | `/api/v1/portfolios` | Create portfolio |
| **Portfolio** | `GET` | `/api/v1/portfolios/{id}` | Portfolio detail with holdings and PnL |
| **Portfolio** | `PATCH` | `/api/v1/portfolios/{id}` | Update portfolio name/currency |
| **Portfolio** | `DELETE` | `/api/v1/portfolios/{id}` | Delete portfolio (cascades transactions) |
| **Portfolio** | `POST` | `/api/v1/portfolios/{id}/transactions` | Add BUY/SELL transaction |
| **Portfolio** | `DELETE` | `/api/v1/portfolios/{id}/transactions/{txn_id}` | Delete a transaction |
| **Quant Score** | `GET` | `/api/v1/stocks/{symbol}/score` | Multi-factor quant score breakdown |
| **Screener** | `POST` | `/api/v1/screener` | Filter & rank IDX stocks with conviction score, 7 strategy presets, volume/volatility/momentum filters |
| **Technical** | `GET` | `/api/v1/stocks/{symbol}/technical` | 34+ indicators: MA, RSI, MACD, ADX, MFI, Stochastic RSI, OBV, Bollinger, volume analysis, volatility regime, multi-TF momentum, drawdown, risk-adjusted returns (Sharpe/Sortino/Calmar), support/resistance |
| **IDX Data** | `GET` | `/api/v1/idx/universe` | Full active IDX stock universe with IDX-IC classification |
| **IDX Data** | `GET` | `/api/v1/idx/stocks/{symbol}` | IDX stock profile with foreign flow and corporate actions |
| **IDX Data** | `GET` | `/api/v1/idx/stocks/{symbol}/flow-analysis` | Foreign flow analysis: accumulation/distribution signal, divergence, momentum, streak |
| **IDX Data** | `GET` | `/api/v1/idx/broker-summary` | Broker-level daily trading activity from idx.co.id |
| **IDX Data** | `POST` | `/api/v1/idx/factor-rotation/backtest` | Run IDX multi-asset factor rotation backtest vs IHSG |
| **Scanner** | `GET` | `/api/v1/scanner/swing` | Swing breakout scanner (volume Z ≥ 1.5 + momentum) |
| **Scanner** | `GET` | `/api/v1/scanner/scalping` | Scalping/gorengan scanner (volume Z ≥ 2.0 + aggressive momentum) |
| **Scanner** | `GET` | `/api/v1/scanner/accumulation` | Foreign accumulation scanner (smart money buying) |
| **Scanner** | `GET` | `/api/v1/scanner/oversold-bounce` | Oversold bounce scanner (RSI ≤ 35 + mean reversion) |

## API scope status

The active endpoints implement the current synchronous analytical contracts. Portfolio
management includes full CRUD (create, read, update, delete) with cascade transaction
deletion; portfolio detail includes realized/unrealized PnL and deterministic risk
metrics. Backtest responses include Sortino and reproducibility metadata. AI responses
include evidence and data-quality metadata. The screener v2 engine computes a composite
conviction score (0-100) blending quant factors, foreign flow signals, and risk-adjusted
returns into actionable buy recommendations.

Market data is sourced from two providers:
- **yfinance** (Yahoo Finance): 78 IDX liquid stocks, 2-year daily OHLCV + TTM
  fundamentals, ingested via `python -m scripts.backfill_market_data`.
- **idx.co.id** (BEI): Daily foreign flow per stock + broker trading summary,
  ingested via `python -m scripts.backfill_idx_data`.

Provider-neutral ingestion contracts are internal service modules, not public API
endpoints.

## Related documents

- [QuantLens PRD Specification](../product/quantlens-spec.md) - Full system specification.
- [Authentication & Errors](./authentication.md) - Auth endpoint details, envelope, and error codes.
- [Database Schema](../database/schema.md) - PostgreSQL & TimescaleDB schema definition.
- [Market Data feature](../features/market-data.md) - ingestion pipeline and operational details.
- [ADR-005](../architecture/adr/ADR-005-yfinance-provider.md) - yfinance provider decision.

## Axios clients

- **`authClient`** - credentialed client (`withCredentials: true`) for
  authentication endpoints.
- **`apiClient`** - Bearer token client for business endpoints. Reads the
  access token from `useAuthStore` and sets `Authorization: Bearer <token>`.

### Interceptors

- `apiClient` request interceptor attaches the Bearer token from the store.
- `apiClient` response interceptor:
  1. Unwraps the envelope: returns `response.data.data` when present.
  2. On `401` with code `ACCESS_TOKEN_EXPIRED` (and not already retried),
     triggers a single-flight refresh, then retries the original request.
  3. On refresh failure, clears the session and redirects to `/login`.

### Single-flight refresh

```text
concurrent 401s -> one shared refreshAccessToken() promise -> all callers retry
```

Implemented with a module-level `refreshPromise` in `client.ts`. The refresh
call itself goes through `authClient` (`POST /api/v1/auth/refresh`), updates the
store, and returns the new access token. The `_retry` flag prevents infinite
retry loops.

## Query configuration

Defined in `src/lib/api/queries.ts`.

- `queryDefaults` - per-domain defaults for auth, data, lists, and profile
  (gcTime, staleTime, retry, refetchOnWindowFocus).
- `queryClientConfig` - defaultOptions wired into `QueryProvider`.
- `invalidateAuthQueries` / `clearAuthQueries` - invalidate or remove auth and
  profile query keys on session changes.
- `handleQueryError` - maps terminal auth errors to logout + redirect.

Query keys live in `src/lib/api/query-keys.ts` (`auth.session`,
`user.profile`).
