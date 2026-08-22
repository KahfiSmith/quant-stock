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

## Planned QuantLens API Endpoints (`/api/v1`)

| Module | Method | Path | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/login` | User login (JWT + refresh cookie) |
| **Auth** | `POST` | `/api/v1/auth/register` | User registration |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Single-flight token refresh |
| **Auth** | `POST` | `/api/v1/auth/logout` | Session invalidation |
| **Market Data** | `GET` | `/api/v1/stocks` | List and search stocks with summary metrics |
| **Market Data** | `GET` | `/api/v1/stocks/{symbol}/prices` | Historical OHLCV prices for charts |
| **Technical** | `GET` | `/api/v1/stocks/{symbol}/technical` | Technical indicators (MA, RSI, MACD, ATR) |
| **Fundamental**| `GET` | `/api/v1/stocks/{symbol}/fundamental` | Fundamental ratios & growth metrics |
| **Quant Score** | `GET` | `/api/v1/stocks/{symbol}/score` | Multi-factor quant score breakdown |
| **Screener** | `POST` | `/api/v1/screener` | Filter & rank stocks by multi-criteria |
| **Portfolio** | `GET`/`POST` | `/api/v1/portfolios` | User portfolio & transaction management |
| **Backtest** | `POST` | `/api/v1/backtest` | Run historical strategy backtest |
| **AI Analyst** | `GET` | `/api/v1/stocks/{symbol}/ai-summary` | AI-generated strengths, risks, conclusion |

## Related documents

- [QuantLens PRD Specification](../product/quantlens-spec.md) - Full system specification.
- [Authentication & Errors](./authentication.md) - Auth endpoint details, envelope, and error codes.
- [Database Schema](../database/schema.md) - PostgreSQL & TimescaleDB schema definition.

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
